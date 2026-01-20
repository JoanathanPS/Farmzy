"""API routes for Farmzy application."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

router = APIRouter()

# Farm model data endpoint
@router.get("/api/farm/model")
async def get_farm_model():
    """Get the example farm model data."""
    return {
        "farm_id": "FARM_PNL_01",
        "location": "Poonamallee, Chennai",
        "area": 2,
        "area_unit": "acres",
        "area_m2": 8093.72,
        "soil_type": "loamy",
        "crop": "paddy",
        "irrigation_type": "drip",
        "zones": [
            {
                "zone_id": "Z1",
                "area_acres": 1,
                "area_m2": 4046.86
            },
            {
                "zone_id": "Z2",
                "area_acres": 1,
                "area_m2": 4046.86
            }
        ]
    }

@router.get("/visualization", response_class=HTMLResponse)
async def farm_visualization():
    """Serve the 3D farm visualization page."""
    static_path = Path(__file__).parent.parent / "static" / "farm_3d.html"
    return FileResponse(static_path)
