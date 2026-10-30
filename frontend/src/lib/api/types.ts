// API Response Types

export interface SoilHealth {
  device_id: string;
  farm_id?: string;
  date: string;
  nitrogen: {
    value: number;
    status: string;
  };
  phosphorus: {
    value: number;
    status: string;
  };
  potassium: {
    value: number;
    status: string;
  };
  ph: {
    value: number;
    status: string;
  };
  moisture: {
    value: number;
    status: string;
  };
  soil_score: number;
  degradation_index: number;
  depletion_rates: Record<string, number>;
  recommendations?: {
    nitrogen?: string;
    phosphorus?: string;
    potassium?: string;
    ph?: string;
    irrigation?: string;
    priority: string;
    estimated_cost?: number;
    urgency_days?: number;
  };
}

export interface DegradationTrend {
  date: string;
  soil_score: number;
  degradation_index: number;
  nitrogen_value: number;
  phosphorus_value: number;
  potassium_value: number;
  depletion_rates: Record<string, number>;
}

export interface IrrigationDecision {
  irrigate: boolean;
  net_water_liters: number;
  zones: Array<{
    zone_id: string;
    water_liters: number;
    duration_minutes: number;
  }>;
  strategy: {
    cycle_on_min: number;
    cycle_off_min: number;
  };
  reasons: string[];
  confidence: number;
  computed_values: {
    et0_mm?: number;
    etcrop_mm?: number;
    effective_rain_mm?: number;
    field_capacity_pct?: number;
    trigger_threshold_pct?: number;
  };
  timestamp: string;
}

export interface MarketplaceListing {
  id: string;
  farm_id: string;
  crop: string;
  quantity: number;
  quality_grade: string;
  suggested_price: number;
  base_price: number;
  soil_score: number;
  status: string;
  created_at: string;
}

export interface Buyer {
  id: string;
  name: string;
  price: number;
  location: string;
}

export interface Order {
  id: string;
  listing_id: string;
  buyer_id: string;
  quantity: number;
  price: number;
  status: string;
  created_at: string;
}

export interface Delivery {
  id: string;
  order_id: string;
  farm_id: string;
  pickup_time: string;
  delivery_distance_km: number;
  estimated_cost: number;
  delivery_status: string;
  route?: {
    farms: Array<{
      farm_id: string;
      location: { lat: number; lng: number };
    }>;
    total_distance: number;
  };
}

