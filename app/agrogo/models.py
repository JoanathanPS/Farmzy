"""Data models for AgroGo."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class DeliveryStatus(str, Enum):
    """Delivery status."""
    SCHEDULED = "scheduled"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PickupPoint(BaseModel):
    """Pickup point (farm location)."""
    farm_id: str
    location: dict = Field(..., description="{'lat': float, 'lng': float, 'name': str}")
    order_id: Optional[str] = None
    quantity_kg: Optional[float] = None


class Route(BaseModel):
    """Delivery route with multiple pickups."""
    route_id: str
    date: datetime
    farms: List[PickupPoint]
    total_distance_km: float
    estimated_cost: float
    pickup_sequence: List[str] = Field(default_factory=list, description="Ordered list of farm_ids")


class Delivery(BaseModel):
    """Delivery record."""
    id: Optional[str] = None
    order_id: str
    farm_id: str
    route_id: Optional[str] = None
    pickup_time: datetime
    delivery_distance_km: float
    estimated_cost: float
    actual_cost: Optional[float] = None
    delivery_status: DeliveryStatus = DeliveryStatus.SCHEDULED
    created_at: Optional[datetime] = None






