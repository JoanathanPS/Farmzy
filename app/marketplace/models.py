"""Data models for Marketplace."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class QualityGrade(str, Enum):
    """Crop quality grades based on soil health."""
    PREMIUM = "A"  # soil_score >= 80
    GOOD = "B"     # 60 <= soil_score < 80
    STANDARD = "C" # soil_score < 60


class ListingStatus(str, Enum):
    """Listing status."""
    ACTIVE = "active"
    SOLD = "sold"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Listing(BaseModel):
    """Crop listing model."""
    id: Optional[str] = None
    farm_id: str
    crop: str
    quantity: float = Field(..., description="Quantity in kg")
    quality_grade: QualityGrade
    soil_score: float = Field(..., ge=0, le=100)
    suggested_price: float = Field(..., description="Price per kg in ₹")
    base_price: float = Field(..., description="Base market price per kg")
    status: ListingStatus = ListingStatus.ACTIVE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Buyer(BaseModel):
    """Buyer model."""
    id: str
    name: str
    price: float = Field(..., description="Offered price per kg")
    location: str
    rating: Optional[float] = Field(None, ge=0, le=5, description="Buyer rating 0-5")


class PricingSuggestion(BaseModel):
    """Pricing suggestion based on quality and demand."""
    quality_grade: QualityGrade
    soil_score: float
    suggested_price: float = Field(..., description="Suggested price per kg")
    base_price: float = Field(..., description="Base market price per kg")
    price_multiplier: float = Field(..., description="Quality multiplier")
    buyers_available: int = Field(default=0, description="Number of available buyers")


class Order(BaseModel):
    """Order model."""
    id: Optional[str] = None
    listing_id: str
    buyer_id: str
    farm_id: str
    quantity: float = Field(..., description="Quantity in kg")
    price_per_kg: float = Field(..., description="Price per kg")
    total_price: float = Field(..., description="Total order value")
    status: str = Field(default="pending", description="pending, confirmed, shipped, delivered, cancelled")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None






