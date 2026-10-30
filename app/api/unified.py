"""Unified API endpoints - All modules together (Supabase-first)."""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.core.farm_model import FarmModel, DEFAULT_FARM
from app.hydroiq.engine import HydroIQEngine
from app.hydroiq.models import SoilData, WeatherData
from app.hydroiq.weather_service import weather_service
from app.marketplace.engine import MarketplaceEngine
from app.agrogo.engine import AgroGoEngine
from app.models import SoilHealthDB, OrderDB, ListingDB, DeliveryDB
from app.supabase_client import supabase

router = APIRouter(prefix="/api/unified", tags=["unified"])

# Initialize engines
hydroiq_engine = HydroIQEngine()
marketplace_engine = MarketplaceEngine()
agrogo_engine = AgroGoEngine()


@router.get("/dashboard")
async def get_dashboard(
    farm_id: Optional[str] = Query("FARM_PNL_01", description="Farm ID"),
    device_id: Optional[str] = Query("ESP_FARM_01", description="Device ID"),
    db: Optional[Session] = Depends(get_db),
):
    """
    Get unified dashboard data - all 4 skills together.
    Single endpoint that powers the main dashboard.
    """
    try:
        farm = DEFAULT_FARM
        soil_health = None

        if supabase.is_configured:
            sh = supabase.get_latest_soil_health(device_id=device_id)
            if sh:
                soil_health = {
                    "soil_score": float(sh.get("soil_score", 70.0)),
                    "moisture": float(sh.get("moisture_value", 38.0)),
                    "ph": float(sh.get("ph_value", 6.4)),
                    "nitrogen": {
                        "value": sh.get("nitrogen_value", 42),
                        "status": sh.get("nitrogen_status", "medium"),
                    },
                    "phosphorus": {
                        "value": sh.get("phosphorus_value", 18),
                        "status": sh.get("phosphorus_status", "low"),
                    },
                    "potassium": {
                        "value": sh.get("potassium_value", 155),
                        "status": sh.get("potassium_status", "medium"),
                    },
                    "degradation_index": float(sh.get("degradation_index", 22.0)),
                }
        elif db:
            try:
                latest_health = db.query(SoilHealthDB).filter(
                    SoilHealthDB.device_id == device_id
                ).order_by(SoilHealthDB.date.desc()).first()

                if latest_health:
                    soil_health = {
                        "soil_score": latest_health.soil_score,
                        "moisture": latest_health.moisture_value,
                        "ph": latest_health.ph_value,
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
                        "degradation_index": latest_health.degradation_index,
                    }
            except:
                pass

        if not soil_health:
            soil_health = {
                "soil_score": 70.0,
                "moisture": 38.0,
                "ph": 6.4,
                "nitrogen": {"value": 42, "status": "medium"},
                "phosphorus": {"value": 18, "status": "low"},
                "potassium": {"value": 155, "status": "medium"},
                "degradation_index": 22.0,
            }

        # Get weather data
        weather = await weather_service.get_weather(
            farm.location.lat,
            farm.location.lng,
        )

        # Compute irrigation decision (HydroIQ)
        soil_data = SoilData(
            moisture=soil_health["moisture"],
            soil_score=soil_health["soil_score"],
        )
        irrigation_decision = hydroiq_engine.compute_irrigation_decision(
            farm, soil_data, weather
        )

        # Get marketplace pricing
        pricing = marketplace_engine.calculate_pricing(
            farm.crop,
            soil_health["soil_score"],
        )

        # Get active listings
        listings_data = []
        if supabase.is_configured:
            listings = supabase.get_listings(farm_id=farm_id, status="active", limit=5)
            listings_data = [
                {
                    "id": str(l.get("id")),
                    "crop": l.get("crop"),
                    "quantity": l.get("quantity"),
                    "quality_grade": l.get("quality_grade"),
                    "suggested_price": l.get("suggested_price"),
                }
                for l in listings
            ]
        elif db:
            try:
                listings = db.query(ListingDB).filter(
                    ListingDB.farm_id == farm_id,
                    ListingDB.status == "active",
                ).limit(5).all()
                listings_data = [
                    {
                        "id": str(l.id),
                        "crop": l.crop,
                        "quantity": l.quantity,
                        "quality_grade": l.quality_grade,
                        "suggested_price": l.suggested_price,
                    }
                    for l in listings
                ]
            except:
                listings_data = []

        # Get pending deliveries
        deliveries_data = []
        if supabase.is_configured:
            deliveries = supabase.get_deliveries(farm_id=farm_id, limit=5)
            deliveries_data = [
                {
                    "id": str(d.get("id")),
                    "order_id": d.get("order_id"),
                    "pickup_time": d.get("pickup_time"),
                    "delivery_status": d.get("delivery_status"),
                    "estimated_cost": d.get("estimated_cost"),
                }
                for d in deliveries
            ]
        elif db:
            try:
                deliveries = db.query(DeliveryDB).filter(
                    DeliveryDB.farm_id == farm_id,
                    DeliveryDB.delivery_status.in_(["scheduled", "in_transit"]),
                ).limit(5).all()
                deliveries_data = [
                    {
                        "id": str(d.id),
                        "order_id": d.order_id,
                        "pickup_time": d.pickup_time.isoformat() if d.pickup_time else None,
                        "delivery_status": d.delivery_status,
                        "estimated_cost": d.estimated_cost,
                    }
                    for d in deliveries
                ]
            except:
                deliveries_data = []

        return {
            "farm": farm.dict(),
            "soil": soil_health,
            "irrigation": {
                "irrigate": irrigation_decision.irrigate,
                "net_water_liters": irrigation_decision.net_water_liters,
                "zones": [zone.dict() for zone in irrigation_decision.zones],
                "confidence": irrigation_decision.confidence,
                "reasons": irrigation_decision.reasons,
            },
            "marketplace": {
                "pricing": pricing.dict(),
                "listings": listings_data,
            },
            "delivery": {
                "pending_deliveries": deliveries_data,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating dashboard: {str(e)}")


@router.get("/farm/{farm_id}")
async def get_farm(farm_id: str):
    """Get farm model."""
    if farm_id == DEFAULT_FARM.farm_id:
        return DEFAULT_FARM.dict()
    raise HTTPException(status_code=404, detail="Farm not found")


@router.post("/compute-all")
async def compute_all_modules(
    farm_id: Optional[str] = "FARM_PNL_01",
    device_id: Optional[str] = "ESP_FARM_01",
    soil_data: Optional[dict] = None,
    weather_data: Optional[dict] = None,
    db: Optional[Session] = Depends(get_db),
):
    """
    Compute all modules at once.
    """
    try:
        farm = DEFAULT_FARM

        if not soil_data:
            if supabase.is_configured:
                sh = supabase.get_latest_soil_health(device_id=device_id)
                if sh:
                    soil_data = {
                        "moisture": float(sh.get("moisture_value", 38.0)),
                        "soil_score": float(sh.get("soil_score", 70.0)),
                    }
            elif db:
                try:
                    latest_health = db.query(SoilHealthDB).filter(
                        SoilHealthDB.device_id == device_id
                    ).order_by(SoilHealthDB.date.desc()).first()
                    if latest_health:
                        soil_data = {
                            "moisture": latest_health.moisture_value,
                            "soil_score": latest_health.soil_score,
                        }
                except:
                    pass

            if not soil_data:
                soil_data = {
                    "moisture": 38.0,
                    "soil_score": 70.0,
                }

        if not weather_data:
            weather = await weather_service.get_weather(
                farm.location.lat,
                farm.location.lng,
            )
        else:
            weather = WeatherData(**weather_data)

        soil_data_obj = SoilData(**soil_data)
        irrigation_decision = hydroiq_engine.compute_irrigation_decision(
            farm, soil_data_obj, weather
        )

        pricing = marketplace_engine.calculate_pricing(
            farm.crop,
            soil_data["soil_score"],
        )

        return {
            "success": True,
            "soil": {
                "moisture": soil_data["moisture"],
                "soil_score": soil_data["soil_score"],
            },
            "irrigation": {
                "irrigate": irrigation_decision.irrigate,
                "net_water_liters": irrigation_decision.net_water_liters,
                "zones": [zone.dict() for zone in irrigation_decision.zones],
                "confidence": irrigation_decision.confidence,
                "computed_values": irrigation_decision.computed_values,
            },
            "marketplace": pricing.dict(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing modules: {str(e)}")
