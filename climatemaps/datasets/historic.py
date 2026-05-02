from typing import List

from climatemaps.datasets.enums import ClimateVarKey, DataFormat, SpatialResolution
from climatemaps.datasets.models import (
    CHELSAClimateDataConfigGroup,
    ClimateDataConfig,
    ClimateDataConfigGroup,
)
from climatemaps.geotiff import read_geotiff_chelsa, read_geotiff_history


HISTORIC_DATA_GROUPS: List[ClimateDataConfigGroup] = [
    ClimateDataConfigGroup(
        variable_types=[
            ClimateVarKey.T_MAX,
            ClimateVarKey.T_MIN,
            ClimateVarKey.PRECIPITATION,
        ],
        format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
        source="https://www.worldclim.org/data/worldclim21.html",
        resolutions=[SpatialResolution.MIN10, SpatialResolution.MIN5],
        year_ranges=[(1970, 2000)],
        filepath_template="data/raw/worldclim/history/wc2.1_{resolution}_{variable_name}",
        reader_function=read_geotiff_history,
    ),
    CHELSAClimateDataConfigGroup(
        variable_types=[
            ClimateVarKey.T_MAX,
            ClimateVarKey.T_MIN,
            ClimateVarKey.PRECIPITATION,
            ClimateVarKey.RELATIVE_HUMIDITY,
            ClimateVarKey.RADIATION,
            ClimateVarKey.MOISTURE_INDEX,
            ClimateVarKey.POTENTIAL_EVAPOTRANSPIRATION,
            ClimateVarKey.VAPOUR_PRESSURE_DEFICIT,
            ClimateVarKey.WIND_SPEED,
        ],
        format=DataFormat.CHELSA,
        source="https://www.chelsa-climate.org/datasets/chelsa_climatologies",
        resolutions=[SpatialResolution.MIN0_5],
        year_ranges=[(1981, 2010)],
        reader_function=read_geotiff_chelsa,
    ),
    CHELSAClimateDataConfigGroup(
        variable_types=[
            ClimateVarKey.CLOUD_COVER,
        ],
        format=DataFormat.CHELSA,
        source="https://www.chelsa-climate.org/datasets/chelsa_climatologies",
        resolutions=[SpatialResolution.MIN1_5],
        year_ranges=[(1981, 2010)],
        reader_function=read_geotiff_chelsa,
    ),
]


HISTORIC_DATA_SETS: List[ClimateDataConfig] = [
    cfg for data_group in HISTORIC_DATA_GROUPS for cfg in data_group.create_configs()
]

HISTORIC_DATA_SETS_API: List[ClimateDataConfig] = [
    cfg for cfg in HISTORIC_DATA_SETS if cfg.format != DataFormat.GEOTIFF_WORLDCLIM_HISTORY
]
