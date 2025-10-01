import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.nodes.base import BaseTool
from pydantic import BaseModel, Field


class HotelSearchSchema(BaseModel):
    """Schema for hotel search parameters"""

    city: str = Field(description="City to search for hotels")
    country: str = Field(description="Country to search for hotels")
    check_in_date: str = Field(description="Check-in date in YYYY-MM-DD format")
    check_out_date: str = Field(description="Check-out date in YYYY-MM-DD format")
    adults: int = Field(description="Number of adults", default=1)


class HotelOption(BaseModel):
    hotel_id: str
    name: str
    address: str
    price_per_night_usd: float
    total_price_usd: float
    rating: float
    amenities: List[str]
    distance_from_center_km: float
    hotel_type: str
    description: str


class HotelResultSchema(BaseModel):
    """Schema for hotel search result"""

    search_params: Dict[str, Any]
    hotels: List[HotelOption]
    total_results: int


class HotelSearchTool(BaseTool):
    """Tool for searching hotels with mock data generation"""

    name: str = "hotel_search"
    description: str = (
        "Search for hotels in a location. Useful for travel planning and booking."
    )

    def get_args_schema(self) -> BaseModel:
        return HotelSearchSchema

    def get_result_schema(self) -> BaseModel:
        return HotelResultSchema

    async def execute(
        self,
        city: str,
        country: str,
        check_in_date: str,
        check_out_date: str,
        adults: int = 1,
    ) -> Dict[str, Any]:
        """Execute hotel search with semi-random hotel generation"""
        try:
            # Calculate number of nights
            check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
            check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
            nights = (check_out - check_in).days

            if nights <= 0:
                return {
                    "success": False,
                    "error": "Invalid dates",
                    "message": "Check-out date must be after check-in date",
                }

            # Generate fake hotel data
            hotels = self._generate_fake_hotels(city, country, nights, adults)

            result = {
                "search_params": {
                    "city": city,
                    "country": country,
                    "check_in_date": check_in_date,
                    "check_out_date": check_out_date,
                    "adults": adults,
                    "nights": nights,
                },
                "hotels": hotels,
                "total_results": len(hotels),
            }

            return {
                "success": True,
                "data": result,
                "message": f"Found {len(hotels)} hotel options in {city}, {country}",
            }

        except ValueError as e:
            return {
                "success": False,
                "error": "Invalid date format",
                "message": "Please use YYYY-MM-DD format for dates",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to search hotels in {city}, {country}",
            }

    def _generate_fake_hotels(
        self, city: str, country: str, nights: int, adults: int
    ) -> List[Dict[str, Any]]:
        """Generate fake hotel options"""
        hotels = []
        num_hotels = random.randint(4, 8)  # Generate 4-8 hotel options

        for i in range(num_hotels):
            hotel = self._generate_single_fake_hotel(city, country, nights, adults, i)
            hotels.append(hotel)

        # Sort by rating (highest first) with some randomness
        hotels.sort(key=lambda x: x["rating"] + random.uniform(-0.3, 0.3), reverse=True)

        return [hotel.__dict__ for hotel in [HotelOption(**hotel) for hotel in hotels]]

    def _generate_single_fake_hotel(
        self, city: str, country: str, nights: int, adults: int, index: int
    ) -> Dict[str, Any]:
        """Generate a single fake hotel option"""

        # Obviously fake hotel names
        fake_prefixes = [
            "Golden",
            "Silver",
            "Diamond",
            "Crystal",
            "Rainbow",
            "Sunset",
            "Sunrise",
            "Ocean",
            "Mountain",
            "Garden",
            "Plaza",
            "Crown",
            "Royal",
            "Grand",
            "Blue",
            "Green",
            "Red",
            "Purple",
            "Star",
            "Moon",
            "Sun",
        ]

        fake_suffixes = [
            "Palace",
            "Tower",
            "Inn",
            "Hotel",
            "Resort",
            "Lodge",
            "Suites",
            "Manor",
            "Castle",
            "Villa",
            "Retreat",
            "Oasis",
            "Haven",
            "Paradise",
            "Gardens",
            "Springs",
            "Heights",
            "Plaza",
            "Center",
            "Grand",
        ]

        # Generate obviously fake name
        prefix = random.choice(fake_prefixes)
        suffix = random.choice(fake_suffixes)
        name = f"{prefix} {suffix}"

        # Add a random number sometimes to make it more obviously fake
        if random.random() < 0.3:
            name += f" {random.randint(1, 99)}"

        # Simple pricing without location awareness
        base_price = 120  # Standard base price

        # Create price tiers
        tier = random.choices(
            ["budget", "mid-range", "upscale", "luxury"], weights=[25, 40, 25, 10]
        )[0]

        tier_multipliers = {
            "budget": 0.6,
            "mid-range": 1.0,
            "upscale": 1.5,
            "luxury": 2.5,
        }

        price_per_night = base_price * tier_multipliers[tier] + random.randint(-40, 60)
        price_per_night = max(50, price_per_night)  # Minimum $50/night
        total_price = (
            price_per_night * nights * (1 + (adults - 1) * 0.3)
        )  # Extra cost for additional adults

        # Rating based on tier
        base_ratings = {"budget": 3.2, "mid-range": 3.8, "upscale": 4.3, "luxury": 4.7}
        rating = base_ratings[tier] + random.uniform(-0.3, 0.3)
        rating = max(2.5, min(5.0, rating))  # Clamp between 2.5 and 5.0

        # Amenities based on tier
        all_amenities = [
            "Free WiFi",
            "Air Conditioning",
            "24/7 Front Desk",
            "Room Service",
            "Fitness Center",
            "Swimming Pool",
            "Spa",
            "Restaurant",
            "Bar",
            "Business Center",
            "Concierge",
            "Valet Parking",
            "Pet Friendly",
            "Airport Shuttle",
            "Laundry Service",
            "Meeting Rooms",
        ]

        amenity_counts = {"budget": 4, "mid-range": 6, "upscale": 9, "luxury": 12}
        amenities = random.sample(
            all_amenities, min(amenity_counts[tier], len(all_amenities))
        )

        # Always include basic amenities for mid-range and above
        if tier != "budget":
            basic_amenities = ["Free WiFi", "Air Conditioning", "24/7 Front Desk"]
            for amenity in basic_amenities:
                if amenity not in amenities:
                    amenities.append(amenity)

        # Generic address and distance
        street_names = [
            "Main Street",
            "First Avenue",
            "Central Boulevard",
            "Park Road",
            "Hotel Street",
        ]
        address = (
            f"{random.randint(1, 999)} {random.choice(street_names)}, {city}, {country}"
        )
        distance = random.uniform(0.5, 15.0)  # Distance from city center

        # Hotel types and descriptions
        hotel_types = {
            "budget": ["Budget Hotel", "Economy Inn", "Hostel"],
            "mid-range": ["Business Hotel", "City Hotel", "Boutique Hotel"],
            "upscale": ["Upscale Hotel", "Design Hotel", "Premium Hotel"],
            "luxury": ["Luxury Hotel", "5-Star Hotel", "Grand Hotel", "Palace Hotel"],
        }

        hotel_type = random.choice(hotel_types[tier])

        descriptions = {
            "budget": f"Comfortable and affordable accommodation in {city}. Perfect for budget-conscious travelers.",
            "mid-range": f"Well-appointed hotel in {city} offering modern amenities and excellent service.",
            "upscale": f"Sophisticated hotel in the heart of {city} with premium facilities and personalized service.",
            "luxury": f"Exquisite luxury hotel in {city}, offering world-class amenities and unparalleled service.",
        }

        return {
            "hotel_id": f"HTL_{city.upper()[:3]}_{random.randint(1000, 9999)}",
            "name": name,
            "address": address,
            "price_per_night_usd": round(price_per_night, 2),
            "total_price_usd": round(total_price, 2),
            "rating": round(rating, 1),
            "amenities": sorted(amenities),
            "distance_from_center_km": round(distance, 1),
            "hotel_type": hotel_type,
            "description": descriptions[tier],
        }


# Create the hotel search tool instance
hotel_search_tool = HotelSearchTool()
