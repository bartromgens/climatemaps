from typing import List, Optional
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from climatemaps.config import ClimateMap
from climatemaps.settings import settings
from climatemaps.datasets import ClimateDifferenceDataConfig
from climatemaps.data import load_climate_data, load_climate_data_for_difference

app = FastAPI()

climate_maps = [ClimateMap.create(maps_config) for maps_config in settings.DATA_SETS_API]

data_config_map = {config.data_type_slug: config for config in settings.DATA_SETS_API}

# Mount static files colorbars
tiles_path = Path("data/tiles")
if tiles_path.exists():
    app.mount("/data", StaticFiles(directory="data/tiles"), name="tiles")


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
        raise HTTPException(status_code=404, detail="Colorbar not found")


class ClimateValueResponse(BaseModel):
    value: float
    data_type: str
    month: int
    latitude: float
    longitude: float
    unit: str
    variable_name: str


@app.get("/value/{data_type}/{month}", response_model=ClimateValueResponse)
def get_climate_value(data_type: str, month: int, lat: float, lon: float):
    if data_type not in data_config_map:
        raise HTTPException(status_code=404, detail=f"Data type '{data_type}' not found")

    if month < 1 or month > 12:
        raise HTTPException(
            status_code=400, detail=f"Invalid month: {month}. Must be between 1 and 12"
        )

    data_config = data_config_map[data_type]

    try:
        if isinstance(data_config, ClimateDifferenceDataConfig):
            geo_grid = load_climate_data_for_difference(
                data_config.historical_config, data_config.future_config, month
            )
        else:
            geo_grid = load_climate_data(data_config, month)

        value = geo_grid.get_value_at_coordinate(lon, lat)

        return ClimateValueResponse(
            value=value,
            data_type=data_type,
            month=month,
            latitude=lat,
            longitude=lon,
            unit=data_config.variable.unit,
            variable_name=data_config.variable.display_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving climate value: {str(e)}")
