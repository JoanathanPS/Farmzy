"""Soilytics Core Intelligence Engine."""
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import numpy as np
from app.soilytics.models import (
    SoilReading,
    SoilHealth,
    SoilRecommendation,
    NutrientStatus,
    PHStatus,
    MoistureStatus,
    NutrientAnalysis,
)


class SoilIntelligenceEngine:
    """
    Core soil intelligence engine that processes raw sensor data
    and generates actionable insights.
    """
    
    # Nutrient thresholds (mg/kg)
    NITROGEN_THRESHOLDS = {
        "very_low": (0, 20),
        "low": (20, 40),
        "medium": (40, 60),
        "high": (60, 80),
        "excess": (80, float('inf')),
    }
    
    PHOSPHORUS_THRESHOLDS = {
        "very_low": (0, 10),
        "low": (10, 20),
        "medium": (20, 30),
        "high": (30, 40),
        "excess": (40, float('inf')),
    }
    
    POTASSIUM_THRESHOLDS = {
        "very_low": (0, 100),
        "low": (100, 150),
        "medium": (150, 200),
        "high": (200, 250),
        "excess": (250, float('inf')),
    }
    
    # Moisture thresholds (%)
    MOISTURE_THRESHOLDS = {
        "critical": (0, 20),
        "low": (20, 35),
        "moderate": (35, 50),
        "adequate": (50, 70),
        "excess": (70, 100),
    }
    
    # SDI weights
    SDI_WEIGHTS = {
        "nitrogen": 0.35,
        "phosphorus": 0.25,
        "potassium": 0.20,
        "ph": 0.20,
    }
    
    def classify_nitrogen(self, value: float) -> NutrientStatus:
        """Classify nitrogen level."""
        if value < 20:
            return NutrientStatus.VERY_LOW
        elif value < 40:
            return NutrientStatus.LOW
        elif value < 60:
            return NutrientStatus.MEDIUM
        elif value < 80:
            return NutrientStatus.HIGH
        else:
            return NutrientStatus.EXCESS
    
    def classify_phosphorus(self, value: float) -> NutrientStatus:
        """Classify phosphorus level."""
        if value < 10:
            return NutrientStatus.VERY_LOW
        elif value < 20:
            return NutrientStatus.LOW
        elif value < 30:
            return NutrientStatus.MEDIUM
        elif value < 40:
            return NutrientStatus.HIGH
        else:
            return NutrientStatus.EXCESS
    
    def classify_potassium(self, value: float) -> NutrientStatus:
        """Classify potassium level."""
        if value < 100:
            return NutrientStatus.VERY_LOW
        elif value < 150:
            return NutrientStatus.LOW
        elif value < 200:
            return NutrientStatus.MEDIUM
        elif value < 250:
            return NutrientStatus.HIGH
        else:
            return NutrientStatus.EXCESS
    
    def classify_ph(self, ph_value: float) -> PHStatus:
        """Classify pH status."""
        if ph_value < 5.5:
            return PHStatus.ACIDIC
        elif 5.5 <= ph_value <= 7.5:
            return PHStatus.OPTIMAL
        else:
            return PHStatus.ALKALINE
    
    def classify_moisture(self, moisture: float) -> MoistureStatus:
        """Classify moisture status."""
        if moisture < 20:
            return MoistureStatus.CRITICAL
        elif moisture < 35:
            return MoistureStatus.LOW
        elif moisture < 50:
            return MoistureStatus.MODERATE
        elif moisture < 70:
            return MoistureStatus.ADEQUATE
        else:
            return MoistureStatus.EXCESS
    
    def calculate_nutrient_penalty(self, status: NutrientStatus) -> float:
        """Calculate penalty points for nutrient deficiency/excess."""
        penalties = {
            NutrientStatus.VERY_LOW: 30.0,
            NutrientStatus.LOW: 15.0,
            NutrientStatus.MEDIUM: 5.0,
            NutrientStatus.HIGH: 10.0,
            NutrientStatus.EXCESS: 25.0,
        }
        return penalties.get(status, 0.0)
    
    def calculate_ph_penalty(self, ph_status: PHStatus) -> float:
        """Calculate penalty for pH imbalance."""
        penalties = {
            PHStatus.ACIDIC: 20.0,
            PHStatus.OPTIMAL: 0.0,
            PHStatus.ALKALINE: 20.0,
        }
        return penalties.get(ph_status, 0.0)
    
    def calculate_moisture_penalty(self, status: MoistureStatus) -> float:
        """Calculate penalty for moisture stress."""
        penalties = {
            MoistureStatus.CRITICAL: 25.0,
            MoistureStatus.LOW: 15.0,
            MoistureStatus.MODERATE: 5.0,
            MoistureStatus.ADEQUATE: 0.0,
            MoistureStatus.EXCESS: 10.0,
        }
        return penalties.get(status, 0.0)
    
    def calculate_soil_score(
        self,
        n_status: NutrientStatus,
        p_status: NutrientStatus,
        k_status: NutrientStatus,
        ph_status: PHStatus,
        moisture_status: MoistureStatus,
    ) -> float:
        """
        Calculate overall soil health score (0-100).
        
        Formula:
        Score = 100 - (N_penalty + P_penalty + K_penalty + pH_penalty + Moisture_penalty)
        """
        n_penalty = self.calculate_nutrient_penalty(n_status)
        p_penalty = self.calculate_nutrient_penalty(p_status)
        k_penalty = self.calculate_nutrient_penalty(k_status)
        ph_penalty = self.calculate_ph_penalty(ph_status)
        moisture_penalty = self.calculate_moisture_penalty(moisture_status)
        
        total_penalty = n_penalty + p_penalty + k_penalty + ph_penalty + moisture_penalty
        
        # Cap at 0-100
        score = max(0.0, min(100.0, 100.0 - total_penalty))
        return round(score, 2)
    
    def calculate_depletion_rate(
        self,
        previous_value: float,
        current_value: float,
        days: int,
    ) -> float:
        """
        Calculate daily depletion rate.
        
        Formula: (Previous - Current) / Days
        Positive = depletion, Negative = accumulation
        """
        if days <= 0:
            return 0.0
        return round((previous_value - current_value) / days, 4)
    
    def calculate_degradation_index(
        self,
        n_loss: float,
        p_loss: float,
        k_loss: float,
        ph_drift: float,
    ) -> float:
        """
        Calculate Soil Degradation Index (SDI).
        
        Formula:
        SDI = 0.35 * N_loss + 0.25 * P_loss + 0.20 * K_loss + 0.20 * pH_drift
        
        Normalized to 0-100 scale.
        """
        sdi = (
            self.SDI_WEIGHTS["nitrogen"] * abs(n_loss) +
            self.SDI_WEIGHTS["phosphorus"] * abs(p_loss) +
            self.SDI_WEIGHTS["potassium"] * abs(k_loss) +
            self.SDI_WEIGHTS["ph"] * abs(ph_drift)
        )
        
        # Normalize to 0-100 (assuming max loss values are normalized)
        # For simplicity, we'll scale based on typical ranges
        normalized_sdi = min(100.0, sdi * 10)  # Adjust multiplier based on actual data ranges
        return round(normalized_sdi, 2)
    
    def analyze_soil_reading(
        self,
        reading: SoilReading,
        previous_reading: Optional[SoilReading] = None,
    ) -> SoilHealth:
        """
        Analyze a single soil reading and generate health snapshot.
        
        Args:
            reading: Current soil reading
            previous_reading: Previous reading for depletion calculation
            
        Returns:
            SoilHealth object with complete analysis
        """
        # Classify nutrients
        n_status = self.classify_nitrogen(reading.nitrogen)
        p_status = self.classify_phosphorus(reading.phosphorus)
        k_status = self.classify_potassium(reading.potassium)
        ph_status = self.classify_ph(reading.ph)
        moisture_status = self.classify_moisture(reading.moisture)
        
        # Calculate soil score
        soil_score = self.calculate_soil_score(
            n_status, p_status, k_status, ph_status, moisture_status
        )
        
        # Calculate depletion rates if previous reading exists
        depletion_rates = {}
        if previous_reading:
            days_diff = (reading.timestamp - previous_reading.timestamp).days
            if days_diff > 0:
                depletion_rates = {
                    "nitrogen": self.calculate_depletion_rate(
                        previous_reading.nitrogen, reading.nitrogen, days_diff
                    ),
                    "phosphorus": self.calculate_depletion_rate(
                        previous_reading.phosphorus, reading.phosphorus, days_diff
                    ),
                    "potassium": self.calculate_depletion_rate(
                        previous_reading.potassium, reading.potassium, days_diff
                    ),
                }
        
        # Calculate degradation index
        n_loss = depletion_rates.get("nitrogen", 0.0)
        p_loss = depletion_rates.get("phosphorus", 0.0)
        k_loss = depletion_rates.get("potassium", 0.0)
        ph_drift = 0.0  # Would need previous pH to calculate
        
        if previous_reading:
            ph_drift = abs(reading.ph - previous_reading.ph)
        
        degradation_index = self.calculate_degradation_index(
            n_loss, p_loss, k_loss, ph_drift
        )
        
        # Build nutrient analyses
        n_thresholds = self.NITROGEN_THRESHOLDS[n_status.value]
        p_thresholds = self.PHOSPHORUS_THRESHOLDS[p_status.value]
        k_thresholds = self.POTASSIUM_THRESHOLDS[k_status.value]
        
        return SoilHealth(
            device_id=reading.device_id,
            date=reading.timestamp,
            nitrogen=NutrientAnalysis(
                value=reading.nitrogen,
                status=n_status,
                threshold_min=n_thresholds[0],
                threshold_max=n_thresholds[1],
            ),
            phosphorus=NutrientAnalysis(
                value=reading.phosphorus,
                status=p_status,
                threshold_min=p_thresholds[0],
                threshold_max=p_thresholds[1],
            ),
            potassium=NutrientAnalysis(
                value=reading.potassium,
                status=k_status,
                threshold_min=k_thresholds[0],
                threshold_max=k_thresholds[1],
            ),
            ph_status=ph_status,
            ph_value=reading.ph,
            moisture_status=moisture_status,
            moisture_value=reading.moisture,
            soil_score=soil_score,
            degradation_index=degradation_index,
            depletion_rates=depletion_rates,
        )
    
    def generate_recommendations(
        self,
        health: SoilHealth,
    ) -> SoilRecommendation:
        """
        Generate actionable recommendations based on soil health.
        
        Args:
            health: SoilHealth analysis
            
        Returns:
            SoilRecommendation with specific actions
        """
        recommendations = []
        priority = "low"
        urgency_days = None
        
        # Nitrogen recommendations
        if health.nitrogen.status == NutrientStatus.VERY_LOW:
            recommendations.append("nitrogen")
            priority = "critical"
            urgency_days = 3
        elif health.nitrogen.status == NutrientStatus.LOW:
            recommendations.append("nitrogen")
            if priority != "critical":
                priority = "high"
                urgency_days = 7
        
        # Phosphorus recommendations
        if health.phosphorus.status == NutrientStatus.VERY_LOW:
            recommendations.append("phosphorus")
            priority = "critical"
            urgency_days = 3
        elif health.phosphorus.status == NutrientStatus.LOW:
            recommendations.append("phosphorus")
            if priority != "critical":
                priority = "high"
                urgency_days = 7
        
        # Potassium recommendations
        if health.potassium.status == NutrientStatus.VERY_LOW:
            recommendations.append("potassium")
            priority = "critical"
            urgency_days = 3
        elif health.potassium.status == NutrientStatus.LOW:
            recommendations.append("potassium")
            if priority != "critical":
                priority = "high"
                urgency_days = 7
        
        # pH recommendations
        if health.ph_status == PHStatus.ACIDIC:
            recommendations.append("ph")
            if priority not in ["critical", "high"]:
                priority = "medium"
        elif health.ph_status == PHStatus.ALKALINE:
            recommendations.append("ph")
            if priority not in ["critical", "high"]:
                priority = "medium"
        
        # Irrigation recommendations
        if health.moisture_status == MoistureStatus.CRITICAL:
            recommendations.append("irrigation")
            priority = "critical"
            urgency_days = 1
        elif health.moisture_status == MoistureStatus.LOW:
            recommendations.append("irrigation")
            if priority != "critical":
                priority = "high"
                urgency_days = 2
        
        # Build recommendation messages
        rec = SoilRecommendation(priority=priority, urgency_days=urgency_days)
        
        if "nitrogen" in recommendations:
            if health.nitrogen.status == NutrientStatus.VERY_LOW:
                rec.nitrogen = f"Apply 25-30 kg/acre urea within {urgency_days or 7} days. Critical deficiency detected."
            elif health.nitrogen.status == NutrientStatus.LOW:
                rec.nitrogen = f"Apply 15-20 kg/acre urea within {urgency_days or 7} days."
            elif health.nitrogen.status == NutrientStatus.EXCESS:
                rec.nitrogen = "Nitrogen levels are excessive. Reduce fertilizer application."
        
        if "phosphorus" in recommendations:
            if health.phosphorus.status == NutrientStatus.VERY_LOW:
                rec.phosphorus = f"Apply 20-25 kg/acre DAP (Diammonium Phosphate) within {urgency_days or 7} days. Critical deficiency."
            elif health.phosphorus.status == NutrientStatus.LOW:
                rec.phosphorus = f"Apply 10-15 kg/acre DAP within {urgency_days or 7} days."
            elif health.phosphorus.status == NutrientStatus.EXCESS:
                rec.phosphorus = "Phosphorus levels are excessive. Reduce fertilizer application."
        
        if "potassium" in recommendations:
            if health.potassium.status == NutrientStatus.VERY_LOW:
                rec.potassium = f"Apply 15-20 kg/acre MOP (Muriate of Potash) within {urgency_days or 7} days. Critical deficiency."
            elif health.potassium.status == NutrientStatus.LOW:
                rec.potassium = f"Apply 10-15 kg/acre MOP within {urgency_days or 7} days."
            elif health.potassium.status == NutrientStatus.EXCESS:
                rec.potassium = "Potassium levels are excessive. Reduce fertilizer application."
        
        if "ph" in recommendations:
            if health.ph_status == PHStatus.ACIDIC:
                rec.ph = f"Soil is acidic (pH {health.ph_value:.1f}). Apply 500-1000 kg/acre agricultural lime to raise pH to optimal range (5.5-7.5)."
            elif health.ph_status == PHStatus.ALKALINE:
                rec.ph = f"Soil is alkaline (pH {health.ph_value:.1f}). Apply sulfur or acidifying fertilizers to lower pH to optimal range (5.5-7.5)."
        
        if "irrigation" in recommendations:
            if health.moisture_status == MoistureStatus.CRITICAL:
                rec.irrigation = "URGENT: Soil moisture is critically low. Irrigate immediately to prevent crop stress."
            elif health.moisture_status == MoistureStatus.LOW:
                rec.irrigation = "Soil moisture is low. Schedule irrigation within 24-48 hours."
            elif health.moisture_status == MoistureStatus.EXCESS:
                rec.irrigation = "Soil moisture is excessive. Delay irrigation and ensure proper drainage."
        
        # Estimate cost (simplified)
        cost = 0.0
        if rec.nitrogen:
            cost += 500.0  # Approximate cost per acre
        if rec.phosphorus:
            cost += 400.0
        if rec.potassium:
            cost += 350.0
        if rec.ph:
            cost += 800.0
        
        rec.estimated_cost = cost if cost > 0 else None
        
        return rec

