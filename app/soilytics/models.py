"""Data models for Soilytics."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class NutrientStatus(str, Enum):
    """Nutrient status levels."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXCESS = "excess"


class PHStatus(str, Enum):
    """pH status levels."""
    ACIDIC = "acidic"
    OPTIMAL = "optimal"
    ALKALINE = "alkaline"


class MoistureStatus(str, Enum):
    """Moisture status levels."""
    CRITICAL = "critical"
    LOW = "low"
    MODERATE = "moderate"
    ADEQUATE = "adequate"
    EXCESS = "excess"


class SoilReading(BaseModel):
    """Raw sensor reading from ESP device."""
    device_id: str
    timestamp: datetime
    location: dict = Field(default_factory=dict)  # {"lat": float, "lng": float}
    soil: dict = Field(..., description="Soil sensor data")
    
    @property
    def moisture(self) -> float:
        """Extract moisture percentage."""
        return self.soil.get("moisture", 0.0)
    
    @property
    def ph(self) -> float:
        """Extract pH value."""
        return self.soil.get("ph", 7.0)
    
    @property
    def nitrogen(self) -> float:
        """Extract nitrogen (mg/kg)."""
        return self.soil.get("nitrogen", 0.0)
    
    @property
    def phosphorus(self) -> float:
        """Extract phosphorus (mg/kg)."""
        return self.soil.get("phosphorus", 0.0)
    
    @property
    def potassium(self) -> float:
        """Extract potassium (mg/kg)."""
        return self.soil.get("potassium", 0.0)


class NutrientAnalysis(BaseModel):
    """Analysis of a single nutrient."""
    value: float
    status: NutrientStatus
    threshold_min: float
    threshold_max: float
    recommendation: Optional[str] = None


class SoilHealth(BaseModel):
    """Comprehensive soil health snapshot."""
    farm_id: Optional[str] = None
    device_id: str
    date: datetime
    nitrogen: NutrientAnalysis
    phosphorus: NutrientAnalysis
    potassium: NutrientAnalysis
    ph_status: PHStatus
    ph_value: float
    moisture_status: MoistureStatus
    moisture_value: float
    soil_score: float = Field(..., ge=0, le=100, description="Overall soil health score 0-100")
    degradation_index: float = Field(..., ge=0, le=100, description="Soil Degradation Index 0-100")
    depletion_rates: dict = Field(default_factory=dict, description="Daily depletion rates for NPK")


class SoilRecommendation(BaseModel):
    """Actionable recommendations for soil improvement."""
    nitrogen: Optional[str] = None
    phosphorus: Optional[str] = None
    potassium: Optional[str] = None
    ph: Optional[str] = None
    irrigation: Optional[str] = None
    priority: str = Field(default="medium", description="low, medium, high, critical")
    estimated_cost: Optional[float] = None
    urgency_days: Optional[int] = None

