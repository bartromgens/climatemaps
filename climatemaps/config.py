import logging
import os
from dataclasses import dataclass
from typing import Optional
from typing import Tuple

from pydantic import BaseModel

from climatemaps import settings
from climatemaps.datasets import ClimateDataSetConfig
from climatemaps.datasets import ClimateVariable

logger = logging.getLogger(__name__)


@dataclass
class ClimateMapsConfig:
    data_dir_out = 'website/data'
    zoom_min = 1

    @property
    def dev_mode(self) -> bool:
        return False

    @property
    def zoom_max(self) -> int:
        return 10

    @property
    def zoom_factor(self) -> Optional[float]:
        return 2.0

    @property
    def figure_dpi(self) -> int:
        return 5000


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
        return 1000


# TODO: use local setting file instead
def get_config() -> ClimateMapsConfig:
    logger.info(f'DEV_MODE={settings.DEV_MODE}')
    return ClimateMapsConfigDev() if os.getenv("DEV") or settings.DEV_MODE else ClimateMapsConfig()


class ClimateMap(BaseModel):
    data_type: str
    year_range: Tuple[int, int]
    variable: ClimateVariable
    resolution: float  # minutes
    tiles_url: str
    colormap_url: str
    max_zoom_raster: int
    max_zoom_vector: int
    source: str

    @classmethod
    def create(cls, config: ClimateDataSetConfig):
        return ClimateMap(
            data_type=config.data_type,
            year_range=config.year_range,
            variable=config.variable,
            resolution=config.resolution,
            tiles_url=f"{settings.TILE_SERVER_URL}/{config.data_type}",
            colormap_url="?",
            max_zoom_raster=settings.ZOOM_MAX_RASTER,
            max_zoom_vector=get_config().zoom_max,
            source=config.source,
        )
