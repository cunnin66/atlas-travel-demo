from datetime import datetime
from typing import Any, Dict

import requests
from app.services.agent_service import BaseTool
from pydantic import BaseModel, Field


class WeatherQuerySchema(BaseModel):
    """Schema for weather query parameters"""

    location: str = Field(description="Location to get weather for (city, country)")
    days: int = Field(default=7, description="Number of days to forecast (1-10)")


class WeatherTool(BaseTool):
    """Tool for getting weather information"""

    name: str = "get_weather"
    description: str = (
        "Get current weather and forecast for a location. Useful for travel planning."
    )

    def get_args_schema(self) -> BaseModel:
        return WeatherQuerySchema

    async def execute(self, location: str, days: int = 7) -> Dict[str, Any]:
        """Execute weather lookup"""
        try:
            # For demo purposes, return mock data
            # In production, you'd integrate with a real weather API like OpenWeatherMap

            mock_weather = {
                "location": location,
                "current": {
                    "temperature": 22,
                    "condition": "Partly cloudy",
                    "humidity": 65,
                    "wind_speed": 10,
                },
                "forecast": [],
            }

            # Generate mock forecast
            for day in range(days):
                mock_weather["forecast"].append(
                    {
                        "day": day + 1,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "high": 25 + (day % 5),
                        "low": 15 + (day % 3),
                        "condition": ["Sunny", "Partly cloudy", "Cloudy", "Light rain"][
                            day % 4
                        ],
                        "precipitation_chance": min(20 + (day * 10), 80),
                    }
                )

            return {
                "success": True,
                "data": mock_weather,
                "message": f"Weather forecast for {location} retrieved successfully",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get weather for {location}",
            }


# Create and register the tool instance
weather_tool = WeatherTool()
