"""Marketplace - Direct Buy & Sell API endpoints (Supabase-first)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from app.database import get_db
from app.models import ListingDB, OrderDB, SoilHealthDB
from app.marketplace.engine import MarketplaceEngine
from app.marketplace.models import Listing, Order, Buyer, PricingSuggestion
from app.supabase_client import supabase

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])

# Initialize engine
engine = MarketplaceEngine()


class CreateListingRequest(BaseModel):
    """Request model for creating a listing."""
    farm_id: str
    crop: str
    quantity: float
    soil_score: Optional[float] = None


class CreateOrderRequest(BaseModel):
    """Request model for creating an order."""
    listing_id: str
    buyer_id: str
    quantity: float


@router.post("/list")
async def create_listing(
    request: CreateListingRequest,
    db: Optional[Session] = Depends(get_db),
):
    """
    Create a new crop listing.
    Uses Supabase directly if configured.
    """
    try:
        soil_score = request.soil_score
        
        if supabase.is_configured:
            if not soil_score:
                sh = supabase.get_latest_soil_health(f"ESP_{request.farm_id}")
                soil_score = float(sh["soil_score"]) if sh and "soil_score" in sh else 70.0
            
            listing = engine.create_listing(
                farm_id=request.farm_id,
                crop=request.crop,
                quantity=request.quantity,
                soil_score=soil_score,
            )
            
            created = supabase.create_listing({
                "farm_id": listing.farm_id,
                "crop": listing.crop,
                "quantity": listing.quantity,
                "quality_grade": listing.quality_grade.value,
                "soil_score": listing.soil_score,
                "suggested_price": listing.suggested_price,
                "base_price": listing.base_price,
                "status": listing.status.value,
            })
            
            if created:
                return {
                    "id": str(created.get("id")),
                    "farm_id": created.get("farm_id"),
                    "crop": created.get("crop"),
                    "quantity": created.get("quantity"),
                    "quality_grade": created.get("quality_grade"),
                    "suggested_price": created.get("suggested_price"),
                    "base_price": created.get("base_price"),
                    "soil_score": created.get("soil_score"),
                    "status": created.get("status"),
                    "created_at": created.get("created_at"),
                }
            raise HTTPException(status_code=500, detail="Failed to save listing to Supabase")

        if not db:
            raise HTTPException(status_code=500, detail="Database not configured")

        if not soil_score:
            device_id = f"ESP_{request.farm_id}"
            latest_health = db.query(SoilHealthDB).filter(
                SoilHealthDB.device_id == device_id
            ).order_by(desc(SoilHealthDB.date)).first()
            soil_score = latest_health.soil_score if latest_health else 70.0

        listing = engine.create_listing(
            farm_id=request.farm_id,
            crop=request.crop,
            quantity=request.quantity,
            soil_score=soil_score,
        )

        db_listing = ListingDB(
            farm_id=listing.farm_id,
            crop=listing.crop,
            quantity=listing.quantity,
            quality_grade=listing.quality_grade.value,
            soil_score=listing.soil_score,
            suggested_price=listing.suggested_price,
            base_price=listing.base_price,
            status=listing.status.value,
        )
        db.add(db_listing)
        db.commit()
        db.refresh(db_listing)

        return {
            "id": str(db_listing.id),
            "farm_id": db_listing.farm_id,
            "crop": db_listing.crop,
            "quantity": db_listing.quantity,
            "quality_grade": db_listing.quality_grade,
            "suggested_price": db_listing.suggested_price,
            "base_price": db_listing.base_price,
            "soil_score": db_listing.soil_score,
            "status": db_listing.status,
            "created_at": db_listing.created_at.isoformat() if db_listing.created_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        if db:
            db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating listing: {str(e)}")


@router.get("/listings")
async def get_listings(
    farm_id: Optional[str] = Query(None, description="Filter by farm ID"),
    status: Optional[str] = Query("active", description="Filter by status"),
    limit: int = Query(100, description="Number of listings"),
    db: Optional[Session] = Depends(get_db),
):
    """
    Get available listings.
    """
    try:
        if supabase.is_configured:
            items = supabase.get_listings(farm_id=farm_id, status=status, limit=limit)
            return [
                {
                    "id": str(item.get("id")),
                    "farm_id": item.get("farm_id"),
                    "crop": item.get("crop"),
                    "quantity": item.get("quantity"),
                    "quality_grade": item.get("quality_grade"),
                    "suggested_price": item.get("suggested_price"),
                    "base_price": item.get("base_price"),
                    "soil_score": item.get("soil_score"),
                    "status": item.get("status"),
                    "created_at": item.get("created_at"),
                }
                for item in items
            ]

        if not db:
            return []

        query = db.query(ListingDB)
        if farm_id:
            query = query.filter(ListingDB.farm_id == farm_id)
        if status:
            query = query.filter(ListingDB.status == status)

        listings = query.order_by(desc(ListingDB.created_at)).limit(limit).all()
        return [
            {
                "id": str(listing.id),
                "farm_id": listing.farm_id,
                "crop": listing.crop,
                "quantity": listing.quantity,
                "quality_grade": listing.quality_grade,
                "suggested_price": listing.suggested_price,
                "base_price": listing.base_price,
                "soil_score": listing.soil_score,
                "status": listing.status,
                "created_at": listing.created_at.isoformat() if listing.created_at else None,
            }
            for listing in listings
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving listings: {str(e)}")


@router.get("/pricing")
async def get_pricing(
    crop: str = Query(..., description="Crop type"),
    soil_score: float = Query(..., description="Soil health score (0-100)"),
):
    """
    Get price suggestion based on crop and soil score.
    """
    try:
        pricing = engine.calculate_pricing(crop, soil_score)
        return {
            "qualityGrade": pricing.quality_grade.value,
            "suggestedPrice": pricing.suggested_price,
            "basePrice": pricing.base_price,
            "priceMultiplier": pricing.price_multiplier,
            "buyersAvailable": pricing.buyers_available,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating pricing: {str(e)}")


@router.get("/buyers")
async def get_buyers(
    listing_id: str = Query(..., description="Listing ID"),
    limit: int = Query(10, description="Number of buyers"),
    db: Optional[Session] = Depends(get_db),
):
    """
    Get available buyers for a listing.
    """
    try:
        listing_data = None
        if supabase.is_configured:
            rows = supabase.select("listings", {"id": f"eq.{listing_id}"})
            if rows:
                listing_data = rows[0]
        elif db:
            try:
                listing_id_int = int(listing_id)
                db_item = db.query(ListingDB).filter(ListingDB.id == listing_id_int).first()
                if db_item:
                    listing_data = {
                        "id": str(db_item.id),
                        "farm_id": db_item.farm_id,
                        "crop": db_item.crop,
                        "quantity": db_item.quantity,
                        "quality_grade": db_item.quality_grade,
                        "soil_score": db_item.soil_score,
                        "suggested_price": db_item.suggested_price,
                        "base_price": db_item.base_price,
                        "status": db_item.status,
                    }
            except ValueError:
                pass

        if not listing_data:
            raise HTTPException(status_code=404, detail="Listing not found")

        listing = Listing(
            id=str(listing_data["id"]),
            farm_id=listing_data["farm_id"],
            crop=listing_data["crop"],
            quantity=float(listing_data["quantity"]),
            quality_grade=listing_data["quality_grade"],
            soil_score=float(listing_data["soil_score"]),
            suggested_price=float(listing_data["suggested_price"]),
            base_price=float(listing_data["base_price"]),
            status=listing_data["status"],
        )

        buyers = engine.get_buyers_for_listing(listing, limit)
        return [buyer.dict() for buyer in buyers]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving buyers: {str(e)}")


@router.post("/order")
async def create_order(
    request: CreateOrderRequest,
    db: Optional[Session] = Depends(get_db),
):
    """
    Create an order from a listing.
    """
    try:
        if supabase.is_configured:
            rows = supabase.select("listings", {"id": f"eq.{request.listing_id}"})
            if not rows:
                raise HTTPException(status_code=404, detail="Listing not found")
            
            l_row = rows[0]
            if l_row.get("status") != "active":
                raise HTTPException(status_code=400, detail="Listing is not active")

            current_qty = float(l_row.get("quantity", 0))
            if request.quantity > current_qty:
                raise HTTPException(
                    status_code=400,
                    detail=f"Order quantity ({request.quantity}) exceeds available quantity ({current_qty})"
                )

            listing = Listing(
                id=str(l_row["id"]),
                farm_id=l_row["farm_id"],
                crop=l_row["crop"],
                quantity=current_qty,
                quality_grade=l_row["quality_grade"],
                soil_score=float(l_row["soil_score"]),
                suggested_price=float(l_row["suggested_price"]),
                base_price=float(l_row["base_price"]),
                status=l_row["status"],
            )

            order = engine.create_order(listing, request.buyer_id, request.quantity)
            
            created_order = supabase.create_order({
                "listing_id": str(request.listing_id),
                "buyer_id": request.buyer_id,
                "farm_id": listing.farm_id,
                "quantity": order.quantity,
                "price_per_kg": order.price_per_kg,
                "total_price": order.total_price,
                "status": order.status,
            })

            new_qty = current_qty - request.quantity
            supabase.update(
                "listings",
                {"quantity": max(0.0, new_qty), "status": "sold" if new_qty <= 0 else "active"},
                {"id": f"eq.{request.listing_id}"}
            )

            return created_order

        if not db:
            raise HTTPException(status_code=500, detail="Database not configured")

        try:
            listing_id_int = int(request.listing_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid listing ID format")

        listing_db = db.query(ListingDB).filter(ListingDB.id == listing_id_int).first()
        if not listing_db:
            raise HTTPException(status_code=404, detail="Listing not found")

        if listing_db.status != "active":
            raise HTTPException(status_code=400, detail="Listing is not active")

        if request.quantity > listing_db.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Order quantity ({request.quantity}) exceeds available quantity ({listing_db.quantity})"
            )

        listing = Listing(
            id=str(listing_db.id),
            farm_id=listing_db.farm_id,
            crop=listing_db.crop,
            quantity=listing_db.quantity,
            quality_grade=listing_db.quality_grade,
            soil_score=listing_db.soil_score,
            suggested_price=listing_db.suggested_price,
            base_price=listing_db.base_price,
            status=listing_db.status,
        )

        order = engine.create_order(listing, request.buyer_id, request.quantity)

        db_order = OrderDB(
            listing_id=request.listing_id,
            buyer_id=request.buyer_id,
            farm_id=listing.farm_id,
            quantity=order.quantity,
            price_per_kg=order.price_per_kg,
            total_price=order.total_price,
            status=order.status,
        )
        db.add(db_order)

        listing_db.quantity -= request.quantity
        if listing_db.quantity <= 0:
            listing_db.status = "sold"

        db.commit()
        db.refresh(db_order)

        return {
            "id": str(db_order.id),
            "listing_id": db_order.listing_id,
            "buyer_id": db_order.buyer_id,
            "farm_id": db_order.farm_id,
            "quantity": db_order.quantity,
            "price_per_kg": db_order.price_per_kg,
            "total_price": db_order.total_price,
            "status": db_order.status,
            "created_at": db_order.created_at.isoformat() if db_order.created_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        if db:
            db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")


@router.get("/orders")
async def get_orders(
    farm_id: str = Query(..., description="Farm ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Number of orders"),
    db: Optional[Session] = Depends(get_db),
):
    """
    Get orders for a farm.
    """
    try:
        if supabase.is_configured:
            orders = supabase.get_orders(farm_id=farm_id, limit=limit)
            return orders

        if not db:
            return []

        query = db.query(OrderDB).filter(OrderDB.farm_id == farm_id)
        if status:
            query = query.filter(OrderDB.status == status)

        orders = query.order_by(desc(OrderDB.created_at)).limit(limit).all()
        return [
            {
                "id": str(order.id),
                "listing_id": order.listing_id,
                "buyer_id": order.buyer_id,
                "farm_id": order.farm_id,
                "quantity": order.quantity,
                "price_per_kg": order.price_per_kg,
                "total_price": order.total_price,
                "status": order.status,
                "created_at": order.created_at.isoformat() if order.created_at else None,
            }
            for order in orders
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving orders: {str(e)}")
