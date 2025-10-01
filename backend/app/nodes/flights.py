import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.services.agent_service import BaseTool
from pydantic import BaseModel, Field


class FlightSearchSchema(BaseModel):
    """Schema for flight search parameters"""

    origin: str = Field(description="Origin airport code or city")
    destination: str = Field(description="Destination airport code or city")
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

    __root__: List[FlightOption]


class FlightTool(BaseTool):
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
        return_date: Optional[str] = None,
        passengers: int = 1,
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
                    "return_date": return_date,
                    "passengers": passengers,
                },
                "outbound_flights": outbound_flights,
                "return_flights": [],
            }

            # Generate return flights if round trip
            if return_date:
                return_flights = []
                for i in range(3):
                    departure_time = f"{14 + i * 3:02d}:00"
                    arrival_time = f"{18 + i * 3:02d}:30"
                    price = 280 + (i * 60) + random.randint(-40, 80)

                    return_flights.append(
                        {
                            "flight_number": f"{random.choice(['AA', 'DL', 'UA', 'WN'])}{random.randint(100, 9999)}",
                            "airline": random.choice(airlines),
                            "aircraft": random.choice(aircraft_types),
                            "origin": destination,
                            "destination": origin,
                            "departure_date": return_date,
                            "departure_time": departure_time,
                            "arrival_time": arrival_time,
                            "duration": "4h 30m",
                            "price_usd": price,
                            "stops": 0 if i == 0 else 1,
                            "baggage_included": i == 0,
                        }
                    )

                result["return_flights"] = return_flights

            # Calculate total price for round trip
            if return_date and outbound_flights and result["return_flights"]:
                cheapest_outbound = min(outbound_flights, key=lambda x: x["price_usd"])
                cheapest_return = min(
                    result["return_flights"], key=lambda x: x["price_usd"]
                )
                result["total_price_usd"] = (
                    cheapest_outbound["price_usd"] + cheapest_return["price_usd"]
                )
            else:
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


# Create and register the tool instance
flights_tool = FlightTool()
