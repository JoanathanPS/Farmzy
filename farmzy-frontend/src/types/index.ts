// Shared types for Farmzy frontend

export interface SoilHealth {
  soil_score: number;
  moisture: number;
  ph: number;
  nitrogen: { value: number; status: string };
  phosphorus: { value: number; status: string };
  potassium: { value: number; status: string };
  degradation_index: number;
}

export interface IrrigationData {
  irrigate: boolean;
  net_water_liters: number;
  zones: ZoneDistribution[];
  confidence: number;
  reasons: string[];
}

export interface ZoneDistribution {
  zone_id: string;
  water_liters: number;
  duration_minutes: number;
  area_m2: number;
}

export interface MarketPricing {
  quality_grade: string;
  soil_score: number;
  suggested_price: number;
  base_price: number;
  price_multiplier: number;
  buyers_available: number;
}

export interface Listing {
  id: string;
  farm_id: string;
  crop: string;
  quantity: number;
  quality_grade: string;
  suggested_price: number;
  base_price: number;
  soil_score: number;
  status: string;
  created_at: string | null;
}

export interface Order {
  id: string;
  listing_id: string;
  buyer_id: string;
  farm_id: string;
  quantity: number;
  price_per_kg: number;
  total_price: number;
  status: string;
  created_at: string | null;
}

export interface Buyer {
  id: string;
  name: string;
  price: number;
  location: string;
  rating: number | null;
}

export interface DashboardData {
  farm: FarmInfo;
  soil: SoilHealth;
  irrigation: IrrigationData;
  marketplace: {
    pricing: MarketPricing;
    listings: Listing[];
  };
  delivery: {
    pending_deliveries: DeliveryInfo[];
  };
}

export interface FarmInfo {
  farm_id: string;
  location: { name: string; lat: number; lng: number };
  area_acres: number;
  area_m2: number;
  soil_type: string;
  crop: string;
  irrigation_type: string;
  flow_rate_lph: number;
  zones: { zone_id: string; area_acres: number; area_m2: number }[];
}

export interface DeliveryInfo {
  id: string;
  order_id: string;
  pickup_time: string | null;
  delivery_status: string;
  estimated_cost: number;
}

export interface SoilReading {
  id: number;
  device_id: string;
  timestamp: string;
  location: Record<string, number> | null;
  soil: {
    moisture: number;
    ph: number;
    nitrogen: number;
    phosphorus: number;
    potassium: number;
  };
}

export interface ThingSpeakFeed {
  created_at: string;
  entry_id: number;
  field1: string | null;
  field2: string | null;
  field3: string | null;
  field4: string | null;
  field5: string | null;
}

export interface IrrigationPlan {
  id: number;
  farm_id: string;
  irrigate: boolean;
  net_water_liters: number;
  zones: ZoneDistribution[] | null;
  confidence: number;
  status: string;
  created_at: string | null;
}

export interface IrrigationInsights {
  total_water_used_liters: number;
  total_irrigation_sessions: number;
  average_water_per_session: number;
  water_savings_estimate_liters: number;
  efficiency_score: number;
  trends: {
    water_usage: string;
    frequency: string;
  };
}

export interface DeliveryRecord {
  id: string;
  order_id: string;
  farm_id: string;
  route_id: string | null;
  pickup_time: string | null;
  delivery_distance_km: number;
  estimated_cost: number;
  actual_cost: number | null;
  delivery_status: string;
  created_at: string | null;
}

export interface Route {
  route_id: string;
  farms: Record<string, unknown>[];
  total_distance: number;
  estimated_cost: number;
  status: string;
}
