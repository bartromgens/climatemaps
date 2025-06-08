from typing import List

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from climatemaps.config import ClimateMap
from climatemaps.config import DATA_SETS_API

app = FastAPI()

app.mount("/static/", StaticFiles(directory="website/"), name="data")


climate_maps = [ClimateMap.create(maps_config) for maps_config in DATA_SETS_API]


@app.get("/climatemap", response_model=List[ClimateMap])
def list_climate_map():
    return climate_maps
