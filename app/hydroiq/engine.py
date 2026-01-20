"""HydroIQ Core Irrigation Intelligence Engine."""
import math
from typing import Optional, Dict, List
from datetime import datetime
from app.hydroiq.models import (
    IrrigationDecision,
    IrrigationPlan,
    ZoneWaterDistribution,
    IrrigationStrategy,
    WeatherData,
    SoilData,
)
from app.core.farm_model import FarmModel


class HydroIQEngine:
    """
    Core irrigation intelligence engine.
    
    Implements:
    - Hargreaves-based ET₀ calculation
    - Crop coefficient (Kc) lookup
    - Area-based water requirement
    - Soil moisture feedback loop
    - Zone-based distribution
    - Cycle-based strategy
    - Confidence scoring
    """
    
    # Field capacity by soil type (%)
    FIELD_CAPACITY = {
        "sandy": 12,
        "loamy": 20,
        "silty": 25,
        "clay": 30,
    }
    
    # Crop coefficients (Kc)
    CROP_COEFFICIENTS = {
        "paddy": 1.2,
        "wheat": 1.0,
        "maize": 1.15,
        "vegetables": 0.9,
        "tomato": 1.1,
        "cotton": 1.05,
    }
    
    # Irrigation cycle defaults
    DEFAULT_CYCLE_ON_MIN = 30
    DEFAULT_CYCLE_OFF_MIN = 30
    MAX_DURATION_HOURS = 8
    MIN_DURATION_MINUTES = 5
    
    def calculate_et0(self, weather: WeatherData) -> float:
        """
        Calculate reference evapotranspiration (ET₀) using Hargreaves method.
        
        Formula: ET₀ = 0.0023 × (Tavg + 17.8) × √(Tmax − Tmin) × 10
        
        Returns:
            ET₀ in mm/day (clamped to [1.0, 8.0])
        """
        temp_diff = max(0.1, weather.max_temperature - weather.min_temperature)
        avg_temp = weather.average_temperature
        
        et0 = 0.0023 * (avg_temp + 17.8) * math.sqrt(temp_diff) * 10
        
        # Clamp to realistic range
        return max(1.0, min(8.0, et0))
    
    def get_crop_coefficient(self, crop: str) -> float:
        """Get crop coefficient (Kc) for a crop type."""
        return self.CROP_COEFFICIENTS.get(crop.lower(), 1.0)
    
    def calculate_crop_water_requirement(
        self,
        et0: float,
        crop: str,
        area_m2: float,
    ) -> float:
        """
        Calculate crop water requirement.
        
        Formula: ETcrop = ET₀ × Kc
        Water (L) = ETcrop (mm) × Area (m²)
        
        Note: 1 mm of water over 1 m² = 1 liter
        
        Returns:
            Daily water requirement in liters
        """
        kc = self.get_crop_coefficient(crop)
        etcrop_mm = et0 * kc
        
        # Convert mm to liters: 1 mm × 1 m² = 1 liter
        water_liters = etcrop_mm * area_m2
        
        return water_liters
    
    def calculate_effective_rainfall(self, rainfall_mm: float) -> float:
        """
        Calculate effective rainfall (only part is usable).
        
        Formula: EffectiveRain = Rainfall × 0.7
        """
        return rainfall_mm * 0.7
    
    def calculate_net_water_need(
        self,
        crop_water_liters: float,
        effective_rain_mm: float,
        area_m2: float,
    ) -> float:
        """
        Calculate net water need after accounting for rainfall.
        
        Formula: NetWaterNeed = max(ETcrop - EffectiveRain, 0) × Area
        """
        crop_water_mm = crop_water_liters / area_m2 if area_m2 > 0 else 0
        net_need_mm = max(0, crop_water_mm - effective_rain_mm)
        net_water_liters = net_need_mm * area_m2
        
        return net_water_liters
    
    def get_field_capacity(self, soil_type: str) -> float:
        """Get field capacity for soil type."""
        return self.FIELD_CAPACITY.get(soil_type.lower(), 20)
    
    def calculate_trigger_threshold(self, soil_type: str) -> float:
        """
        Calculate soil moisture trigger threshold.
        
        Formula: TriggerThreshold = FieldCapacity × 0.6
        """
        field_capacity = self.get_field_capacity(soil_type)
        return field_capacity * 0.6
    
    def should_irrigate(
        self,
        soil_moisture: float,
        trigger_threshold: float,
        net_water_liters: float,
        forecast_rainfall_mm: float,
    ) -> tuple[bool, List[str]]:
        """
        Determine if irrigation should occur.
        
        Decision logic:
        1. Soil safety check: If moisture >= threshold → DO NOT irrigate
        2. Water stress check: If moisture < threshold AND net need > 0 AND no significant rain → Irrigate
        
        Returns:
            Tuple of (should_irrigate, reasons)
        """
        reasons = []
        
        # Step 1: Soil safety check
        if soil_moisture >= trigger_threshold:
            reasons.append(
                f"Soil moisture ({soil_moisture:.1f}%) above threshold ({trigger_threshold:.1f}%)"
            )
            return False, reasons
        
        # Step 2: Water stress check
        if net_water_liters <= 0:
            reasons.append("No net water requirement (rainfall sufficient)")
            return False, reasons
        
        if forecast_rainfall_mm >= 5:
            reasons.append(
                f"Significant rainfall forecasted ({forecast_rainfall_mm} mm) - postpone irrigation"
            )
            return False, reasons
        
        reasons.append(
            f"Soil moisture ({soil_moisture:.1f}%) below threshold ({trigger_threshold:.1f}%)"
        )
        reasons.append(f"Net water need: {net_water_liters:.0f} liters")
        
        return True, reasons
    
    def calculate_irrigation_duration(
        self,
        net_water_liters: float,
        flow_rate_lph: float,
    ) -> tuple[float, int]:
        """
        Calculate irrigation duration.
        
        Formula: Duration_hours = NetWaterNeed_L / FlowRate_LPH
        Duration_minutes = Duration_hours × 60
        
        Returns:
            Tuple of (duration_hours, duration_minutes)
        """
        if flow_rate_lph <= 0:
            return 0.0, 0
        
        duration_hours = net_water_liters / flow_rate_lph
        duration_minutes = max(
            self.MIN_DURATION_MINUTES,
            min(self.MAX_DURATION_HOURS * 60, int(duration_hours * 60))
        )
        
        # Recalculate hours from clamped minutes
        duration_hours = duration_minutes / 60.0
        
        return duration_hours, duration_minutes
    
    def distribute_zones(
        self,
        net_water_liters: float,
        total_duration_minutes: int,
        farm: FarmModel,
    ) -> List[ZoneWaterDistribution]:
        """
        Distribute water across farm zones.
        
        Formula: ZoneWater_L = NetWaterNeed_L × (ZoneArea_m² / TotalArea_m²)
        """
        zones = []
        total_area = farm.area_m2
        
        for zone in farm.zones:
            zone_ratio = zone.area_m2 / total_area if total_area > 0 else 0
            zone_water = net_water_liters * zone_ratio
            zone_duration = int(total_duration_minutes * zone_ratio)
            
            zones.append(ZoneWaterDistribution(
                zone_id=zone.zone_id,
                water_liters=round(zone_water, 2),
                duration_minutes=zone_duration,
                area_m2=zone.area_m2,
            ))
        
        return zones
    
    def calculate_cycles(
        self,
        duration_minutes: int,
        cycle_on_min: int = None,
        cycle_off_min: int = None,
    ) -> IrrigationStrategy:
        """
        Calculate irrigation cycles.
        
        Formula: TotalCycles = ceil(Duration_minutes / (ON + OFF))
        """
        cycle_on = cycle_on_min or self.DEFAULT_CYCLE_ON_MIN
        cycle_off = cycle_off_min or self.DEFAULT_CYCLE_OFF_MIN
        cycle_total = cycle_on + cycle_off
        
        total_cycles = math.ceil(duration_minutes / cycle_total) if cycle_total > 0 else 1
        
        return IrrigationStrategy(
            cycle_on_min=cycle_on,
            cycle_off_min=cycle_off,
            total_cycles=total_cycles,
        )
    
    def calculate_confidence(
        self,
        soil_data: Optional[SoilData],
        weather: WeatherData,
        soil_score: Optional[float] = None,
    ) -> float:
        """
        Calculate decision confidence score.
        
        Factors:
        - Sensor freshness (if soil_data has timestamp)
        - Weather certainty
        - Data completeness
        - Soil health score
        
        Formula: AdjustedConfidence = BaseConfidence × (0.8 + 0.2 × SoilHealthFactor)
        """
        base_confidence = 0.8
        
        # Check sensor freshness
        if soil_data and soil_data.timestamp:
            age_hours = (datetime.utcnow() - soil_data.timestamp).total_seconds() / 3600
            if age_hours > 24:
                base_confidence *= 0.9
            elif age_hours > 48:
                base_confidence *= 0.7
        
        # Weather certainty (mock data = lower confidence)
        # In real implementation, check weather API reliability
        
        # Soil health factor
        if soil_score is not None:
            soil_health_factor = soil_score / 100.0
            base_confidence = base_confidence * (0.8 + 0.2 * soil_health_factor)
        elif soil_data and soil_data.soil_score:
            soil_health_factor = soil_data.soil_score / 100.0
            base_confidence = base_confidence * (0.8 + 0.2 * soil_health_factor)
        
        # Clamp to [0.3, 1.0]
        return max(0.3, min(1.0, base_confidence))
    
    def compute_irrigation_decision(
        self,
        farm: FarmModel,
        soil_data: SoilData,
        weather: WeatherData,
    ) -> IrrigationDecision:
        """
        Compute complete irrigation decision.
        
        This is the main entry point for irrigation intelligence.
        
        Args:
            farm: Farm model with area, zones, crop, etc.
            soil_data: Current soil conditions
            weather: Weather data for ET₀ calculation
            
        Returns:
            Complete IrrigationDecision with all calculations
        """
        # Step 1: Calculate ET₀
        et0_mm = self.calculate_et0(weather)
        
        # Step 2: Calculate crop water requirement
        crop_water_liters = self.calculate_crop_water_requirement(
            et0_mm, farm.crop, farm.area_m2
        )
        etcrop_mm = (crop_water_liters / farm.area_m2) if farm.area_m2 > 0 else 0
        
        # Step 3: Calculate effective rainfall
        effective_rain_mm = self.calculate_effective_rainfall(weather.rainfall_mm)
        
        # Step 4: Calculate net water need
        net_water_liters = self.calculate_net_water_need(
            crop_water_liters, effective_rain_mm, farm.area_m2
        )
        
        # Step 5: Get trigger threshold
        trigger_threshold = self.calculate_trigger_threshold(farm.soil_type)
        field_capacity = self.get_field_capacity(farm.soil_type)
        
        # Step 6: Decision logic
        should_irrigate, reasons = self.should_irrigate(
            soil_data.moisture,
            trigger_threshold,
            net_water_liters,
            weather.rainfall_mm,
        )
        
        # Step 7: Calculate duration
        duration_hours, duration_minutes = self.calculate_irrigation_duration(
            net_water_liters if should_irrigate else 0,
            farm.flow_rate_lph,
        )
        
        # Step 8: Distribute zones
        zones = []
        if should_irrigate:
            zones = self.distribute_zones(
                net_water_liters, duration_minutes, farm
            )
        
        # Step 9: Calculate cycles
        strategy = self.calculate_cycles(duration_minutes)
        
        # Step 10: Calculate confidence
        confidence = self.calculate_confidence(
            soil_data, weather, soil_data.soil_score
        )
        
        # Build computed values
        computed_values = {
            "et0_mm": round(et0_mm, 2),
            "etcrop_mm": round(etcrop_mm, 2),
            "effective_rain_mm": round(effective_rain_mm, 2),
            "field_capacity_pct": field_capacity,
            "trigger_threshold_pct": round(trigger_threshold, 1),
        }
        
        return IrrigationDecision(
            irrigate=should_irrigate,
            net_water_liters=round(net_water_liters, 2),
            zones=zones,
            strategy=strategy,
            reasons=reasons,
            confidence=round(confidence, 2),
            computed_values=computed_values,
            timestamp=datetime.utcnow(),
        )






