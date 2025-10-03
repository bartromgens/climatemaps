from typing import List
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from climatemaps.config import ClimateMap
from climatemaps.settings import settings

app = FastAPI()

climate_maps = [ClimateMap.create(maps_config) for maps_config in settings.DATA_SETS_API]

# Mount static files for tiles and colorbars
tiles_path = Path("tiles")
if tiles_path.exists():
    app.mount("/data", StaticFiles(directory="tiles"), name="tiles")


@app.get("/climatemap", response_model=List[ClimateMap])
def list_climate_map():
    return climate_maps


@app.get("/colorbar/{data_type}/{month}")
def get_colorbar(data_type: str, month: int):
    """Serve colorbar image for a specific data type and month."""
    colorbar_path = tiles_path / data_type / f"{month}_colorbar.png"

    if colorbar_path.exists():
        return FileResponse(
            colorbar_path, media_type="image/png", filename=f"{data_type}_{month}_colorbar.png"
        )
    else:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Colorbar not found")
