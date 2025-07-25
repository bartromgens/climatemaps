from typing import List

from fastapi import FastAPI

from climatemaps.config import ClimateMap
from climatemaps.settings import settings

app = FastAPI()

climate_maps = [ClimateMap.create(maps_config) for maps_config in settings.DATA_SETS_API]


@app.get("/climatemap", response_model=List[ClimateMap])
def list_climate_map():
    return climate_maps
