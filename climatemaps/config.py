from dataclasses import dataclass
from typing import Optional
from typing import Tuple

from pydantic import BaseModel

from climatemaps.datasets import ClimateMapConfig
from climatemaps.datasets import ClimateVariable
from climatemaps.datasets import HISTORIC_DATA_SETS

TILE_SERVER_URL = 'http://localhost:8080/data'
ZOOM_MAX_RASTER = 4

DATA_SETS_API = HISTORIC_DATA_SETS


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
        return 6

    @property
    def zoom_factor(self) -> Optional[float]:
        return None

    @property
    def figure_dpi(self) -> int:
        return 1000


config_prod = ClimateMapsConfig()
config_dev = ClimateMapsConfigDev()

maps_config = config_dev


class ClimateMap(BaseModel):
    data_type: str
    # year: int
    year_range: Tuple[int, int]
    variable: ClimateVariable
    resolution: float  # minutes
    tiles_url: str
    colormap_url: str
    max_zoom_raster: int
    max_zoom_vector: int
    source: str

    @classmethod
    def create(cls, config: ClimateMapConfig):
        return ClimateMap(
            data_type=config.data_type,
            year_range=config.year_range,
            variable=config.variable,
            resolution=config.resolution,
            tiles_url=f"{TILE_SERVER_URL}/{config.data_type}",
            colormap_url="?",
            max_zoom_raster=4,
            max_zoom_vector=maps_config.zoom_max,
            source=config.source,
        )
