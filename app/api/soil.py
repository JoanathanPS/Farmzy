"""Soil data and health API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import datetime, timedelta
from app.database import get_db
from app.models import SoilReadingDB, SoilHealthDB, RecommendationDB
from app.soilytics.engine import SoilIntelligenceEngine
from app.soilytics.models import SoilReading, SoilHealth, SoilRecommendation
from app.soilytics.thingspeak import ThingSpeakClient
from pydantic import BaseModel

router = APIRouter(prefix="/api/soil", tags=["soil"])

# Initialize engine
engine = SoilIntelligenceEngine()


class SoilReadingInput(BaseModel):
    """Input model for soil reading."""
    device_id: str
    timestamp: Optional[datetime] = None
    location: Optional[dict] = None
    soil: dict


async def _process_soil_reading(
    soil_reading: SoilReading,
    db: Session,
) -> dict:
    """
    Internal function to process a soil reading.
    Returns dict with reading_id, health_id, recommendation_id.
    """
    # Store raw reading in database
    db_reading = SoilReadingDB(
        device_id=soil_reading.device_id,
        timestamp=soil_reading.timestamp,
        location=soil_reading.location,
        moisture=soil_reading.moisture,
        ph=soil_reading.ph,
        nitrogen=soil_reading.nitrogen,
        phosphorus=soil_reading.phosphorus,
        potassium=soil_reading.potassium,
    )
    db.add(db_reading)
    db.flush()
    
    # Get previous reading for depletion calculation
    previous_db = db.query(SoilReadingDB).filter(
        SoilReadingDB.device_id == soil_reading.device_id
    ).order_by(desc(SoilReadingDB.timestamp)).offset(1).first()
    
    previous_reading = None
    if previous_db:
        previous_reading = SoilReading(
            device_id=previous_db.device_id,
            timestamp=previous_db.timestamp,
            location=previous_db.location or {},
            soil={
                "moisture": previous_db.moisture,
                "ph": previous_db.ph,
                "nitrogen": previous_db.nitrogen,
                "phosphorus": previous_db.phosphorus,
                "potassium": previous_db.potassium,
            },
        )
    
    # Analyze soil health
    health = engine.analyze_soil_reading(soil_reading, previous_reading)
    
    # Store health snapshot
    db_health = SoilHealthDB(
        device_id=health.device_id,
        date=health.date,
        nitrogen_status=health.nitrogen.status.value,
        nitrogen_value=health.nitrogen.value,
        phosphorus_status=health.phosphorus.status.value,
        phosphorus_value=health.phosphorus.value,
        potassium_status=health.potassium.status.value,
        potassium_value=health.potassium.value,
        ph_status=health.ph_status.value,
        ph_value=health.ph_value,
        moisture_status=health.moisture_status.value,
        moisture_value=health.moisture_value,
        soil_score=health.soil_score,
        degradation_index=health.degradation_index,
        depletion_rates=health.depletion_rates,
    )
    db.add(db_health)
    db.flush()
    
    # Generate recommendations
    recommendations = engine.generate_recommendations(health)
    
    # Store recommendations
    db_rec = RecommendationDB(
        device_id=health.device_id,
        nitrogen_rec=recommendations.nitrogen,
        phosphorus_rec=recommendations.phosphorus,
        potassium_rec=recommendations.potassium,
        ph_rec=recommendations.ph,
        irrigation_rec=recommendations.irrigation,
        priority=recommendations.priority,
        estimated_cost=recommendations.estimated_cost,
        urgency_days=recommendations.urgency_days,
    )
    db.add(db_rec)
    
    db.commit()
    
    return {
        "reading_id": db_reading.id,
        "health_id": db_health.id,
        "recommendation_id": db_rec.id,
    }


@router.post("/data")
async def ingest_soil_data(
    reading: SoilReadingInput,
    db: Session = Depends(get_db),
):
    """
    Ingest raw soil sensor data from ESP device.
    
    This endpoint accepts sensor readings and:
    1. Stores raw data
    2. Analyzes soil health
    3. Generates recommendations
    """
    try:
        # Parse input
        if reading.timestamp is None:
            reading.timestamp = datetime.utcnow()
        
        soil_reading = SoilReading(
            device_id=reading.device_id,
            timestamp=reading.timestamp,
            location=reading.location or {},
            soil=reading.soil,
        )
        
        result = await _process_soil_reading(soil_reading, db)
        
        return {
            "message": "Soil data ingested successfully",
            **result,
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing soil data: {str(e)}")


@router.get("/health")
async def get_soil_health(
    device_id: Optional[str] = Query(None, description="Device ID"),
    farm_id: Optional[str] = Query(None, description="Farm ID"),
    db: Session = Depends(get_db),
):
    """
    Get latest soil health snapshot for a device or farm.
    """
    query = db.query(SoilHealthDB)
    
    if device_id:
        query = query.filter(SoilHealthDB.device_id == device_id)
    if farm_id:
        query = query.filter(SoilHealthDB.farm_id == farm_id)
    
    latest_health = query.order_by(desc(SoilHealthDB.date)).first()
    
    if not latest_health:
        raise HTTPException(status_code=404, detail="No soil health data found")
    
    # Get latest recommendations
    rec_query = db.query(RecommendationDB).filter(
        RecommendationDB.device_id == latest_health.device_id
    )
    if farm_id:
        rec_query = rec_query.filter(RecommendationDB.farm_id == farm_id)
    
    latest_rec = rec_query.order_by(desc(RecommendationDB.created_at)).first()
    
    response = {
        "device_id": latest_health.device_id,
        "farm_id": latest_health.farm_id,
        "date": latest_health.date.isoformat(),
        "nitrogen": {
            "value": latest_health.nitrogen_value,
            "status": latest_health.nitrogen_status,
        },
        "phosphorus": {
            "value": latest_health.phosphorus_value,
            "status": latest_health.phosphorus_status,
        },
        "potassium": {
            "value": latest_health.potassium_value,
            "status": latest_health.potassium_status,
        },
        "ph": {
            "value": latest_health.ph_value,
            "status": latest_health.ph_status,
        },
        "moisture": {
            "value": latest_health.moisture_value,
            "status": latest_health.moisture_status,
        },
        "soil_score": latest_health.soil_score,
        "degradation_index": latest_health.degradation_index,
        "depletion_rates": latest_health.depletion_rates or {},
    }
    
    if latest_rec:
        response["recommendations"] = {
            "nitrogen": latest_rec.nitrogen_rec,
            "phosphorus": latest_rec.phosphorus_rec,
            "potassium": latest_rec.potassium_rec,
            "ph": latest_rec.ph_rec,
            "irrigation": latest_rec.irrigation_rec,
            "priority": latest_rec.priority,
            "estimated_cost": latest_rec.estimated_cost,
            "urgency_days": latest_rec.urgency_days,
        }
    
    return response


@router.get("/degradation")
async def get_degradation_trends(
    device_id: str = Query(..., description="Device ID"),
    range_days: int = Query(30, alias="range", description="Number of days"),
    db: Session = Depends(get_db),
):
    """
    Get soil degradation trends over time.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=range_days)
    
    health_records = db.query(SoilHealthDB).filter(
        SoilHealthDB.device_id == device_id,
        SoilHealthDB.date >= cutoff_date,
    ).order_by(SoilHealthDB.date).all()
    
    if not health_records:
        raise HTTPException(status_code=404, detail="No degradation data found")
    
    trends = []
    for record in health_records:
        trends.append({
            "date": record.date.isoformat(),
            "soil_score": record.soil_score,
            "degradation_index": record.degradation_index,
            "nitrogen_value": record.nitrogen_value,
            "phosphorus_value": record.phosphorus_value,
            "potassium_value": record.potassium_value,
            "depletion_rates": record.depletion_rates or {},
        })
    
    return {
        "device_id": device_id,
        "range_days": range_days,
        "trends": trends,
    }


