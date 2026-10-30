"""Database models for Farmzy."""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.database import Base


class SoilReadingDB(Base):
    """Database model for raw soil sensor readings."""
    __tablename__ = "soil_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    location = Column(JSON, nullable=True)
    moisture = Column(Float, nullable=False)
    ph = Column(Float, nullable=False)
    nitrogen = Column(Float, nullable=False)
    phosphorus = Column(Float, nullable=False)
    potassium = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "location": self.location,
            "soil": {
                "moisture": self.moisture,
                "ph": self.ph,
                "nitrogen": self.nitrogen,
                "phosphorus": self.phosphorus,
                "potassium": self.potassium,
            },
        }


class SoilHealthDB(Base):
    """Database model for soil health snapshots."""
    __tablename__ = "soil_health"
    
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(String, index=True, nullable=True)
    device_id = Column(String, index=True, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    nitrogen_status = Column(String, nullable=False)
    nitrogen_value = Column(Float, nullable=False)
    phosphorus_status = Column(String, nullable=False)
    phosphorus_value = Column(Float, nullable=False)
    potassium_status = Column(String, nullable=False)
    potassium_value = Column(Float, nullable=False)
    ph_status = Column(String, nullable=False)
    ph_value = Column(Float, nullable=False)
    moisture_status = Column(String, nullable=False)
    moisture_value = Column(Float, nullable=False)
    soil_score = Column(Float, nullable=False)
    degradation_index = Column(Float, nullable=False)
    depletion_rates = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RecommendationDB(Base):
    """Database model for soil recommendations."""
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True, nullable=False)
    farm_id = Column(String, index=True, nullable=True)
    nitrogen_rec = Column(Text, nullable=True)
    phosphorus_rec = Column(Text, nullable=True)
    potassium_rec = Column(Text, nullable=True)
    ph_rec = Column(Text, nullable=True)
    irrigation_rec = Column(Text, nullable=True)
    priority = Column(String, nullable=False, default="medium")
    estimated_cost = Column(Float, nullable=True)
    urgency_days = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_acknowledged = Column(String, default="false")


class IrrigationPlanDB(Base):
    """Database model for irrigation plans."""
    __tablename__ = "irrigation_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(String, index=True, nullable=False)
    irrigate = Column(String, nullable=False)  # "true" or "false" as string
    net_water_liters = Column(Float, nullable=False)
    zones = Column(JSON, nullable=True)  # List of zone distributions
    strategy = Column(JSON, nullable=True)  # Cycle strategy
    reasons = Column(JSON, nullable=True)  # List of reasons
    confidence = Column(Float, nullable=False)
    computed_values = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="pending")  # pending, scheduled, executing, completed, cancelled
    scheduled_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class IrrigationExecutionDB(Base):
    """Database model for irrigation execution history."""
    __tablename__ = "irrigation_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, index=True, nullable=False)
    farm_id = Column(String, index=True, nullable=False)
    executed_zones = Column(JSON, nullable=True)  # List of executed zones
    actual_water_liters = Column(Float, nullable=True)
    execution_start = Column(DateTime(timezone=True), nullable=False)
    execution_end = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False, default="executing")  # executing, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ListingDB(Base):
    """Database model for marketplace listings."""
    __tablename__ = "listings"
    
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(String, index=True, nullable=False)
    crop = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    quality_grade = Column(String, nullable=False)  # A, B, C
    soil_score = Column(Float, nullable=False)
    suggested_price = Column(Float, nullable=False)
    base_price = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="active")  # active, sold, cancelled, expired
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class OrderDB(Base):
    """Database model for marketplace orders."""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(String, index=True, nullable=False)
    buyer_id = Column(String, index=True, nullable=False)
    farm_id = Column(String, index=True, nullable=False)
    quantity = Column(Float, nullable=False)
    price_per_kg = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, confirmed, shipped, delivered, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DeliveryDB(Base):
    """Database model for delivery records."""
    __tablename__ = "deliveries"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, index=True, nullable=False)
    farm_id = Column(String, index=True, nullable=False)
    route_id = Column(String, index=True, nullable=True)
    pickup_time = Column(DateTime(timezone=True), nullable=False)
    delivery_distance_km = Column(Float, nullable=False)
    estimated_cost = Column(Float, nullable=False)
    actual_cost = Column(Float, nullable=True)
    delivery_status = Column(String, nullable=False, default="scheduled")  # scheduled, in_transit, delivered, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class RouteDB(Base):
    """Database model for delivery routes."""
    __tablename__ = "routes"
    
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(String, unique=True, index=True, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    farms = Column(JSON, nullable=False)  # List of farm locations
    total_distance_km = Column(Float, nullable=False)
    estimated_cost = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="planned")  # planned, active, completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

