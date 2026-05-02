import logging
import os
from dataclasses import dataclass
from typing import Optional
from typing import Tuple

from pydantic import BaseModel

from climatemaps.datasets import SpatialResolution
from climatemaps.settings import settings
from climatemaps.datasets import ClimateDataConfig
from climatemaps.datasets import ClimateDifferenceDataConfig
from climatemaps.datasets import ClimateVariable
from climatemaps.datasets import ClimateModel
from climatemaps.datasets import ClimateScenario

logger = logging.getLogger(__name__)


@dataclass
class ClimateMapsConfig:
    data_dir_out = "data/tiles"
    zoom_min = 0

    @property
    def dev_mode(self) -> bool:
        return False

    @property
    def zoom_max_vector(self) -> int:
        return 8


class ClimateMapsConfigDev(ClimateMapsConfig):

    @property
    def dev_mode(self) -> bool:
        return True

    @property
    def zoom_max_vector(self) -> int:
        return 8


def get_config() -> ClimateMapsConfig:
    logger.info(f"DEV_MODE={settings.DEV_MODE}")
    return ClimateMapsConfigDev() if os.getenv("DEV") or settings.DEV_MODE else ClimateMapsConfig()


class ClimateMap(BaseModel):
    data_type: str
    year_range: Tuple[int, int]
    variable: ClimateVariable
    resolution: SpatialResolution
    resolution_effective: float
    tiles_url: str
    colormap_url: str
    max_zoom_raster: int
    max_zoom_vector: int
    source: Optional[str]
    climate_model: Optional[ClimateModel] = None
    climate_scenario: Optional[ClimateScenario] = None
    is_difference_map: bool = False
    historical_year_range: Optional[Tuple[int, int]] = None

    @classmethod
    def create(cls, config: ClimateDataConfig):
        # Check if config has climate model and scenario (FutureClimateDataConfig)
        climate_model = getattr(config, "climate_model", None)
        climate_scenario = getattr(config, "climate_scenario", None)

        # Check if this is a difference map
        is_difference_map = isinstance(config, ClimateDifferenceDataConfig)
        historical_year_range = None

        if is_difference_map and config.historical_config:
            historical_year_range = config.historical_config.year_range
            # For difference maps, get climate model and scenario from future_config
            if hasattr(config, "future_config") and config.future_config:
                climate_model = config.future_config.climate_model
                climate_scenario = config.future_config.climate_scenario

        resolution_effective = config.resolution_effective

        return ClimateMap(
            data_type=config.data_type_slug,
            year_range=config.year_range,
            variable=config.variable,
            resolution=config.resolution_input,
            resolution_effective=resolution_effective,
            tiles_url=f"{settings.TILE_SERVER_URL}/{config.data_type_slug}",
            colormap_url=f"{settings.API_BASE_URL}/colorbar/{config.data_type_slug}",
            max_zoom_raster=config.target_max_zoom_raster,
            max_zoom_vector=get_config().zoom_max_vector,
            source=config.source,
            climate_model=climate_model,
            climate_scenario=climate_scenario,
            is_difference_map=is_difference_map,
            historical_year_range=historical_year_range,
        )
