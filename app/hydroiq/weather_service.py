"""Weather service for HydroIQ."""
import httpx
from typing import Optional, Dict
from app.hydroiq.models import WeatherData
from app.config import settings


class WeatherService:
    """Service for fetching weather data."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize weather service.
        
        Args:
            api_key: OpenWeatherMap API key (optional, will use mock if not provided)
        """
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def get_weather(
        self,
        lat: float,
        lng: float,
    ) -> WeatherData:
        """
        Fetch weather data for a location.
        
        Args:
            lat: Latitude
            lng: Longitude
            
        Returns:
            WeatherData object
        """
        # If no API key, return mock data for hackathon
        if not self.api_key:
            return self._get_mock_weather()
        
        try:
            # OpenWeatherMap API call
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": lat,
                "lon": lng,
                "appid": self.api_key,
                "units": "metric",
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            main = data.get("main", {})
            
            return WeatherData(
                min_temp=main.get("temp_min", 22.0),
                max_temp=main.get("temp_max", 32.0),
                avg_temp=main.get("temp", 27.0),
                rainfall_mm=0.0,  # Would need forecast API for this
                humidity=main.get("humidity"),
            )
        except Exception as e:
            print(f"Weather API error: {e}, using mock data")
            return self._get_mock_weather()
    
    def _get_mock_weather(self) -> WeatherData:
        """Return mock weather data for Chennai/Poonamallee."""
        # Typical Chennai weather
        return WeatherData(
            min_temp=22.0,
            max_temp=32.0,
            avg_temp=27.0,
            rainfall_mm=0.5,
            humidity=65.0,
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global weather service instance
weather_service = WeatherService()






