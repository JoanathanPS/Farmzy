"""Intelligence Engines - Core business logic for all modules."""
from typing import Dict, List, Optional
from datetime import datetime
from app.core.farm_model import FarmModel


class SoilEngine:
    """Soil Intelligence Engine."""
    
    @staticmethod
    def analyze_soil(soil_data: Dict) -> Dict:
        """
        Analyze soil data and return structured output.
        Used by: HydroIQ, Finance, Market
        """
        moisture = soil_data.get("moisture", 0)
        ph = soil_data.get("ph", 7.0)
        nitrogen = soil_data.get("nitrogen", 0)
        phosphorus = soil_data.get("phosphorus", 0)
        potassium = soil_data.get("potassium", 0)
        
        # Calculate soil score (0-100)
        score = 100
        if moisture < 20:
            score -= 15
        elif moisture > 60:
            score -= 10
        
        if ph < 6.0 or ph > 7.5:
            score -= 10
        
        if nitrogen < 40:
            score -= 10
        if phosphorus < 20:
            score -= 10
        if potassium < 150:
            score -= 10
        
        # Degradation index (lower is better)
        degradation = 0
        if nitrogen < 30:
            degradation += 15
        if phosphorus < 15:
            degradation += 10
        if ph < 5.5 or ph > 8.0:
            degradation += 10
        
        return {
            "soilScore": max(0, min(100, score)),
            "moisture": moisture,
            "ph": ph,
            "nutrientStatus": {
                "N": _classify_nutrient(nitrogen, [20, 40, 60, 80]),
                "P": _classify_nutrient(phosphorus, [10, 20, 30, 40]),
                "K": _classify_nutrient(potassium, [100, 150, 200, 250])
            },
            "degradationIndex": degradation,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def get_fertilizer_recommendations(soil_output: Dict) -> Dict:
        """Get fertilizer recommendations based on soil analysis."""
        recs = []
        nutrients = soil_output["nutrientStatus"]
        
        if nutrients["N"] in ["very_low", "low"]:
            recs.append({
                "nutrient": "Nitrogen",
                "amount": "Apply 50-75 kg/acre of Urea",
                "cost_per_acre": 1200,
                "urgency": "high" if nutrients["N"] == "very_low" else "medium"
            })
        
        if nutrients["P"] in ["very_low", "low"]:
            recs.append({
                "nutrient": "Phosphorus",
                "amount": "Apply 30-50 kg/acre of DAP",
                "cost_per_acre": 1800,
                "urgency": "high" if nutrients["P"] == "very_low" else "medium"
            })
        
        if nutrients["K"] in ["very_low", "low"]:
            recs.append({
                "nutrient": "Potassium",
                "amount": "Apply 40-60 kg/acre of MOP",
                "cost_per_acre": 1500,
                "urgency": "high" if nutrients["K"] == "very_low" else "medium"
            })
        
        return {
            "recommendations": recs,
            "total_cost_per_acre": sum(r["cost_per_acre"] for r in recs),
            "timestamp": datetime.utcnow().isoformat()
        }


class WaterEngine:
    """Water/Irrigation Intelligence Engine."""
    
    @staticmethod
    def compute_irrigation(
        farm: FarmModel,
        soil_output: Dict,
        weather_data: Dict
    ) -> Dict:
        """
        Compute irrigation decision.
        Uses: Soil moisture, weather, farm config
        Outputs: Water required, zones, savings
        """
        # Constants
        ACRES_TO_M2 = 4046.86
        FIELD_CAPACITY = {"sandy": 12, "loamy": 20, "silty": 25, "clay": 30}
        CROP_COEFFICIENT = {
            "paddy": 1.2, "wheat": 1.0, "maize": 1.15,
            "vegetables": 0.9, "tomato": 1.1, "cotton": 1.05
        }
        
        # ET₀ calculation (Hargreaves)
        temp_diff = max(0.1, abs(
            weather_data.get("max_temp", 32) - weather_data.get("min_temp", 22)
        ))
        avg_temp = weather_data.get("avg_temp", 27)
        et0 = max(1.0, min(8.0, 
            0.0023 * (avg_temp + 17.8) * (temp_diff ** 0.5) * 10
        ))
        
        # ETcrop
        kc = CROP_COEFFICIENT.get(farm.crop, 1.0)
        etcrop = et0 * kc
        
        # Effective rainfall
        rainfall = weather_data.get("rainfall_mm", 0)
        effective_rain = rainfall * 0.7
        
        # Net water need
        net_need_mm = max(0, etcrop - effective_rain)
        net_water_liters = net_need_mm * farm.area_m2
        
        # Soil moisture check
        field_capacity = FIELD_CAPACITY.get(farm.soil_type, 20)
        trigger_threshold = field_capacity * 0.6
        soil_moisture = soil_output.get("moisture", 0)
        
        # Decision logic
        should_irrigate = (
            soil_moisture < trigger_threshold and
            net_water_liters > 0 and
            rainfall < 5
        )
        
        # Duration
        duration_hours = net_water_liters / farm.flow_rate_lph if farm.flow_rate_lph > 0 else 0
        duration_minutes = max(5, min(480, duration_hours * 60))
        
        # Zone distribution
        zones = []
        for zone in farm.zones:
            zone_water = net_water_liters * (zone.area_m2 / farm.area_m2)
            zone_duration = duration_minutes * (zone.area_m2 / farm.area_m2)
            zones.append({
                "zone_id": zone.zone_id,
                "water_liters": round(zone_water, 2),
                "duration_minutes": round(zone_duration)
            })
        
        # Water savings (compared to traditional irrigation)
        traditional_water = farm.area_m2 * 10  # Assume 10mm traditional
        water_saved = max(0, traditional_water - net_water_liters)
        water_saved_percent = (water_saved / traditional_water * 100) if traditional_water > 0 else 0
        
        return {
            "irrigate": should_irrigate,
            "waterLiters": round(net_water_liters, 2),
            "durationHours": round(duration_hours, 2),
            "durationMinutes": round(duration_minutes),
            "zones": zones,
            "waterSavedPercent": round(water_saved_percent, 1),
            "computedValues": {
                "et0_mm": round(et0, 2),
                "etcrop_mm": round(etcrop, 2),
                "effectiveRain_mm": round(effective_rain, 2),
                "fieldCapacity_pct": field_capacity,
                "triggerThreshold_pct": round(trigger_threshold, 1)
            },
            "reasons": _generate_reasons(soil_moisture, trigger_threshold, et0, rainfall),
            "confidence": 0.78,
            "timestamp": datetime.utcnow().isoformat()
        }


class WeatherEngine:
    """Weather Intelligence Engine."""
    
    @staticmethod
    def get_weather_advice(location: Dict, weather_data: Dict) -> Dict:
        """
        Get weather-based advice.
        Used by: HydroIQ, Finance
        """
        rainfall = weather_data.get("rainfall_mm", 0)
        temp = weather_data.get("avg_temp", 27)
        
        advice = "Normal conditions"
        if rainfall >= 5:
            advice = "Significant rainfall expected — delay irrigation"
        elif temp > 35:
            advice = "High temperature — increase irrigation frequency"
        elif temp < 20:
            advice = "Low temperature — reduce irrigation"
        
        return {
            "temp": temp,
            "rainForecast": rainfall,
            "advice": advice,
            "irrigationAllowed": rainfall < 5,
            "timestamp": datetime.utcnow().isoformat()
        }


class FinanceEngine:
    """Finance Intelligence Engine."""
    
    @staticmethod
    def calculate_profit(
        farm: FarmModel,
        water_output: Dict,
        soil_output: Dict,
        fertilizer_recs: Dict
    ) -> Dict:
        """
        Calculate farm profitability.
        Uses: Water usage, fertilizer costs, market prices
        """
        # Income (based on crop and area)
        crop_prices = {
            "paddy": 1800,  # Rs per quintal
            "wheat": 2100,
            "maize": 1500,
            "vegetables": 2500,
            "tomato": 3000,
            "cotton": 6000
        }
        
        # Estimated yield (quintals per acre)
        yield_per_acre = {
            "paddy": 25,
            "wheat": 20,
            "maize": 30,
            "vegetables": 15,
            "tomato": 20,
            "cotton": 8
        }
        
        price_per_quintal = crop_prices.get(farm.crop, 2000)
        yield_qty = yield_per_acre.get(farm.crop, 20) * farm.area_acres
        income = price_per_quintal * yield_qty
        
        # Expenses
        water_cost_per_liter = 0.45  # Rs per liter
        water_used = water_output.get("waterLiters", 0)
        water_cost = water_used * water_cost_per_liter
        
        fertilizer_cost = fertilizer_recs.get("total_cost_per_acre", 0) * farm.area_acres
        
        labor_cost = 19000 * farm.area_acres  # Rs per acre
        other_costs = 10000 * farm.area_acres
        
        total_expenses = water_cost + fertilizer_cost + labor_cost + other_costs
        
        # Water savings
        water_saved = water_output.get("waterSavedPercent", 0) / 100 * water_cost
        
        # Net profit
        net_profit = income - total_expenses + water_saved
        
        return {
            "income": round(income, 2),
            "expenses": {
                "water": round(water_cost, 2),
                "fertilizer": round(fertilizer_cost, 2),
                "labor": round(labor_cost, 2),
                "other": round(other_costs, 2),
                "total": round(total_expenses, 2)
            },
            "waterSavings": round(water_saved, 2),
            "netProfit": round(net_profit, 2),
            "profitPerAcre": round(net_profit / farm.area_acres, 2),
            "timestamp": datetime.utcnow().isoformat()
        }


class MarketEngine:
    """Marketplace Intelligence Engine."""
    
    @staticmethod
    def get_market_insights(
        farm: FarmModel,
        soil_output: Dict
    ) -> Dict:
        """
        Get market insights and pricing.
        Uses: Crop quality (from soil), demand
        """
        # Quality grade based on soil score
        soil_score = soil_output.get("soilScore", 70)
        if soil_score >= 80:
            quality = "Premium"
            price_multiplier = 1.15
        elif soil_score >= 60:
            quality = "Good"
            price_multiplier = 1.0
        else:
            quality = "Standard"
            price_multiplier = 0.9
        
        # Base prices
        base_prices = {
            "paddy": 1800,
            "wheat": 2100,
            "maize": 1500,
            "vegetables": 2500,
            "tomato": 3000,
            "cotton": 6000
        }
        
        base_price = base_prices.get(farm.crop, 2000)
        suggested_price = base_price * price_multiplier
        
        return {
            "qualityGrade": quality,
            "soilScore": soil_score,
            "suggestedPrice": round(suggested_price, 2),
            "basePrice": base_price,
            "priceMultiplier": price_multiplier,
            "buyers": [
                {"name": "Local Market", "price": round(suggested_price * 0.95, 2)},
                {"name": "Cooperative", "price": round(suggested_price * 0.98, 2)},
                {"name": "Direct Buyer", "price": round(suggested_price, 2)}
            ],
            "timestamp": datetime.utcnow().isoformat()
        }


# Helper functions
def _classify_nutrient(value: float, thresholds: List[float]) -> str:
    """Classify nutrient level."""
    if value < thresholds[0]:
        return "very_low"
    elif value < thresholds[1]:
        return "low"
    elif value < thresholds[2]:
        return "medium"
    elif value < thresholds[3]:
        return "high"
    else:
        return "excess"


def _generate_reasons(
    soil_moisture: float,
    threshold: float,
    et0: float,
    rainfall: float
) -> List[str]:
    """Generate decision reasons."""
    reasons = []
    if soil_moisture < threshold:
        reasons.append(f"Soil moisture ({soil_moisture:.1f}%) below threshold ({threshold:.1f}%)")
    else:
        reasons.append(f"Soil moisture ({soil_moisture:.1f}%) above threshold ({threshold:.1f}%)")
    
    if et0 > 5:
        reasons.append(f"High evapotranspiration ({et0:.2f} mm/day)")
    
    if rainfall < 5:
        reasons.append(f"Low forecast rainfall ({rainfall} mm)")
    else:
        reasons.append(f"Significant rainfall forecasted ({rainfall} mm)")
    
    return reasons
