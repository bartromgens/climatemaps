from typing import List, Tuple

from climatemaps.datasets.enums import (
    ClimateModel,
    ClimateScenario,
    ClimateVarKey,
    DataFormat,
    SpatialResolution,
)
from climatemaps.datasets.models import (
    FutureClimateDataConfig,
    FutureClimateDataConfigGroup,
)
from climatemaps.geotiff import read_geotiff_future


FUTURE_FILE_TEMPLATE = "data/raw/worldclim/future/wc2.1_{resolution}_{variable_name}_{climate_model}_{climate_scenario}_{year_range[0]}-{year_range[1]}.tif"
FUTURE_DATE_RANGES: List[Tuple[int, int]] = [(2021, 2040), (2041, 2060), (2061, 2080), (2081, 2100)]


FUTURE_DATA_GROUPS: List[FutureClimateDataConfigGroup] = [
    FutureClimateDataConfigGroup(
        variable_types=[ClimateVarKey.T_MIN, ClimateVarKey.T_MAX, ClimateVarKey.PRECIPITATION],
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source="https://www.worldclim.org/data/cmip6/cmip6climate.html",
        resolutions=[SpatialResolution.MIN10, SpatialResolution.MIN5],
        year_ranges=FUTURE_DATE_RANGES,
        climate_scenarios=[
            ClimateScenario.SSP126,
            ClimateScenario.SSP245,
            ClimateScenario.SSP370,
            ClimateScenario.SSP585,
        ],
        climate_models=[
            ClimateModel.ENSEMBLE_MEAN,
        ],
        filepath_template=FUTURE_FILE_TEMPLATE,
        reader_function=read_geotiff_future,
    ),
    FutureClimateDataConfigGroup(
        variable_types=[ClimateVarKey.T_MIN, ClimateVarKey.T_MAX, ClimateVarKey.PRECIPITATION],
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source="https://www.worldclim.org/data/cmip6/cmip6climate.html",
        resolutions=[SpatialResolution.MIN10],
        year_ranges=FUTURE_DATE_RANGES,
        climate_scenarios=[
            ClimateScenario.SSP126,
            ClimateScenario.SSP245,
            ClimateScenario.SSP370,
            ClimateScenario.SSP585,
        ],
        climate_models=[
            ClimateModel.ENSEMBLE_STD_DEV,
            ClimateModel.EC_EARTH3_VEG,
            ClimateModel.ACCESS_CM2,
            ClimateModel.MPI_ESM1_2_HR,
        ],
        filepath_template=FUTURE_FILE_TEMPLATE,
        reader_function=read_geotiff_future,
    ),
    FutureClimateDataConfigGroup(
        variable_types=[ClimateVarKey.T_MIN, ClimateVarKey.T_MAX, ClimateVarKey.PRECIPITATION],
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source="https://www.worldclim.org/data/cmip6/cmip6climate.html",
        resolutions=[SpatialResolution.MIN10],
        year_ranges=FUTURE_DATE_RANGES,
        climate_scenarios=[
            ClimateScenario.SSP126,
            ClimateScenario.SSP370,
        ],
        climate_models=[
            ClimateModel.GFDL_ESM4,
        ],
        filepath_template=FUTURE_FILE_TEMPLATE,
        reader_function=read_geotiff_future,
    ),
]


FUTURE_DATA_SETS: List[FutureClimateDataConfig] = [
    cfg for data_group in FUTURE_DATA_GROUPS for cfg in data_group.create_configs()
]
