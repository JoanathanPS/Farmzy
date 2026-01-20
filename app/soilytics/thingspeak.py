"""ThingSpeak API integration for fetching sensor data."""
import httpx
from typing import Optional, Dict, List
from datetime import datetime
from app.config import settings
from app.soilytics.models import SoilReading


class ThingSpeakClient:
    """Client for fetching data from ThingSpeak API."""
    
    BASE_URL = "https://api.thingspeak.com"
    
    def __init__(
        self,
        channel_id: Optional[str] = None,
        read_api_key: Optional[str] = None,
    ):
        """
        Initialize ThingSpeak client.
        
        Args:
            channel_id: ThingSpeak channel ID
            read_api_key: ThingSpeak read API key
        """
        self.channel_id = channel_id or settings.thingspeak_channel_id
        self.read_api_key = read_api_key or settings.thingspeak_read_api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def fetch_latest_reading(
        self,
        device_id: Optional[str] = None,
        location: Optional[Dict[str, float]] = None,
    ) -> Optional[SoilReading]:
        """
        Fetch the latest sensor reading from ThingSpeak.
        
        Args:
            device_id: Device identifier (defaults to channel-based)
            location: Optional location data {"lat": float, "lng": float}
            
        Returns:
            SoilReading object or None if fetch fails
        """
        if not self.channel_id or not self.read_api_key:
            raise ValueError("ThingSpeak channel_id and read_api_key must be configured")
        
        try:
            # ThingSpeak API endpoint for latest data
            url = f"{self.BASE_URL}/channels/{self.channel_id}/feeds/last.json"
            params = {"api_key": self.read_api_key}
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse ThingSpeak feed data
            # ThingSpeak typically returns fields like field1, field2, etc.
            # Adjust field mapping based on your actual ThingSpeak channel setup
            feed = data.get("feeds", [{}])[0] if isinstance(data.get("feeds"), list) else data
            
            # Map ThingSpeak fields to our soil reading format
            # Adjust these field names based on your actual ThingSpeak channel configuration
            soil_data = {
                "moisture": float(feed.get("field1", feed.get("moisture", 0.0))),
                "ph": float(feed.get("field2", feed.get("ph", 7.0))),
                "nitrogen": float(feed.get("field3", feed.get("nitrogen", 0.0))),
                "phosphorus": float(feed.get("field4", feed.get("phosphorus", 0.0))),
                "potassium": float(feed.get("field5", feed.get("potassium", 0.0))),
            }
            
            # Parse timestamp
            timestamp_str = feed.get("created_at") or feed.get("timestamp")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                except:
                    timestamp = datetime.utcnow()
            else:
                timestamp = datetime.utcnow()
            
            return SoilReading(
                device_id=device_id or f"ESP_{self.channel_id}",
                timestamp=timestamp,
                location=location or {},
                soil=soil_data,
            )
            
        except httpx.HTTPError as e:
            print(f"ThingSpeak API error: {e}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            print(f"Error parsing ThingSpeak data: {e}")
            return None
    
    async def fetch_historical_readings(
        self,
        device_id: Optional[str] = None,
        days: int = 7,
        location: Optional[Dict[str, float]] = None,
    ) -> List[SoilReading]:
        """
        Fetch historical sensor readings from ThingSpeak.
        
        Args:
            device_id: Device identifier
            days: Number of days of history to fetch
            location: Optional location data
            
        Returns:
            List of SoilReading objects, sorted by timestamp (oldest first)
        """
        if not self.channel_id or not self.read_api_key:
            raise ValueError("ThingSpeak channel_id and read_api_key must be configured")
        
        try:
            # ThingSpeak API endpoint for historical data
            url = f"{self.BASE_URL}/channels/{self.channel_id}/feeds.json"
            params = {
                "api_key": self.read_api_key,
                "results": min(days * 24, 8000),  # ThingSpeak limit
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            feeds = data.get("feeds", [])
            
            readings = []
            for feed in feeds:
                try:
                    soil_data = {
                        "moisture": float(feed.get("field1", feed.get("moisture", 0.0))),
                        "ph": float(feed.get("field2", feed.get("ph", 7.0))),
                        "nitrogen": float(feed.get("field3", feed.get("nitrogen", 0.0))),
                        "phosphorus": float(feed.get("field4", feed.get("phosphorus", 0.0))),
                        "potassium": float(feed.get("field5", feed.get("potassium", 0.0))),
                    }
                    
                    timestamp_str = feed.get("created_at") or feed.get("timestamp")
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        except:
                            continue
                    else:
                        continue
                    
                    readings.append(SoilReading(
                        device_id=device_id or f"ESP_{self.channel_id}",
                        timestamp=timestamp,
                        location=location or {},
                        soil=soil_data,
                    ))
                except (KeyError, ValueError, TypeError):
                    continue
            
            # Sort by timestamp (oldest first)
            readings.sort(key=lambda x: x.timestamp)
            return readings
            
        except httpx.HTTPError as e:
            print(f"ThingSpeak API error: {e}")
            return []
        except (KeyError, ValueError, TypeError) as e:
            print(f"Error parsing ThingSpeak data: {e}")
            return []
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

