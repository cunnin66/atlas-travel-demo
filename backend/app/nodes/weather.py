from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field


class WeatherQuerySchema(BaseModel):
    """Schema for weather query parameters"""

    location: str = Field(description="Location to get weather for (city, country)")
    days: int = Field(
        default=7, description="Number of days to forecast (1-16)", ge=1, le=16
    )


class WeatherTool:
    """Tool for getting weather information using Open-Meteo API"""

    def __init__(self):
        self.name = "get_weather"
        self.description = "Get current weather and forecast for a location using Open-Meteo API. Useful for travel planning."
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"

    def get_args_schema(self) -> BaseModel:
        return WeatherQuerySchema

    async def _geocode_location(self, location: str) -> Optional[Dict[str, float]]:
        """Convert location name to coordinates using Open-Meteo Geocoding API"""
        try:
            params = {"name": location, "count": 1, "language": "en", "format": "json"}

            response = requests.get(self.geocoding_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get("results") and len(data["results"]) > 0:
                result = data["results"][0]
                return {
                    "latitude": result["latitude"],
                    "longitude": result["longitude"],
                    "name": result["name"],
                    "country": result.get("country", ""),
                    "admin1": result.get("admin1", ""),
                }
            return None

        except Exception as e:
            print(f"Geocoding error for {location}: {e}")
            return None

    async def execute(self, location: str, days: int = 7) -> Dict[str, Any]:
        """Execute weather lookup using Open-Meteo API"""
        try:
            # First, geocode the location to get coordinates
            geo_data = await self._geocode_location(location)
            if not geo_data:
                return {
                    "success": False,
                    "error": "Location not found",
                    "message": f"Could not find coordinates for {location}",
                }

            # Prepare weather API parameters
            params = {
                "latitude": geo_data["latitude"],
                "longitude": geo_data["longitude"],
                "current": [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "weather_code",
                    "wind_speed_10m",
                    "wind_direction_10m",
                ],
                "daily": [
                    "weather_code",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "precipitation_probability_max",
                    "wind_speed_10m_max",
                    "wind_direction_10m_dominant",
                ],
                "timezone": "auto",
                "forecast_days": min(days, 16),  # Open-Meteo supports up to 16 days
            }

            # Make the weather API request
            response = requests.get(self.weather_url, params=params, timeout=10)
            response.raise_for_status()

            weather_data = response.json()

            # Parse and format the response
            formatted_weather = self._format_weather_data(weather_data, geo_data, days)

            return {
                "success": True,
                "data": formatted_weather,
                "message": f"Weather forecast for {geo_data['name']} retrieved successfully",
            }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"API request failed: {str(e)}",
                "message": f"Failed to get weather for {location}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get weather for {location}",
            }

    def _format_weather_data(
        self, weather_data: Dict, geo_data: Dict, days: int
    ) -> Dict[str, Any]:
        """Format Open-Meteo weather data into a consistent structure"""

        # Weather code mapping (simplified)
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
        }

        current = weather_data.get("current", {})
        daily = weather_data.get("daily", {})

        # Format current weather
        current_weather = {
            "temperature": round(current.get("temperature_2m", 0), 1),
            "feels_like": round(current.get("apparent_temperature", 0), 1),
            "humidity": current.get("relative_humidity_2m", 0),
            "wind_speed": round(current.get("wind_speed_10m", 0), 1),
            "wind_direction": current.get("wind_direction_10m", 0),
            "condition": weather_codes.get(current.get("weather_code", 0), "Unknown"),
            "time": current.get("time", ""),
        }

        # Format daily forecast
        forecast = []
        if daily.get("time"):
            for i in range(min(len(daily["time"]), days)):
                day_data = {
                    "date": daily["time"][i],
                    "day": i + 1,
                    "high": round(daily.get("temperature_2m_max", [0] * days)[i], 1),
                    "low": round(daily.get("temperature_2m_min", [0] * days)[i], 1),
                    "condition": weather_codes.get(
                        daily.get("weather_code", [0] * days)[i], "Unknown"
                    ),
                    "precipitation_sum": round(
                        daily.get("precipitation_sum", [0] * days)[i], 1
                    ),
                    "precipitation_chance": daily.get(
                        "precipitation_probability_max", [0] * days
                    )[i],
                    "wind_speed": round(
                        daily.get("wind_speed_10m_max", [0] * days)[i], 1
                    ),
                    "wind_direction": daily.get(
                        "wind_direction_10m_dominant", [0] * days
                    )[i],
                }
                forecast.append(day_data)

        return {
            "location": f"{geo_data['name']}, {geo_data['country']}",
            "coordinates": {
                "latitude": geo_data["latitude"],
                "longitude": geo_data["longitude"],
            },
            "current": current_weather,
            "forecast": forecast,
            "timezone": weather_data.get("timezone", "UTC"),
            "units": {"temperature": "°C", "wind_speed": "km/h", "precipitation": "mm"},
        }


# Create and register the tool instance
weather_tool = WeatherTool()
