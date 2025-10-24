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
    zoom_min = 1

    @property
    def dev_mode(self) -> bool:
        return False

    @property
    def zoom_max(self) -> int:
        return 8

    @property
    def zoom_factor(self) -> Optional[float]:
        return 2.0

    @property
    def figure_dpi(self) -> int:
        return 1000


class ClimateMapsConfigDev(ClimateMapsConfig):

    @property
    def dev_mode(self) -> bool:
        return True

    @property
    def zoom_max(self) -> int:
        return 7

    @property
    def zoom_factor(self) -> Optional[float]:
        return None

    @property
    def figure_dpi(self) -> int:
        return 700


def get_config() -> ClimateMapsConfig:
    logger.info(f"DEV_MODE={settings.DEV_MODE}")
    return ClimateMapsConfigDev() if os.getenv("DEV") or settings.DEV_MODE else ClimateMapsConfig()


class ClimateMap(BaseModel):
    data_type: str
    year_range: Tuple[int, int]
    variable: ClimateVariable
    resolution: SpatialResolution  # minutes
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

        return ClimateMap(
            data_type=config.data_type_slug,
            year_range=config.year_range,
            variable=config.variable,
            resolution=config.resolution,
            tiles_url=f"{settings.TILE_SERVER_URL}/{config.data_type_slug}",
            colormap_url=f"{settings.API_BASE_URL}/colorbar/{config.data_type_slug}",
            max_zoom_raster=settings.ZOOM_MAX_RASTER,
            max_zoom_vector=get_config().zoom_max,
            source=config.source,
            climate_model=climate_model,
            climate_scenario=climate_scenario,
            is_difference_map=is_difference_map,
            historical_year_range=historical_year_range,
        )
