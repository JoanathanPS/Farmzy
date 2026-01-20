"""Data models for HydroIQ."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class ZoneWaterDistribution(BaseModel):
    """Water distribution for a single zone."""
    zone_id: str
    water_liters: float
    duration_minutes: int
    area_m2: float


class IrrigationStrategy(BaseModel):
    """Irrigation cycle strategy."""
    cycle_on_min: int = Field(default=30, description="Minutes ON per cycle")
    cycle_off_min: int = Field(default=30, description="Minutes OFF per cycle")
    total_cycles: Optional[int] = None


class IrrigationDecision(BaseModel):
    """Complete irrigation decision output."""
    irrigate: bool
    net_water_liters: float
    zones: List[ZoneWaterDistribution]
    strategy: IrrigationStrategy
    reasons: List[str]
    confidence: float = Field(..., ge=0.0, le=1.0, description="Decision confidence 0-1")
    computed_values: Dict[str, float] = Field(default_factory=dict)
    timestamp: datetime


class IrrigationPlan(BaseModel):
    """Irrigation plan for execution."""
    plan_id: Optional[int] = None
    farm_id: str
    decision: IrrigationDecision
    scheduled_time: Optional[datetime] = None
    status: str = Field(default="pending", description="pending, scheduled, executing, completed, cancelled")
    created_at: Optional[datetime] = None


class WeatherData(BaseModel):
    """Weather data for irrigation calculation."""
    min_temperature: float = Field(..., alias="min_temp", description="Minimum temperature in °C")
    max_temperature: float = Field(..., alias="max_temp", description="Maximum temperature in °C")
    average_temperature: float = Field(..., alias="avg_temp", description="Average temperature in °C")
    rainfall_mm: float = Field(default=0.0, description="Rainfall in mm")
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    
    class Config:
        allow_population_by_field_name = True


class SoilData(BaseModel):
    """Soil data from Soilytics."""
    moisture: float = Field(..., ge=0, le=100, description="Soil moisture percentage")
    soil_score: Optional[float] = Field(None, ge=0, le=100, description="Soil health score")
    timestamp: Optional[datetime] = None






