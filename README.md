# Farmzy - Smart Farming Platform (Astro Edition)

**Soilytics** (Soil Intelligence) | **HydroIQ** (Smart Irrigation) | **Marketplace** (Direct Trade) | **AgroGo** (Rural Logistics)

## 🏗️ Architecture

```
ESP32 Sensors → ThingSpeak API → FastAPI Backend (Python) → AstroWind Frontend (Astro 5 + Tailwind)
```

### Project Structure

```
Farmzy1/
├── app/                  # FastAPI backend
│   ├── agrogo/           # Rural delivery & route optimization engine
│   ├── api/              # API routers (soil, irrigation, marketplace, delivery, unified)
│   ├── core/             # Core farm models and engines
│   ├── hydroiq/          # Smart irrigation intelligence engine
│   ├── marketplace/      # Direct crop listing & pricing engine
│   ├── soilytics/        # Soil intelligence & ThingSpeak integration
│   ├── static/           # Fallback plain HTML modules
│   ├── config.py         # App configuration & settings
│   ├── database.py       # SQLAlchemy database connection
│   ├── main.py           # FastAPI application
│   └── models.py         # Database ORM models
├── frontend/             # AstroWind-based Astro 5 frontend
│   ├── src/
│   │   ├── pages/        # Astro pages (/, /soilytics, /hydroiq, /marketplace, /agrogo)
│   │   ├── lib/api/      # Backend API client integration
│   │   ├── components/   # UI components
│   │   └── navigation.ts # Header & footer navigation
│   ├── package.json
│   ├── astro.config.ts
│   └── vercel.json
├── api/
│   └── index.py          # Vercel serverless function entrypoint for FastAPI
├── requirements.txt      # Python dependencies
├── run.bat               # One-click start script (Windows)
└── README.md
```

## 🚀 Getting Started

### 1. Start Both Backend & Frontend
Double-click or run:
```bash
run.bat
```

### 2. Manual Start

**Backend (FastAPI):**
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend (Astro):**
```bash
cd frontend
npm install
npm run dev
```

- **Frontend**: http://localhost:4321
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## ☁️ Deploying to Vercel

1. Import your repository into Vercel.
2. In **Settings -> General**:
   - Set **Root Directory** to `frontend`.
   - Framework will automatically be detected as **Astro**.
3. In **Settings -> Environment Variables**:
   - Add `PUBLIC_API_URL` pointing to your hosted FastAPI backend URL.
