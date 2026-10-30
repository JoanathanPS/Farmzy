-- ========================================================
-- Farmzy Supabase PostgreSQL Database Schema
-- Paste and Run this in Supabase Dashboard -> SQL Editor
-- ========================================================

-- 1. Raw Soil Sensor Readings
CREATE TABLE IF NOT EXISTS public.soil_readings (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    location JSONB,
    moisture DOUBLE PRECISION NOT NULL,
    ph DOUBLE PRECISION NOT NULL,
    nitrogen DOUBLE PRECISION NOT NULL,
    phosphorus DOUBLE PRECISION NOT NULL,
    potassium DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_soil_readings_device_id ON public.soil_readings(device_id);
CREATE INDEX IF NOT EXISTS idx_soil_readings_timestamp ON public.soil_readings(timestamp);

-- 2. Soil Health Snapshots (Calculated from readings)
CREATE TABLE IF NOT EXISTS public.soil_health (
    id SERIAL PRIMARY KEY,
    farm_id VARCHAR(100),
    device_id VARCHAR(100) NOT NULL,
    date TIMESTAMPTZ NOT NULL,
    nitrogen_status VARCHAR(50) NOT NULL,
    nitrogen_value DOUBLE PRECISION NOT NULL,
    phosphorus_status VARCHAR(50) NOT NULL,
    phosphorus_value DOUBLE PRECISION NOT NULL,
    potassium_status VARCHAR(50) NOT NULL,
    potassium_value DOUBLE PRECISION NOT NULL,
    ph_status VARCHAR(50) NOT NULL,
    ph_value DOUBLE PRECISION NOT NULL,
    moisture_status VARCHAR(50) NOT NULL,
    moisture_value DOUBLE PRECISION NOT NULL,
    soil_score DOUBLE PRECISION NOT NULL,
    degradation_index DOUBLE PRECISION NOT NULL,
    depletion_rates JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_soil_health_device_id ON public.soil_health(device_id);
CREATE INDEX IF NOT EXISTS idx_soil_health_date ON public.soil_health(date);

-- 3. Soil Nutrient & Irrigation Recommendations
CREATE TABLE IF NOT EXISTS public.recommendations (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL,
    farm_id VARCHAR(100),
    nitrogen_rec TEXT,
    phosphorus_rec TEXT,
    potassium_rec TEXT,
    ph_rec TEXT,
    irrigation_rec TEXT,
    priority VARCHAR(50) DEFAULT 'medium',
    estimated_cost DOUBLE PRECISION,
    urgency_days INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_acknowledged VARCHAR(10) DEFAULT 'false'
);

CREATE INDEX IF NOT EXISTS idx_recommendations_device_id ON public.recommendations(device_id);

-- 4. HydroIQ Irrigation Plans
CREATE TABLE IF NOT EXISTS public.irrigation_plans (
    id SERIAL PRIMARY KEY,
    farm_id VARCHAR(100) NOT NULL,
    irrigate VARCHAR(10) NOT NULL,
    net_water_liters DOUBLE PRECISION NOT NULL,
    zones JSONB,
    strategy JSONB,
    reasons JSONB,
    confidence DOUBLE PRECISION NOT NULL,
    computed_values JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    scheduled_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_irrigation_plans_farm_id ON public.irrigation_plans(farm_id);

-- 5. Irrigation Execution History
CREATE TABLE IF NOT EXISTS public.irrigation_executions (
    id SERIAL PRIMARY KEY,
    plan_id INTEGER NOT NULL,
    farm_id VARCHAR(100) NOT NULL,
    executed_zones JSONB,
    actual_water_liters DOUBLE PRECISION,
    execution_start TIMESTAMPTZ NOT NULL,
    execution_end TIMESTAMPTZ,
    status VARCHAR(50) DEFAULT 'executing',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_irrigation_executions_plan_id ON public.irrigation_executions(plan_id);

-- 6. Marketplace Produce Listings
CREATE TABLE IF NOT EXISTS public.listings (
    id SERIAL PRIMARY KEY,
    farm_id VARCHAR(100) NOT NULL,
    crop VARCHAR(100) NOT NULL,
    quantity DOUBLE PRECISION NOT NULL,
    quality_grade VARCHAR(10) NOT NULL,
    soil_score DOUBLE PRECISION NOT NULL,
    suggested_price DOUBLE PRECISION NOT NULL,
    base_price DOUBLE PRECISION NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_listings_farm_id ON public.listings(farm_id);

-- 7. Marketplace Orders
CREATE TABLE IF NOT EXISTS public.orders (
    id SERIAL PRIMARY KEY,
    listing_id VARCHAR(100) NOT NULL,
    buyer_id VARCHAR(100) NOT NULL,
    farm_id VARCHAR(100) NOT NULL,
    quantity DOUBLE PRECISION NOT NULL,
    price_per_kg DOUBLE PRECISION NOT NULL,
    total_price DOUBLE PRECISION NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_farm_id ON public.orders(farm_id);

-- 8. AgroGo Rural Deliveries
CREATE TABLE IF NOT EXISTS public.deliveries (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(100) NOT NULL,
    farm_id VARCHAR(100) NOT NULL,
    route_id VARCHAR(100),
    pickup_time TIMESTAMPTZ NOT NULL,
    delivery_distance_km DOUBLE PRECISION NOT NULL,
    estimated_cost DOUBLE PRECISION NOT NULL,
    actual_cost DOUBLE PRECISION,
    delivery_status VARCHAR(50) DEFAULT 'scheduled',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_deliveries_farm_id ON public.deliveries(farm_id);

-- 9. AgroGo Optimized Routes
CREATE TABLE IF NOT EXISTS public.routes (
    id SERIAL PRIMARY KEY,
    route_id VARCHAR(100) UNIQUE NOT NULL,
    date TIMESTAMPTZ NOT NULL,
    farms JSONB NOT NULL,
    total_distance_km DOUBLE PRECISION NOT NULL,
    estimated_cost DOUBLE PRECISION NOT NULL,
    status VARCHAR(50) DEFAULT 'planned',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_routes_route_id ON public.routes(route_id);
CREATE INDEX IF NOT EXISTS idx_routes_date ON public.routes(date);

-- Enable Realtime for Listings (for live updates in frontend)
ALTER PUBLICATION supabase_realtime ADD TABLE public.listings;

-- ========================================================
-- Grant Permissions & Disable RLS for Direct Supabase API
-- (Allows frontend & backend to read/write using SUPABASE_KEY without database passwords)
-- ========================================================
ALTER TABLE public.soil_readings DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.soil_health DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendations DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.irrigation_plans DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.irrigation_executions DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.listings DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.deliveries DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.routes DISABLE ROW LEVEL SECURITY;

GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;

