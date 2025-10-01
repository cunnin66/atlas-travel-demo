import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from amadeus import Client, ResponseError
from app.core.config import settings
from app.nodes.base import BaseTool
from pydantic import BaseModel, Field


class FlightSearchSchema(BaseModel):
    """Schema for flight search parameters"""

    origin: str = Field(description="Origin airport code")
    destination: str = Field(description="Destination airport code")
    departure_date: str = Field(description="Departure date in YYYY-MM-DD format")
    # return_date: Optional[str] = Field(default=None, description="Return date in YYYY-MM-DD format for round trip")


class FlightOption(BaseModel):
    flight_id: str
    carrier: str
    depart_local: datetime
    arrive_local: datetime
    num_stops: int
    fare_usd: float
    co2_kg: float


class FlightResultSchema(BaseModel):
    """Schema for flight search result as an array of flight options"""

    flights: List[FlightOption]


class FlightToolFixture(BaseTool):
    """Tool for searching flights"""

    name: str = "search_flights"
    description: str = "Search for flights between two locations. Useful for travel planning and booking."

    def get_args_schema(self) -> BaseModel:
        return FlightSearchSchema

    def get_result_schema(self) -> BaseModel:
        return FlightResultSchema

    async def execute(
        self,
        origin: str,
        destination: str,
        departure_date: str,
    ) -> Dict[str, Any]:
        """Execute flight search"""
        try:
            # For demo purposes, return mock flight data
            # In production, you'd integrate with flight APIs like Amadeus, Skyscanner, etc.

            airlines = ["American Airlines", "Delta", "United", "Southwest", "JetBlue"]
            aircraft_types = ["Boeing 737", "Airbus A320", "Boeing 777", "Airbus A330"]

            # Generate mock outbound flights
            outbound_flights = []
            for i in range(3):  # Return 3 flight options
                departure_time = f"{8 + i * 4:02d}:00"
                arrival_time = f"{12 + i * 4:02d}:30"
                price = 250 + (i * 50) + random.randint(-50, 100)

                outbound_flights.append(
                    {
                        "flight_number": f"{random.choice(['AA', 'DL', 'UA', 'WN'])}{random.randint(100, 9999)}",
                        "airline": random.choice(airlines),
                        "aircraft": random.choice(aircraft_types),
                        "origin": origin,
                        "destination": destination,
                        "departure_date": departure_date,
                        "departure_time": departure_time,
                        "arrival_time": arrival_time,
                        "duration": "4h 30m",
                        "price_usd": price,
                        "stops": 0 if i == 0 else 1,
                        "baggage_included": i == 0,
                    }
                )

            result = {
                "search_params": {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                },
                "outbound_flights": outbound_flights,
                "return_flights": [],
            }

            result["total_price_usd"] = (
                min(outbound_flights, key=lambda x: x["price_usd"])["price_usd"]
                if outbound_flights
                else 0
            )

            return {
                "success": True,
                "data": result,
                "message": f"Found {len(outbound_flights)} flight options from {origin} to {destination}",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to search flights from {origin} to {destination}",
            }


class AmadeusFlightTool(BaseTool):
    """Tool for searching flights using Amadeus API"""

    name: str = "search_flights_amadeus"
    description: str = "Search for real flights using Amadeus API. Provides actual flight data with pricing and schedules."

    def get_args_schema(self) -> BaseModel:
        return FlightSearchSchema

    def get_result_schema(self) -> BaseModel:
        return FlightResultSchema

    async def execute(
        self,
        origin: str,
        destination: str,
        departure_date: str,
    ) -> Dict[str, Any]:
        """Execute flight search using Amadeus API"""
        try:
            # Initialize the Amadeus client
            try:
                amadeus = Client(
                    client_id=settings.AMADEUS_API_KEY,
                    client_secret=settings.AMADEUS_SECRET_KEY,
                )
            except Exception as e:
                print("AMADEDUS CLIENT INITIALIZATION FAILED", e)
                return {
                    "success": False,
                    "error": "Amadeus client initialization failed",
                    "message": f"Could not initialize Amadeus client. Check environment variables: {str(e)}",
                }

            # Search for flight offers
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=departure_date,
                adults=1,
                currencyCode="USD",
                max=5,  # Ask for a maximum of 5 flight options
            )
            print("AMADEDUS RESPONSE", response)

            # Parse the response into the expected format
            outbound_flights = []
            for offer in response.data:
                # Extract flight details from Amadeus response
                segments = offer["itineraries"][0]["segments"]
                first_segment = segments[0]
                last_segment = segments[-1]

                flight_details = {
                    "flight_number": f"{first_segment['carrierCode']}{first_segment['number']}",
                    "airline": first_segment[
                        "carrierCode"
                    ],  # Could be enhanced with airline name lookup
                    "aircraft": first_segment.get("aircraft", {}).get(
                        "code", "Unknown"
                    ),
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                    "departure_time": first_segment["departure"]["at"].split("T")[1][
                        :5
                    ],  # Extract time from ISO datetime
                    "arrival_time": last_segment["arrival"]["at"].split("T")[1][
                        :5
                    ],  # Extract time from ISO datetime
                    "duration": offer["itineraries"][0].get("duration", "Unknown"),
                    "price_usd": float(offer["price"]["total"]),
                    "stops": len(segments) - 1,
                    "baggage_included": True,  # Amadeus doesn't always provide this info clearly
                }
                outbound_flights.append(flight_details)

            result = {
                "search_params": {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                },
                "outbound_flights": outbound_flights,
                "return_flights": [],
            }

            result["total_price_usd"] = (
                min(outbound_flights, key=lambda x: x["price_usd"])["price_usd"]
                if outbound_flights
                else 0
            )

            return {
                "success": True,
                "data": result,
                "message": f"Found {len(outbound_flights)} flight options from {origin} to {destination}",
            }

        except ResponseError as error:
            return {
                "success": False,
                "error": f"Amadeus API Error: {error.description}",
                "message": f"Failed to search flights from {origin} to {destination}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"An unexpected error occurred while searching flights from {origin} to {destination}",
            }


# Create and register the tool instances
flights_fixture = FlightToolFixture()
amadeus_tool = AmadeusFlightTool()
