"""Marketplace Intelligence Engine."""
from typing import Dict, Optional
from app.marketplace.models import (
    Listing,
    Order,
    Buyer,
    PricingSuggestion,
    QualityGrade,
    ListingStatus,
)


class MarketplaceEngine:
    """
    Marketplace intelligence engine.
    
    Handles:
    - Quality-based pricing
    - Crop listing management
    - Buyer matching
    - Price suggestions
    """
    
    # Base prices per crop (₹ per kg)
    BASE_PRICES = {
        "paddy": 28.0,
        "wheat": 24.0,
        "maize": 22.0,
        "vegetables": 35.0,
        "tomato": 40.0,
        "cotton": 180.0,  # per kg
    }
    
    # Quality multipliers
    QUALITY_MULTIPLIERS = {
        QualityGrade.PREMIUM: 1.15,  # 15% premium
        QualityGrade.GOOD: 1.0,       # Standard price
        QualityGrade.STANDARD: 0.9,   # 10% discount
    }
    
    # Mock buyers (in production, fetch from database)
    MOCK_BUYERS = [
        {"id": "B001", "name": "Local Market", "location": "Chennai", "rating": 4.2},
        {"id": "B002", "name": "Cooperative Society", "location": "Poonamallee", "rating": 4.5},
        {"id": "B003", "name": "Direct Buyer", "location": "Chennai", "rating": 4.8},
        {"id": "B004", "name": "Wholesale Dealer", "location": "Chennai", "rating": 4.0},
        {"id": "B005", "name": "Export Company", "location": "Chennai", "rating": 4.7},
        {"id": "B006", "name": "Retail Chain", "location": "Chennai", "rating": 4.3},
    ]
    
    def determine_quality_grade(self, soil_score: float) -> QualityGrade:
        """
        Determine quality grade based on soil health score.
        
        - Grade A (Premium): soil_score >= 80
        - Grade B (Good): 60 <= soil_score < 80
        - Grade C (Standard): soil_score < 60
        """
        if soil_score >= 80:
            return QualityGrade.PREMIUM
        elif soil_score >= 60:
            return QualityGrade.GOOD
        else:
            return QualityGrade.STANDARD
    
    def get_base_price(self, crop: str) -> float:
        """Get base market price for crop."""
        return self.BASE_PRICES.get(crop.lower(), 25.0)
    
    def calculate_pricing(
        self,
        crop: str,
        soil_score: float,
        demand_factor: float = 1.0,
    ) -> PricingSuggestion:
        """
        Calculate pricing suggestion based on quality and demand.
        
        Formula: SuggestedPrice = BasePrice × QualityMultiplier × DemandFactor
        
        Args:
            crop: Crop type
            soil_score: Soil health score (0-100)
            demand_factor: Demand multiplier (default 1.0)
            
        Returns:
            PricingSuggestion with all pricing details
        """
        base_price = self.get_base_price(crop)
        quality_grade = self.determine_quality_grade(soil_score)
        quality_multiplier = self.QUALITY_MULTIPLIERS[quality_grade]
        
        suggested_price = base_price * quality_multiplier * demand_factor
        
        # Count available buyers (mock - in production, query database)
        buyers_available = len(self.MOCK_BUYERS)
        
        return PricingSuggestion(
            quality_grade=quality_grade,
            soil_score=soil_score,
            suggested_price=round(suggested_price, 2),
            base_price=base_price,
            price_multiplier=quality_multiplier,
            buyers_available=buyers_available,
        )
    
    def get_buyers_for_listing(
        self,
        listing: Listing,
        limit: int = 10,
    ) -> List[Buyer]:
        """
        Get available buyers for a listing.
        
        In production, this would:
        - Match buyers based on location
        - Filter by crop preferences
        - Sort by rating and price
        
        For now, returns mock buyers with adjusted prices.
        """
        buyers = []
        pricing = self.calculate_pricing(listing.crop, listing.soil_score)
        
        for i, mock_buyer in enumerate(self.MOCK_BUYERS[:limit]):
            # Adjust price slightly for each buyer (simulate negotiation)
            price_variation = 0.95 + (i % 3) * 0.025  # 95%, 97.5%, 100% of suggested
            buyer_price = pricing.suggested_price * price_variation
            
            buyers.append(Buyer(
                id=mock_buyer["id"],
                name=mock_buyer["name"],
                price=round(buyer_price, 2),
                location=mock_buyer["location"],
                rating=mock_buyer.get("rating", 4.0),
            ))
        
        return buyers
    
    def create_listing(
        self,
        farm_id: str,
        crop: str,
        quantity: float,
        soil_score: float,
    ) -> Listing:
        """
        Create a new crop listing.
        
        Args:
            farm_id: Farm identifier
            crop: Crop type
            quantity: Quantity in kg
            soil_score: Soil health score for quality grading
            
        Returns:
            Listing object
        """
        pricing = self.calculate_pricing(crop, soil_score)
        
        return Listing(
            farm_id=farm_id,
            crop=crop,
            quantity=quantity,
            quality_grade=pricing.quality_grade,
            soil_score=soil_score,
            suggested_price=pricing.suggested_price,
            base_price=pricing.base_price,
            status=ListingStatus.ACTIVE,
        )
    
    def create_order(
        self,
        listing: Listing,
        buyer_id: str,
        quantity: float,
    ) -> Order:
        """
        Create an order from a listing.
        
        Args:
            listing: The listing being ordered
            buyer_id: Buyer identifier
            quantity: Quantity to order (must be <= listing quantity)
            
        Returns:
            Order object
        """
        if quantity > listing.quantity:
            raise ValueError(f"Order quantity ({quantity}) exceeds listing quantity ({listing.quantity})")
        
        total_price = listing.suggested_price * quantity
        
        return Order(
            listing_id=listing.id or "",
            buyer_id=buyer_id,
            farm_id=listing.farm_id,
            quantity=quantity,
            price_per_kg=listing.suggested_price,
            total_price=round(total_price, 2),
            status="pending",
        )






