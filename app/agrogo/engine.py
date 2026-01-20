"""AgroGo Route Optimization and Delivery Engine."""
import math
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.agrogo.models import Delivery, Route, PickupPoint, DeliveryStatus
from app.core.farm_model import FarmModel, DEFAULT_FARM


class AgroGoEngine:
    """
    AgroGo delivery intelligence engine.
    
    Handles:
    - Route optimization
    - Local aggregation
    - Cost estimation
    - Delivery scheduling
    """
    
    # Cost parameters
    BASE_COST_PER_KM = 50.0  # ₹ per km
    PICKUP_COST = 200.0  # ₹ per pickup point
    MIN_DISTANCE_KM = 5.0  # Minimum distance for cost calculation
    
    # Aggregation parameters
    MAX_ROUTE_DISTANCE_KM = 50.0  # Maximum distance for single route
    NEARBY_THRESHOLD_KM = 10.0  # Farms within this distance can be aggregated
    
    def haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """
        Calculate distance between two points using Haversine formula.
        
        Returns:
            Distance in kilometers
        """
        # Earth radius in km
        R = 6371.0
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))
        
        distance = R * c
        
        return distance
    
    def find_nearby_farms(
        self,
        farms: List[PickupPoint],
        center_lat: float,
        center_lng: float,
        threshold_km: float = None,
    ) -> List[PickupPoint]:
        """
        Find farms within threshold distance of a center point.
        
        Args:
            farms: List of pickup points
            center_lat: Center latitude
            center_lng: Center longitude
            threshold_km: Distance threshold (default: NEARBY_THRESHOLD_KM)
            
        Returns:
            List of nearby farms
        """
        threshold = threshold_km or self.NEARBY_THRESHOLD_KM
        nearby = []
        
        for farm in farms:
            loc = farm.location
            distance = self.haversine_distance(
                center_lat, center_lng,
                loc.get("lat", 0), loc.get("lng", 0)
            )
            
            if distance <= threshold:
                nearby.append(farm)
        
        return nearby
    
    def optimize_route_sequence(
        self,
        farms: List[PickupPoint],
        start_lat: float,
        start_lng: float,
    ) -> tuple[List[str], float]:
        """
        Optimize pickup sequence using nearest neighbor heuristic.
        
        Args:
            farms: List of pickup points
            start_lat: Starting latitude
            start_lng: Starting longitude
            
        Returns:
            Tuple of (ordered farm_ids, total_distance_km)
        """
        if not farms:
            return [], 0.0
        
        # Start from first farm or provided start point
        remaining = farms.copy()
        sequence = []
        total_distance = 0.0
        
        current_lat = start_lat
        current_lng = start_lng
        
        while remaining:
            # Find nearest farm
            nearest = None
            nearest_distance = float('inf')
            nearest_idx = -1
            
            for idx, farm in enumerate(remaining):
                loc = farm.location
                distance = self.haversine_distance(
                    current_lat, current_lng,
                    loc.get("lat", 0), loc.get("lng", 0)
                )
                
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest = farm
                    nearest_idx = idx
            
            if nearest:
                sequence.append(nearest.farm_id)
                total_distance += nearest_distance
                
                # Update current position
                loc = nearest.location
                current_lat = loc.get("lat", 0)
                current_lng = loc.get("lng", 0)
                
                # Remove from remaining
                remaining.pop(nearest_idx)
        
        return sequence, total_distance
    
    def aggregate_pickups(
        self,
        farms: List[PickupPoint],
    ) -> List[Route]:
        """
        Aggregate multiple farms into optimized routes.
        
        Groups nearby farms and creates routes for each group.
        
        Args:
            farms: List of pickup points to aggregate
            
        Returns:
            List of optimized routes
        """
        if not farms:
            return []
        
        routes = []
        processed = set()
        
        for farm in farms:
            if farm.farm_id in processed:
                continue
            
            # Find nearby farms
            loc = farm.location
            nearby = self.find_nearby_farms(
                farms,
                loc.get("lat", 0),
                loc.get("lng", 0),
            )
            
            # Filter out already processed
            nearby = [f for f in nearby if f.farm_id not in processed]
            
            if not nearby:
                continue
            
            # Optimize sequence
            sequence, total_distance = self.optimize_route_sequence(
                nearby,
                loc.get("lat", 0),
                loc.get("lng", 0),
            )
            
            # Calculate cost
            estimated_cost = self.estimate_cost(total_distance, len(nearby))
            
            # Create route
            route_id = f"ROUTE_{datetime.utcnow().strftime('%Y%m%d')}_{len(routes) + 1}"
            route = Route(
                route_id=route_id,
                date=datetime.utcnow(),
                farms=nearby,
                total_distance_km=round(total_distance, 2),
                estimated_cost=round(estimated_cost, 2),
                pickup_sequence=sequence,
            )
            
            routes.append(route)
            
            # Mark as processed
            for f in nearby:
                processed.add(f.farm_id)
        
        return routes
    
    def estimate_cost(
        self,
        distance_km: float,
        pickup_count: int,
    ) -> float:
        """
        Estimate delivery cost.
        
        Formula: Cost = (Distance × BaseCostPerKm) + (PickupCount × PickupCost)
        
        Args:
            distance_km: Total distance in kilometers
            pickup_count: Number of pickup points
            
        Returns:
            Estimated cost in ₹
        """
        distance_cost = max(self.MIN_DISTANCE_KM, distance_km) * self.BASE_COST_PER_KM
        pickup_cost = pickup_count * self.PICKUP_COST
        
        total_cost = distance_cost + pickup_cost
        
        return total_cost
    
    def schedule_delivery(
        self,
        order_id: str,
        farm_id: str,
        farm_location: dict,
        delivery_date: Optional[datetime] = None,
    ) -> Delivery:
        """
        Schedule a delivery for an order.
        
        Args:
            order_id: Order identifier
            farm_id: Farm identifier
            farm_location: Farm location {'lat': float, 'lng': float, 'name': str}
            delivery_date: Preferred delivery date (default: tomorrow)
            
        Returns:
            Delivery object
        """
        if not delivery_date:
            # Default to tomorrow 6:30 AM
            tomorrow = datetime.utcnow() + timedelta(days=1)
            delivery_date = tomorrow.replace(hour=6, minute=30, second=0, microsecond=0)
        
        # Calculate distance (simplified - in production, use actual delivery address)
        # For now, estimate based on typical rural delivery distance
        estimated_distance = 18.0  # km (mock value)
        
        # Estimate cost
        estimated_cost = self.estimate_cost(estimated_distance, 1)
        
        return Delivery(
            order_id=order_id,
            farm_id=farm_id,
            pickup_time=delivery_date,
            delivery_distance_km=estimated_distance,
            estimated_cost=estimated_cost,
            delivery_status=DeliveryStatus.SCHEDULED,
        )






