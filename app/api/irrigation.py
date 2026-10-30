"""HydroIQ - Smart Irrigation Intelligence API endpoints (Supabase-first)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.database import get_db
from app.models import IrrigationPlanDB, IrrigationExecutionDB, SoilHealthDB
from app.hydroiq.engine import HydroIQEngine
from app.hydroiq.models import IrrigationDecision, SoilData, WeatherData
from app.hydroiq.weather_service import weather_service
from app.core.farm_model import FarmModel, DEFAULT_FARM
from app.supabase_client import supabase

router = APIRouter(prefix="/api/irrigation", tags=["irrigation"])

# Initialize engine
engine = HydroIQEngine()


class IrrigationComputeRequest(BaseModel):
    """Request model for irrigation computation."""
    farm_id: str
    soil_data: Optional[dict] = None
    weather_data: Optional[dict] = None


class IrrigationExecuteRequest(BaseModel):
    """Request model for irrigation execution logging."""
    plan_id: int
    zones: List[dict]


@router.post("/compute")
async def compute_irrigation(
    request: IrrigationComputeRequest,
    db: Optional[Session] = Depends(get_db),
):
    """
    Compute irrigation decision for a farm.
    """
    try:
        farm = DEFAULT_FARM
        soil_data = None

        if request.soil_data:
            soil_data = SoilData(**request.soil_data)
        elif supabase.is_configured:
            device_id = f"ESP_{request.farm_id}"
            sh = supabase.get_latest_soil_health(device_id=device_id)
            if sh:
                soil_data = SoilData(
                    moisture=float(sh.get("moisture_value", 38.0)),
                    soil_score=float(sh.get("soil_score", 70.0)),
                    timestamp=datetime.fromisoformat(sh["date"].replace("Z", "+00:00")) if "date" in sh else None,
                )
        elif db:
            try:
                device_id = f"ESP_{request.farm_id}"
                latest_health = db.query(SoilHealthDB).filter(
                    SoilHealthDB.device_id == device_id
                ).order_by(desc(SoilHealthDB.date)).first()
                if latest_health:
                    soil_data = SoilData(
                        moisture=latest_health.moisture_value,
                        soil_score=latest_health.soil_score,
                        timestamp=latest_health.date,
                    )
            except:
                pass

        if not soil_data:
            soil_data = SoilData(moisture=38.0, soil_score=70.0)

        # Get weather data
        weather = None
        if request.weather_data:
            weather = WeatherData(**request.weather_data)
        else:
            weather = await weather_service.get_weather(
                farm.location.lat,
                farm.location.lng,
            )

        # Compute irrigation decision
        decision = engine.compute_irrigation_decision(farm, soil_data, weather)

        plan_id = None
        if supabase.is_configured:
            created_plan = supabase.create_irrigation_plan({
                "farm_id": farm.farm_id,
                "irrigate": str(decision.irrigate).lower(),
                "net_water_liters": decision.net_water_liters,
                "zones": [zone.dict() for zone in decision.zones],
                "strategy": decision.strategy.dict(),
                "reasons": decision.reasons,
                "confidence": decision.confidence,
                "computed_values": decision.computed_values,
                "status": "pending",
            })
            if created_plan:
                plan_id = created_plan.get("id")
        elif db:
            db_plan = IrrigationPlanDB(
                farm_id=farm.farm_id,
                irrigate=str(decision.irrigate).lower(),
                net_water_liters=decision.net_water_liters,
                zones=[zone.dict() for zone in decision.zones],
                strategy=decision.strategy.dict(),
                reasons=decision.reasons,
                confidence=decision.confidence,
                computed_values=decision.computed_values,
                status="pending",
            )
            db.add(db_plan)
            db.commit()
            db.refresh(db_plan)
            plan_id = db_plan.id

        return {
            "success": True,
            "plan_id": plan_id,
            "decision": {
                "irrigate": decision.irrigate,
                "net_water_liters": decision.net_water_liters,
                "zones": [zone.dict() for zone in decision.zones],
                "strategy": decision.strategy.dict(),
                "reasons": decision.reasons,
                "confidence": decision.confidence,
                "computed_values": decision.computed_values,
                "timestamp": decision.timestamp.isoformat(),
            },
        }

    except Exception as e:
        if db:
            db.rollback()
        raise HTTPException(status_code=500, detail=f"Error computing irrigation: {str(e)}")


@router.post("/execute")
async def execute_irrigation(
    request: IrrigationExecuteRequest,
    db: Optional[Session] = Depends(get_db),
):
    """
    Mark an irrigation plan as executed and log execution.
    """
    try:
        if supabase.is_configured:
            supabase.update(
                "irrigation_plans",
                {"status": "executing"},
                {"id": f"eq.{request.plan_id}"}
            )
            exec_record = supabase.insert("irrigation_executions", {
                "plan_id": request.plan_id,
                "farm_id": DEFAULT_FARM.farm_id,
                "executed_zones": request.zones,
                "execution_start": datetime.utcnow().isoformat(),
                "status": "executing",
            })
            return {
                "success": True,
                "execution_id": exec_record.get("id") if exec_record else None,
                "message": "Irrigation execution logged",
            }

        if not db:
            raise HTTPException(status_code=500, detail="Database not configured")

        plan = db.query(IrrigationPlanDB).filter(
            IrrigationPlanDB.id == request.plan_id
        ).first()

        if not plan:
            raise HTTPException(status_code=404, detail="Irrigation plan not found")

        execution = IrrigationExecutionDB(
            plan_id=plan.id,
            farm_id=plan.farm_id,
            executed_zones=request.zones,
            execution_start=datetime.utcnow(),
            status="executing",
        )
        db.add(execution)
        plan.status = "executing"
        db.commit()
        db.refresh(execution)

        return {
            "success": True,
            "execution_id": execution.id,
            "message": "Irrigation execution logged",
        }

    except HTTPException:
        raise
    except Exception as e:
        if db:
            db.rollback()
        raise HTTPException(status_code=500, detail=f"Error logging execution: {str(e)}")


@router.get("/history")
async def get_irrigation_history(
    farm_id: str = Query(..., description="Farm ID"),
    limit: int = Query(50, description="Number of records"),
    db: Optional[Session] = Depends(get_db),
):
    """
    Retrieve irrigation history for a farm.
    """
    try:
        if supabase.is_configured:
            plans = supabase.get_irrigation_plans(farm_id=farm_id, limit=limit)
            return {
                "success": True,
                "plans": [
                    {
                        "id": plan.get("id"),
                        "farm_id": plan.get("farm_id"),
                        "irrigate": plan.get("irrigate") == "true",
                        "net_water_liters": plan.get("net_water_liters"),
                        "zones": plan.get("zones"),
                        "confidence": plan.get("confidence"),
                        "status": plan.get("status"),
                        "created_at": plan.get("created_at"),
                    }
                    for plan in plans
                ],
                "total": len(plans),
            }

        if not db:
            return {"success": True, "plans": [], "total": 0}

        plans = db.query(IrrigationPlanDB).filter(
            IrrigationPlanDB.farm_id == farm_id
        ).order_by(desc(IrrigationPlanDB.created_at)).limit(limit).all()

        return {
            "success": True,
            "plans": [
                {
                    "id": plan.id,
                    "farm_id": plan.farm_id,
                    "irrigate": plan.irrigate == "true",
                    "net_water_liters": plan.net_water_liters,
                    "zones": plan.zones,
                    "confidence": plan.confidence,
                    "status": plan.status,
                    "created_at": plan.created_at.isoformat() if plan.created_at else None,
                }
                for plan in plans
            ],
            "total": len(plans),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")


@router.get("/insights")
async def get_irrigation_insights(
    farm_id: str = Query(..., description="Farm ID"),
    period: str = Query("month", description="Period: week, month, year"),
    db: Optional[Session] = Depends(get_db),
):
    """
    Provide analytics and insights for irrigation.
    """
    try:
        total_water = 0.0
        total_sessions = 0

        if supabase.is_configured:
            plans = supabase.get_irrigation_plans(farm_id=farm_id, limit=50)
            irrigated_plans = [p for p in plans if p.get("irrigate") == "true"]
            total_water = sum(float(p.get("net_water_liters", 0)) for p in irrigated_plans)
            total_sessions = len(irrigated_plans)
        elif db:
            plans = db.query(IrrigationPlanDB).filter(
                IrrigationPlanDB.farm_id == farm_id,
                IrrigationPlanDB.irrigate == "true",
            ).all()
            total_water = sum(plan.net_water_liters for plan in plans)
            total_sessions = len(plans)

        avg_water = total_water / total_sessions if total_sessions > 0 else 0
        farm = DEFAULT_FARM
        traditional_water = farm.area_m2 * 10 * total_sessions
        water_saved = max(0, traditional_water - total_water)

        return {
            "success": True,
            "insights": {
                "total_water_used_liters": round(total_water, 2),
                "total_irrigation_sessions": total_sessions,
                "average_water_per_session": round(avg_water, 2),
                "water_savings_estimate_liters": round(water_saved, 2),
                "efficiency_score": round((water_saved / traditional_water * 100) if traditional_water > 0 else 0, 1),
                "trends": {
                    "water_usage": "stable",
                    "frequency": "stable",
                },
            },
            "period": period,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating insights: {str(e)}")
