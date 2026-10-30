"""Shared Farm Model - Single Source of Truth for all modules."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class Location(BaseModel):
    """Farm location."""
    name: str
    lat: float
    lng: float


class Zone(BaseModel):
    """Irrigation zone."""
    zone_id: str
    area_acres: float
    area_m2: float


class FarmModel(BaseModel):
    """Core farm model - used by all modules."""
    farm_id: str
    location: Location
    area_acres: float
    area_m2: float
    soil_type: str  # loamy, sandy, clay, silty
    crop: str  # paddy, wheat, maize, vegetables, tomato, cotton
    irrigation_type: str  # drip, sprinkler, flood
    flow_rate_lph: float
    zones: List[Zone]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "farm_id": "FARM_PNL_01",
                "location": {
                    "name": "Poonamallee, Chennai",
                    "lat": 13.0475,
                    "lng": 80.1112
                },
                "area_acres": 2.0,
                "area_m2": 8093.72,
                "soil_type": "loamy",
                "crop": "paddy",
                "irrigation_type": "drip",
                "flow_rate_lph": 2000.0,
                "zones": [
                    {
                        "zone_id": "Z1",
                        "area_acres": 1.0,
                        "area_m2": 4046.86
                    },
                    {
                        "zone_id": "Z2",
                        "area_acres": 1.0,
                        "area_m2": 4046.86
                    }
                ]
            }
        }


# Default farm for demo
DEFAULT_FARM = FarmModel(
    farm_id="FARM_PNL_01",
    location=Location(
        name="Poonamallee, Chennai",
        lat=13.0475,
        lng=80.1112
    ),
    area_acres=2.0,
    area_m2=8093.72,
    soil_type="loamy",
    crop="paddy",
    irrigation_type="drip",
    flow_rate_lph=2000.0,
    zones=[
        Zone(zone_id="Z1", area_acres=1.0, area_m2=4046.86),
        Zone(zone_id="Z2", area_acres=1.0, area_m2=4046.86)
    ]
)
