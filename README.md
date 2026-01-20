# Farmzy - Smart Farming Platform

**Soilytics** - Soil Intelligence Engine | **HydroIQ** - Smart Irrigation Intelligence Engine | **Marketplace** - Direct Buy & Sell | **AgroGo** - Rural Delivery

## 🎯 Overview

Farmzy is a comprehensive smart farming platform that converts raw ESP sensor data (moisture, pH, NPK) into actionable soil health insights, nutrient recommendations, degradation tracking, AI-powered irrigation decisions, marketplace connections, and rural delivery logistics.

## 🏗️ Architecture

```
ESP Sensors → ThingSpeak API → FastAPI Backend → Astro Frontend
```

### Project Structure

```
App/
├── frontend/          # AstroWind-based Astro frontend
│   ├── src/
│   │   ├── pages/    # All application pages
│   │   ├── components/# Reusable components
│   │   ├── layouts/  # Page layouts
│   │   └── lib/      # API clients and utilities
│   └── package.json
├── app/              # FastAPI backend
│   ├── api/         # API endpoints
│   ├── soilytics/   # Soil intelligence engine
│   └── main.py      # FastAPI application
└── README.md
```

## 🚀 Features

### Soilytics Core Engine

- **Nutrient Classification**: NPK levels (Very Low, Low, Medium, High, Excess)
- **pH Intelligence**: Acidic, Optimal, Alkaline classification
- **Moisture Intelligence**: Critical, Low, Moderate, Adequate, Excess status
- **Soil Health Score**: 0-100 comprehensive metric
- **Degradation Tracking**: Soil Degradation Index (SDI) calculation
- **Depletion Rates**: Daily nutrient depletion tracking
- **Recommendation Engine**: Actionable fertilizer and irrigation recommendations

### HydroIQ Smart Irrigation

- **AI-Powered Decisions**: Real-time irrigation recommendations based on soil, weather, and crop data
- **Evapotranspiration Calculation**: Hargreaves-based ET₀ computation
- **Zone-Based Management**: Automatic farm zone division and water distribution
- **Cycle-Based Strategy**: Optimized irrigation cycles to prevent runoff
- **Confidence Scoring**: Decision reliability metrics
- **Water Savings**: Intelligent water usage optimization

### Marketplace (Skill 3)

- **Quality-Based Pricing**: Soil score influences crop grade (A/B/C)
  - Grade A (Premium): soil_score ≥ 80 → 1.15x multiplier
  - Grade B (Good): 60 ≤ soil_score < 80 → 1.0x multiplier
  - Grade C (Standard): soil_score < 60 → 0.9x multiplier
- **Direct Listings**: Farmers list produce directly
- **Buyer Matching**: Connect with verified buyers
- **Price Optimization**: Demand-aware pricing suggestions
- **Order Management**: Complete order lifecycle tracking

### AgroGo Delivery (Skill 4)

- **Route Optimization**: Smart routing using nearest neighbor heuristic
- **Local Aggregation**: Groups nearby farms (within 10km) into single routes
- **Cost Estimation**: Transparent delivery cost calculation (₹50/km + ₹200/pickup)
- **Delivery Tracking**: Real-time status updates
- **Haversine Distance**: Accurate distance calculation for route planning

## 📦 Installation

### Backend Setup

1. **Navigate to project root**

```bash
cd App
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment**

Copy `.env.example` to `.env` and update with your credentials:

```bash
# ThingSpeak Configuration
THINGSPEAK_CHANNEL_ID=your_channel_id
THINGSPEAK_READ_API_KEY=your_read_api_key

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/farmzy_db
```

5. **Initialize database**

```bash
# Create database (PostgreSQL)
createdb farmzy_db

# Tables will be created automatically on first run
```

### Frontend Setup

1. **Navigate to frontend directory**

```bash
cd frontend
```

2. **Install dependencies**

```bash
npm install
```

3. **Configure environment**

Create `frontend/.env`:

```bash
PUBLIC_API_URL=http://localhost:8000
```

## 🏃 Running the Application

### Quick Start (Windows)

**Option 1: Run both servers together**
```batch
start-all.bat
```

**Option 2: Run servers separately**
```batch
start-backend.bat    # Backend only
start-frontend.bat   # Frontend only
```

**Option 3: Manual start**

Backend (FastAPI):
```bash
# From App/ directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend (Astro):
```bash
# From frontend/ directory
npm run dev
```

### First Time Setup

Run the setup script to install all dependencies:
```batch
setup.bat
```

### Stopping Servers

To stop all servers:
```batch
stop-all.bat
```

### Server URLs

- **Backend API**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`
- **Frontend**: `http://localhost:4321`

The frontend is configured to proxy API requests to the backend automatically.

## 📡 API Endpoints

### Soil Data (Soilytics)

