"""HydroIQ - Smart Irrigation Intelligence API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.database import get_db
from app.models import IrrigationPlanDB, IrrigationExecutionDB
from app.hydroiq.engine import HydroIQEngine
from app.hydroiq.models import IrrigationDecision, SoilData, WeatherData
from app.hydroiq.weather_service import weather_service
from app.core.farm_model import FarmModel, DEFAULT_FARM
from app.models import SoilHealthDB

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
    db: Session = Depends(get_db),
):
    """
    Compute irrigation decision for a farm.
    
    Uses HydroIQ engine to calculate:
    - ET₀ (Hargreaves method)
    - Crop water requirement
    - Net water need (after rainfall)
    - Soil moisture feedback
    - Zone distribution
    - Cycle strategy
    """
    try:
        # Get farm model (in production, fetch from DB)
        # For now, use default farm
        farm = DEFAULT_FARM
        if request.farm_id != DEFAULT_FARM.farm_id:
            # In production, fetch from database
            farm = DEFAULT_FARM  # Fallback to default
        
        # Get soil data
        soil_data = None
        if request.soil_data:
            soil_data = SoilData(**request.soil_data)
        else:
            # Try to get latest soil health from Soilytics
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
                # Use default if can't fetch
                soil_data = SoilData(moisture=38.0, soil_score=70.0)
        
        if not soil_data:
            soil_data = SoilData(moisture=38.0, soil_score=70.0)
        
        # Get weather data
        weather = None
        if request.weather_data:
            weather = WeatherData(**request.weather_data)
        else:
            # Fetch from weather service
            weather = await weather_service.get_weather(
                farm.location.lat,
                farm.location.lng,
            )
        
        # Compute irrigation decision
        decision = engine.compute_irrigation_decision(farm, soil_data, weather)
        
        # Store plan in database
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
        
        return {
            "success": True,
            "plan_id": db_plan.id,
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
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error computing irrigation: {str(e)}")


@router.post("/execute")
async def execute_irrigation(
    request: IrrigationExecuteRequest,
    db: Session = Depends(get_db),
):
    """
    Mark an irrigation plan as executed and log execution.
    """
    try:
        # Get plan
        plan = db.query(IrrigationPlanDB).filter(
            IrrigationPlanDB.id == request.plan_id
        ).first()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Irrigation plan not found")
        
        # Create execution record
        execution = IrrigationExecutionDB(
            plan_id=plan.id,
            farm_id=plan.farm_id,
            executed_zones=request.zones,
            execution_start=datetime.utcnow(),
            status="executing",
        )
        db.add(execution)
        
        # Update plan status
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
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error logging execution: {str(e)}")


@router.get("/history")
async def get_irrigation_history(
    farm_id: str = Query(..., description="Farm ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(50, description="Number of records"),
    db: Session = Depends(get_db),
):
    """
    Retrieve irrigation history for a farm.
    """
    try:
        query = db.query(IrrigationPlanDB).filter(
            IrrigationPlanDB.farm_id == farm_id
        )
        
        if start_date:
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.filter(IrrigationPlanDB.created_at >= start)
        
        if end_date:
            end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            query = query.filter(IrrigationPlanDB.created_at <= end)
        
        plans = query.order_by(desc(IrrigationPlanDB.created_at)).limit(limit).all()
        
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
    db: Session = Depends(get_db),
):
    """
    Provide analytics and insights for irrigation.
    """
    try:
        # Calculate date range
        now = datetime.utcnow()
        if period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        elif period == "year":
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)
        
        # Get plans in period
        plans = db.query(IrrigationPlanDB).filter(
            IrrigationPlanDB.farm_id == farm_id,
            IrrigationPlanDB.created_at >= start_date,
            IrrigationPlanDB.irrigate == "true",
        ).all()
        
        # Get executions
        executions = db.query(IrrigationExecutionDB).filter(
            IrrigationExecutionDB.farm_id == farm_id,
            IrrigationExecutionDB.execution_start >= start_date,
        ).all()
        
        # Calculate metrics
        total_water = sum(plan.net_water_liters for plan in plans)
        total_sessions = len(executions)
        avg_water = total_water / total_sessions if total_sessions > 0 else 0
        
        # Estimate water savings (compared to traditional 10mm irrigation)
        # This is a simplified calculation
        farm = DEFAULT_FARM  # In production, fetch from DB
        traditional_water = farm.area_m2 * 10 * total_sessions  # 10mm per session
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
                    "water_usage": "stable",  # Would calculate from historical data
                    "frequency": "stable",
                },
            },
            "period": period,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating insights: {str(e)}")
