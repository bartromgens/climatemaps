from typing import List, Optional
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from citipy import citipy
import pycountry
from geopy.geocoders import Photon
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from climatemaps.config import ClimateMap
from climatemaps.settings import settings
from climatemaps.datasets import ClimateDifferenceDataConfig
from climatemaps.data import load_climate_data, load_climate_data_for_difference

from .middleware import RateLimitMiddleware
from .cache import GeoGridCache

app = FastAPI()

api = FastAPI()
app.mount("/v1", api)

climate_maps = [ClimateMap.create(maps_config) for maps_config in settings.DATA_SETS_API]

data_config_map = {config.data_type_slug: config for config in settings.DATA_SETS_API}

geocoder = Photon(user_agent="openclimatemap", timeout=10)

geo_grid_cache = GeoGridCache()

api.add_middleware(RateLimitMiddleware, calls_per_minute=1000)


@api.get("/climatemap", response_model=List[ClimateMap])
def list_climate_map():
    return climate_maps


@api.get("/colorbar/{data_type}/{month}")
def get_colorbar(data_type: str, month: int):
    """Serve colorbar image for a specific data type and month."""
    tiles_path = Path("data/tiles")
    colorbar_path = tiles_path / data_type / f"{month}_colorbar.png"

    if colorbar_path.exists():
        return FileResponse(
            colorbar_path, media_type="image/png", filename=f"{data_type}_{month}_colorbar.png"
        )
    else:
        raise HTTPException(status_code=404, detail="Colorbar not found")


class ColorbarConfigResponse(BaseModel):
    title: str
    unit: str
    levels: list[float]
    colors: list[list[float]]
    level_lower: float
    level_upper: float
    log_scale: bool


@api.get("/colorbar-config/{data_type}", response_model=ColorbarConfigResponse)
def get_colorbar_config(data_type: str):
    """Get colorbar configuration (colors and levels) as JSON for a specific data type."""
    if data_type not in data_config_map:
        raise HTTPException(status_code=404, detail=f"Data type '{data_type}' not found")

    data_config = data_config_map[data_type]
    contour_config = data_config.contour_config
    colorbar_data = contour_config.get_colorbar_data()

    return ColorbarConfigResponse(**colorbar_data)


class ClimateValueResponse(BaseModel):
    value: float
    data_type: str
    month: int
    latitude: float
    longitude: float
    unit: str
    variable_name: str


@api.get("/value/{data_type}/{month}", response_model=ClimateValueResponse)
def get_climate_value(data_type: str, month: int, lat: float, lon: float):
    if data_type not in data_config_map:
        raise HTTPException(status_code=404, detail=f"Data type '{data_type}' not found")

    if month < 1 or month > 12:
        raise HTTPException(
            status_code=400, detail=f"Invalid month: {month}. Must be between 1 and 12"
        )

    data_config = data_config_map[data_type]

    try:
        geo_grid = geo_grid_cache.get(data_type, month)

        if geo_grid is None:
            if isinstance(data_config, ClimateDifferenceDataConfig):
                geo_grid = load_climate_data_for_difference(
                    data_config.historical_config, data_config.future_config, month
                )
            else:
                geo_grid = load_climate_data(data_config, month)
            geo_grid_cache.set(data_type, month, geo_grid)

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


class NearestCityResponse(BaseModel):
    city_name: str
    country_name: str
    country_code: str
    latitude: float
    longitude: float


@api.get("/nearest-city", response_model=NearestCityResponse)
def get_nearest_city(lat: float, lon: float) -> NearestCityResponse:
    try:
        city = citipy.nearest_city(lat, lon)
        country_code = city.country_code.upper()

        country_name = country_code
        try:
            country = pycountry.countries.get(alpha_2=country_code)
            if country:
                country_name = country.name
        except Exception:
            pass

        return NearestCityResponse(
            city_name=city.city_name,
            country_name=country_name,
            country_code=country_code,
            latitude=lat,
            longitude=lon,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding nearest city: {str(e)}")


class GeocodingLocation(BaseModel):
    display_name: str
    latitude: float
    longitude: float
    type: str
    bounding_box: Optional[List[float]] = None


@api.get("/geocode", response_model=List[GeocodingLocation])
def search_locations(query: str, limit: int = 50) -> List[GeocodingLocation]:
    if not query or len(query.strip()) < 2:
        return []

    if limit < 1 or limit > 50:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 50")

    max_retries = 3
    retry_delay = 0.5

    for attempt in range(max_retries):
        try:
            results = geocoder.geocode(query, exactly_one=False, limit=50, language="en")

            if not results:
                return []

            locations: List[GeocodingLocation] = []

            for result in results:
                if not hasattr(result, "raw"):
                    continue

                raw = result.raw
                properties = raw.get("properties", {})

                if not _is_city_country_or_town_photon(properties):
                    continue

                location_type = properties.get("type", "").lower()
                bounding_box = None
                if "extent" in properties and len(properties["extent"]) == 4:
                    extent = properties["extent"]
                    bounding_box = [extent[1], extent[3], extent[0], extent[2]]

                locations.append(
                    GeocodingLocation(
                        display_name=result.address,
                        latitude=result.latitude,
                        longitude=result.longitude,
                        type=location_type,
                        bounding_box=bounding_box,
                    )
                )

            return locations[:limit]

        except GeocoderTimedOut:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2**attempt))
                continue
            raise HTTPException(status_code=504, detail="Geocoding service timed out after retries")
        except GeocoderServiceError as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2**attempt))
                continue
            raise HTTPException(status_code=503, detail=f"Geocoding service error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error searching locations: {str(e)}")


def _is_city_country_or_town_photon(properties: dict) -> bool:
    location_type = properties.get("type", "").lower()

    allowed_types = [
        "city",
        "town",
        "village",
        "hamlet",
        "state",
        "country",
    ]

    return location_type in allowed_types