- `POST /api/soil/data` - Ingest raw sensor data
- `GET /api/soil/health?device_id=xxx` - Get latest soil health
- `GET /api/soil/degradation?device_id=xxx&range=30` - Get degradation trends
- `GET /api/soil/fetch-thingspeak` - Fetch and process from ThingSpeak
- `GET /api/soil/readings?device_id=xxx` - Get historical readings

### Irrigation (HydroIQ)

- `POST /api/irrigation/compute` - Compute irrigation decision
- `POST /api/irrigation/execute` - Log irrigation execution
- `GET /api/irrigation/history?farm_id=xxx` - Get irrigation history
- `GET /api/irrigation/insights?farm_id=xxx` - Get analytics and insights

### Marketplace

- `POST /api/marketplace/list` - Create crop listing
- `GET /api/marketplace/listings?farm_id=xxx` - Get listings
- `GET /api/marketplace/pricing?crop=xxx&soil_score=xxx` - Get price suggestion
- `GET /api/marketplace/buyers?listing_id=xxx` - Get available buyers
- `POST /api/marketplace/order` - Create order
- `GET /api/marketplace/orders?farm_id=xxx` - Get farm orders

### Delivery (AgroGo)

- `POST /api/delivery/schedule` - Schedule delivery for order
- `GET /api/delivery/routes?date=xxx` - Get optimized routes
- `POST /api/delivery/aggregate` - Aggregate multiple pickups
- `GET /api/delivery/status?order_id=xxx` - Get delivery status
- `POST /api/delivery/cost-estimate` - Estimate delivery cost

### Marketplace

- `POST /api/marketplace/list` - Create crop listing
- `GET /api/marketplace/listings?farm_id=xxx` - Get listings
- `GET /api/marketplace/pricing?crop=xxx&soil_score=xxx` - Get price suggestion
- `POST /api/marketplace/order` - Create order
- `GET /api/marketplace/orders?farm_id=xxx` - Get orders

### Delivery (AgroGo)

- `POST /api/delivery/schedule` - Schedule delivery
- `GET /api/delivery/routes?date=xxx` - Get optimized routes
- `POST /api/delivery/aggregate` - Aggregate multiple pickups
- `GET /api/delivery/status?order_id=xxx` - Get delivery status
- `POST /api/delivery/cost-estimate` - Estimate delivery cost

## 🧠 Soilytics Intelligence

### Nutrient Thresholds

**Nitrogen (mg/kg)**
- Very Low: < 20
- Low: 20-40
- Medium: 40-60
- High: 60-80
- Excess: > 80

**Phosphorus (mg/kg)**
- Very Low: < 10
- Low: 10-20
- Medium: 20-30
- High: 30-40
- Excess: > 40

**Potassium (mg/kg)**
- Very Low: < 100
- Low: 100-150
- Medium: 150-200
- High: 200-250
- Excess: > 250

### Soil Health Score

```
Score = 100 - (N_penalty + P_penalty + K_penalty + pH_penalty + Moisture_penalty)
```

### Soil Degradation Index (SDI)

```
SDI = 0.35 * N_loss + 0.25 * P_loss + 0.20 * K_loss + 0.20 * pH_drift
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **NumPy/Pandas** - Data processing
- **ThingSpeak** - IoT data platform

### Frontend
- **Astro** - Modern web framework
- **AstroWind** - Template/theme
- **Tailwind CSS** - Utility-first CSS
- **TypeScript** - Type safety
- **Astro Icon** - Icon system

## 📝 Development

### Building for Production

**Frontend:**
```bash
cd frontend
npm run build
```

**Backend:**
The FastAPI backend runs as a server, no build step needed.

### Project Structure

```
App/
├── frontend/              # Astro frontend
│   ├── src/
│   │   ├── pages/        # Application pages
│   │   │   ├── index.astro           # Dashboard
│   │   │   ├── soilytics/index.astro
│   │   │   ├── hydroiq/index.astro
│   │   │   ├── marketplace/index.astro
│   │   │   └── agrogo/index.astro
│   │   ├── lib/
│   │   │   └── api/      # API clients
│   │   └── components/  # Reusable components
│   └── package.json
├── app/                  # FastAPI backend
│   ├── api/             # API routes
│   ├── soilytics/       # Soil intelligence
│   └── main.py
└── requirements.txt
```

## 🧠 System Integration Flow

```
ESP Sensors → ThingSpeak → Soilytics → HydroIQ → Marketplace → AgroGo
```

1. **Soilytics** processes sensor data → soil health score
2. **HydroIQ** uses soil health → irrigation decision
3. **Marketplace** uses soil health → quality grade & pricing
4. **AgroGo** uses marketplace orders → delivery scheduling

## 🔜 Next Steps

- Enhanced data visualization with charts
- Real-time WebSocket updates
- Mobile app integration
- Advanced analytics dashboard
- Multi-farm management
- Weather API integration (OpenWeatherMap)

## 📄 License

MIT