@router.get("/fetch-thingspeak")
async def fetch_from_thingspeak(
    device_id: Optional[str] = Query(None, description="Device ID override"),
    location: Optional[str] = Query(None, description="Location JSON string"),
    db: Session = Depends(get_db),
):
    """
    Fetch latest sensor data from ThingSpeak and process it.
    """
    try:
        client = ThingSpeakClient()
        
        # Parse location if provided
        loc_dict = None
        if location:
            import json
            loc_dict = json.loads(location)
        
        # Fetch latest reading
        reading = await client.fetch_latest_reading(
            device_id=device_id,
            location=loc_dict,
        )
        
        if not reading:
            raise HTTPException(
                status_code=404,
                detail="Failed to fetch data from ThingSpeak or no data available"
            )
        
        # Process the reading
        result = await _process_soil_reading(reading, db)
        
        await client.close()
        
        return {
            "message": "Successfully fetched and processed data from ThingSpeak",
            **result,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching from ThingSpeak: {str(e)}")


@router.get("/readings")
async def get_soil_readings(
    device_id: Optional[str] = Query(None, description="Device ID"),
    limit: int = Query(100, le=1000, description="Number of readings to return"),
    db: Session = Depends(get_db),
):
    """
    Get historical soil readings.
    """
    query = db.query(SoilReadingDB)
    
    if device_id:
        query = query.filter(SoilReadingDB.device_id == device_id)
    
    readings = query.order_by(desc(SoilReadingDB.timestamp)).limit(limit).all()
    
    return {
        "readings": [reading.to_dict() for reading in readings],
        "count": len(readings),
    }

