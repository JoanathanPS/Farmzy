"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.config import settings

# Try to import database and routers (may fail if DB not configured)
try:
    from app.database import engine, Base
    if engine:
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as db_error:
            print(f"Warning: Database initialization failed: {db_error}")
except Exception as import_error:
    print(f"Warning: Could not import database module: {import_error}")

try:
    from app.api import soil, irrigation, unified, marketplace, delivery
    SOIL_ROUTER_AVAILABLE = True
    IRRIGATION_ROUTER_AVAILABLE = True
    UNIFIED_ROUTER_AVAILABLE = True
    MARKETPLACE_ROUTER_AVAILABLE = True
    DELIVERY_ROUTER_AVAILABLE = True
except Exception as router_error:
    print(f"Warning: Could not import API routers: {router_error}")
    SOIL_ROUTER_AVAILABLE = False
    IRRIGATION_ROUTER_AVAILABLE = False
    UNIFIED_ROUTER_AVAILABLE = False
    MARKETPLACE_ROUTER_AVAILABLE = False
    DELIVERY_ROUTER_AVAILABLE = False

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Farmzy - Smart Farming Backend with Soilytics & HydroIQ Intelligence Engines",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include routers (if available)
if SOIL_ROUTER_AVAILABLE:
    app.include_router(soil.router)
if IRRIGATION_ROUTER_AVAILABLE:
    app.include_router(irrigation.router)
if MARKETPLACE_ROUTER_AVAILABLE:
    app.include_router(marketplace.router)
if DELIVERY_ROUTER_AVAILABLE:
    app.include_router(delivery.router)
if UNIFIED_ROUTER_AVAILABLE:
    app.include_router(unified.router)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the unified dashboard."""
    dashboard_path = static_path / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    # Fallback to index if dashboard doesn't exist
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse(content="<h1>Farmzy Frontend</h1><p>dashboard.html not found</p>")


@app.get("/modules", response_class=HTMLResponse)
async def modules_view():
    """Serve the module-by-module view."""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse(content="<h1>Farmzy Modules</h1><p>index.html not found</p>")


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "message": "Farmzy API - Smart Farming Backend",
        "version": settings.app_version,
        "status": "operational",
        "modules": {
            "soilytics": "Soil Intelligence Engine",
            "hydroiq": "Smart Irrigation Intelligence Engine",
            "marketplace": "Direct Buy & Sell Platform",
            "agrogo": "Rural Delivery System",
            "unified": "Unified Dashboard API",
        },
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
    }

