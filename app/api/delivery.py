"""AgroGo - Rural Delivery API endpoints (Supabase-first)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.database import get_db
from app.models import DeliveryDB, RouteDB, OrderDB
from app.agrogo.engine import AgroGoEngine
from app.agrogo.models import Delivery, Route, PickupPoint, DeliveryStatus
from app.core.farm_model import DEFAULT_FARM
from app.supabase_client import supabase

router = APIRouter(prefix="/api/delivery", tags=["delivery"])

# Initialize engine
engine = AgroGoEngine()


class ScheduleDeliveryRequest(BaseModel):
    """Request model for scheduling delivery."""
    order_id: str
    farm_id: str
    farm_location: Optional[dict] = None
    delivery_date: Optional[str] = None


class AggregatePickupsRequest(BaseModel):
    """Request model for aggregating pickups."""
    farm_ids: List[str]
    date: str


class CostEstimateRequest(BaseModel):
    """Request model for cost estimation."""
    distance_km: float
    pickup_count: int


@router.post("/schedule")
async def schedule_delivery(
    request: ScheduleDeliveryRequest,
    db: Optional[Session] = Depends(get_db),
):
    """
    Schedule delivery for an order.
    """
    try:
        farm_location = request.farm_location or {
            "lat": DEFAULT_FARM.location.lat,
            "lng": DEFAULT_FARM.location.lng,
            "name": DEFAULT_FARM.location.name,
        }

        delivery_date = None
        if request.delivery_date:
            delivery_date = datetime.fromisoformat(request.delivery_date.replace("Z", "+00:00"))

        delivery = engine.schedule_delivery(
            order_id=request.order_id,
            farm_id=request.farm_id,
            farm_location=farm_location,
            delivery_date=delivery_date,
        )

        if supabase.is_configured:
            created_del = supabase.create_delivery({
                "order_id": request.order_id,
                "farm_id": request.farm_id,
                "pickup_time": delivery.pickup_time.isoformat() if delivery.pickup_time else None,
                "delivery_distance_km": delivery.delivery_distance_km,
                "estimated_cost": delivery.estimated_cost,
                "delivery_status": delivery.delivery_status.value,
            })
            return created_del

        if not db:
            raise HTTPException(status_code=500, detail="Database not configured")

        db_delivery = DeliveryDB(
            order_id=request.order_id,
            farm_id=request.farm_id,
            pickup_time=delivery.pickup_time,
            delivery_distance_km=delivery.delivery_distance_km,
            estimated_cost=delivery.estimated_cost,
            delivery_status=delivery.delivery_status.value,
        )
        db.add(db_delivery)
        db.commit()
        db.refresh(db_delivery)

        return {
            "id": str(db_delivery.id),
            "order_id": db_delivery.order_id,
            "farm_id": db_delivery.farm_id,
            "pickup_time": db_delivery.pickup_time.isoformat() if db_delivery.pickup_time else None,
            "delivery_distance_km": db_delivery.delivery_distance_km,
            "estimated_cost": db_delivery.estimated_cost,
            "delivery_status": db_delivery.delivery_status,
            "created_at": db_delivery.created_at.isoformat() if db_delivery.created_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        if db:
            db.rollback()
        raise HTTPException(status_code=500, detail=f"Error scheduling delivery: {str(e)}")


@router.get("/routes")
async def get_routes(
    date: str = Query(..., description="Date in ISO format"),
    db: Optional[Session] = Depends(get_db),
):
    """
    Get optimized routes for a date.
    """
    try:
        if supabase.is_configured:
            routes = supabase.get_routes()
            return {
                "routes": [
                    {
                        "route_id": route.get("route_id"),
                        "farms": route.get("farms"),
                        "total_distance": route.get("total_distance_km"),
                        "estimated_cost": route.get("estimated_cost"),
                        "status": route.get("status"),
                    }
                    for route in routes
                ],
            }

        if not db:
            return {"routes": []}

        target_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
        routes = db.query(RouteDB).filter(
            RouteDB.date >= target_date.replace(hour=0, minute=0, second=0),
            RouteDB.date < target_date.replace(hour=23, minute=59, second=59) + timedelta(days=1),
        ).all()

        return {
            "routes": [
                {
                    "route_id": route.route_id,
                    "farms": route.farms,
                    "total_distance": route.total_distance_km,
                    "estimated_cost": route.estimated_cost,
                    "status": route.status,
                }
                for route in routes
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving routes: {str(e)}")


@router.post("/aggregate")
async def aggregate_pickups(
    request: AggregatePickupsRequest,
    db: Optional[Session] = Depends(get_db),
):
    """
    Aggregate multiple farm pickups into optimized routes.
    """
    try:
        pickup_points = []
        if supabase.is_configured:
            orders = supabase.select("orders", {"status": "eq.confirmed"})
            matching = [o for o in orders if o.get("farm_id") in request.farm_ids]
            for order in matching:
                pickup_points.append(PickupPoint(
                    farm_id=order["farm_id"],
                    location={
                        "lat": DEFAULT_FARM.location.lat,
                        "lng": DEFAULT_FARM.location.lng,
                        "name": DEFAULT_FARM.location.name,
                    },
                    order_id=str(order.get("id")),
                    quantity_kg=float(order.get("quantity", 0)),
                ))
        elif db:
            orders = db.query(OrderDB).filter(
                OrderDB.farm_id.in_(request.farm_ids),
                OrderDB.status == "confirmed",
            ).all()
            for order in orders:
                pickup_points.append(PickupPoint(
                    farm_id=order.farm_id,
                    location={
                        "lat": DEFAULT_FARM.location.lat,
                        "lng": DEFAULT_FARM.location.lng,
                        "name": DEFAULT_FARM.location.name,
                    },
                    order_id=str(order.id),
                    quantity_kg=order.quantity,
                ))

        routes = engine.aggregate_pickups(pickup_points)
        target_date = datetime.fromisoformat(request.date.replace("Z", "+00:00"))

        if supabase.is_configured:
            for route in routes:
                supabase.create_route({
                    "route_id": route.route_id,
                    "date": target_date.isoformat(),
                    "farms": [farm.dict() for farm in route.farms],
                    "total_distance_km": route.total_distance_km,
                    "estimated_cost": route.estimated_cost,
                    "status": "planned",
                })
        elif db:
            for route in routes:
                db_route = RouteDB(
                    route_id=route.route_id,
                    date=target_date,
                    farms=[farm.dict() for farm in route.farms],
                    total_distance_km=route.total_distance_km,
                    estimated_cost=route.estimated_cost,
                    status="planned",
                )
                db.add(db_route)
            db.commit()

        return {
            "routes": [
                {
                    "route_id": route.route_id,
                    "farms": [farm.dict() for farm in route.farms],
                    "total_distance": route.total_distance_km,
                    "estimated_cost": route.estimated_cost,
                    "pickup_sequence": route.pickup_sequence,
                }
                for route in routes
            ],
        }

    except Exception as e:
        if db:
            db.rollback()
        raise HTTPException(status_code=500, detail=f"Error aggregating pickups: {str(e)}")


@router.get("/status")
async def get_delivery_status(
    order_id: str = Query(..., description="Order ID"),
    db: Optional[Session] = Depends(get_db),
):
    """
    Get delivery status for an order.
    """
    try:
        if supabase.is_configured:
            dels = supabase.select("deliveries", {"order_id": f"eq.{order_id}", "order": "created_at.desc", "limit": "1"})
            if not dels:
                raise HTTPException(status_code=404, detail="Delivery not found")
            deliv = dels[0]
            return {
                "id": str(deliv.get("id")),
                "order_id": deliv.get("order_id"),
                "farm_id": deliv.get("farm_id"),
                "route_id": deliv.get("route_id"),
                "pickup_time": deliv.get("pickup_time"),
                "delivery_distance_km": deliv.get("delivery_distance_km"),
                "estimated_cost": deliv.get("estimated_cost"),
                "actual_cost": deliv.get("actual_cost"),
                "delivery_status": deliv.get("delivery_status"),
                "created_at": deliv.get("created_at"),
            }

        if not db:
            raise HTTPException(status_code=404, detail="Delivery not found")

        delivery = db.query(DeliveryDB).filter(
            DeliveryDB.order_id == order_id
        ).order_by(desc(DeliveryDB.created_at)).first()

        if not delivery:
            raise HTTPException(status_code=404, detail="Delivery not found")

        return {
            "id": str(delivery.id),
            "order_id": delivery.order_id,
            "farm_id": delivery.farm_id,
            "route_id": delivery.route_id,
            "pickup_time": delivery.pickup_time.isoformat() if delivery.pickup_time else None,
            "delivery_distance_km": delivery.delivery_distance_km,
            "estimated_cost": delivery.estimated_cost,
            "actual_cost": delivery.actual_cost,
            "delivery_status": delivery.delivery_status,
            "created_at": delivery.created_at.isoformat() if delivery.created_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving delivery status: {str(e)}")


@router.post("/cost-estimate")
async def estimate_cost(
    request: CostEstimateRequest,
):
    """
    Estimate delivery cost.
    """
    try:
        estimated_cost = engine.estimate_cost(
            request.distance_km,
            request.pickup_count,
        )
        distance_cost = max(engine.MIN_DISTANCE_KM, request.distance_km) * engine.BASE_COST_PER_KM
        pickup_cost = request.pickup_count * engine.PICKUP_COST

        return {
            "estimated_cost": round(estimated_cost, 2),
            "breakdown": {
                "base_cost": round(distance_cost, 2),
                "distance_cost": round(distance_cost, 2),
                "pickup_cost": round(pickup_cost, 2),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error estimating cost: {str(e)}")
