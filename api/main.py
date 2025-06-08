from typing import List
from typing import Tuple

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

app.mount("/static/", StaticFiles(directory="website/"), name="data")

TILE_SERVER_URL = 'http://localhost:8080/data'


class ClimateVariable(BaseModel):
    name: str
    display_name: str
    unit: str


precipitation = ClimateVariable(name="Precipitation", display_name="Precipitation", unit="mm/day")
temperature_max = ClimateVariable(name="Tmax", display_name="Temperature Max", unit="C")


class ClimateMap(BaseModel):
    year: int
    year_range: Tuple[int, int]
    variable: ClimateVariable
    resolution: float # minutes
    tiles_url: str
    colormap_url: str
    source: str


climate_maps = [
    ClimateMap(
        year=1990, year_range=(1970, 2000), variable=precipitation,
        resolution='10',
        tiles_url=f"{TILE_SERVER_URL}/pre_worldclim_10m",
        colormap_url="?",
        source="WorldClim 2.1"
    ),
    ClimateMap(
        year=1990, year_range=(1970, 2000), variable=temperature_max,
        resolution='10',
        tiles_url=f"{TILE_SERVER_URL}/tmax_worldclim_10m",
        colormap_url="?",
        source="WorldClim 2.1"
    ),
]


@app.get("/climatemap", response_model=List[ClimateMap])
def list_climate_map():
    return climate_maps
