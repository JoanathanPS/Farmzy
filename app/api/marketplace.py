"""Marketplace - Direct Buy & Sell API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from app.database import get_db
from app.models import ListingDB, OrderDB
from app.marketplace.engine import MarketplaceEngine
from app.marketplace.models import Listing, Order, Buyer, PricingSuggestion
from app.models import SoilHealthDB

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
    db: Session = Depends(get_db),
):
    """
    Create a new crop listing.
    
    If soil_score is not provided, fetches latest from Soilytics.
    """
    try:
        # Get soil score if not provided
        soil_score = request.soil_score
        if not soil_score:
            # Try to get from latest soil health
            device_id = f"ESP_{request.farm_id}"
            latest_health = db.query(SoilHealthDB).filter(
                SoilHealthDB.device_id == device_id
            ).order_by(desc(SoilHealthDB.date)).first()
            
            if latest_health:
                soil_score = latest_health.soil_score
            else:
                soil_score = 70.0  # Default
        
        # Create listing using engine
        listing = engine.create_listing(
            farm_id=request.farm_id,
            crop=request.crop,
            quantity=request.quantity,
            soil_score=soil_score,
        )
        
        # Store in database
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
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating listing: {str(e)}")


@router.get("/listings")
async def get_listings(
    farm_id: Optional[str] = Query(None, description="Filter by farm ID"),
    status: Optional[str] = Query("active", description="Filter by status"),
    limit: int = Query(100, description="Number of listings"),
    db: Session = Depends(get_db),
):
    """
    Get available listings.
    """
    try:
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
    db: Session = Depends(get_db),
):
    """
    Get available buyers for a listing.
    """
    try:
        # Get listing (handle both int and string IDs)
        try:
            listing_id_int = int(listing_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid listing ID format")
        
        listing_db = db.query(ListingDB).filter(ListingDB.id == listing_id_int).first()
        
        if not listing_db:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        # Convert to Listing model
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
        
        # Get buyers
        buyers = engine.get_buyers_for_listing(listing, limit)
        
        return [buyer.dict() for buyer in buyers]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving buyers: {str(e)}")


@router.post("/order")
async def create_order(
    request: CreateOrderRequest,
    db: Session = Depends(get_db),
):
    """
    Create an order from a listing.
    """
    try:
        # Get listing (handle both int and string IDs)
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
        
        # Convert to Listing model
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
        
        # Create order
        order = engine.create_order(listing, request.buyer_id, request.quantity)
        
        # Store in database
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
        
        # Update listing quantity
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
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")


@router.get("/orders")
async def get_orders(
    farm_id: str = Query(..., description="Farm ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Number of orders"),
    db: Session = Depends(get_db),
):
    """
    Get orders for a farm.
    """
    try:
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

