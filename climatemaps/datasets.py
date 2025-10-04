import calendar
import enum
from dataclasses import dataclass, field
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import numpy as np
import numpy.typing as npt
import matplotlib.pyplot as plt
from pydantic import BaseModel

from climatemaps.contour_config import ContourPlotConfig


class DataFormat(enum.Enum):
    GEOTIFF_WORLDCLIM_CMIP6 = "GEOTIFF_WORLDCLIM_CMIP6"
    GEOTIFF_WORLDCLIM_HISTORY = "GEOTIFF_WORLDCLIM_HISTORY"
    IPCC_GRID = "IPCC_GRID"


class SpatialResolution(enum.Enum):
    MIN10 = "10m"
    MIN5 = "5m"
    MIN2_5 = "2.5m"


class ClimateVarKey(enum.Enum):
    PRECIPITATION = "PRECIPITATION"
    T_MAX = "T_MAX"
    T_MIN = "T_MIN"
    CLOUD_COVER = "CLOUD_COVER"
    WET_DAYS = "WET_DAYS"
    WIND_SPEED = "WIND_SPEED"
    RADIATION = "RADIATION"


class ClimateScenario(enum.Enum):
    """
    Shared Socioeconomic Pathways (SSP) + expected level of radiative forcing in the year 2100
    """

    SSP126 = "SSP126"
    SSP245 = "SSP245"
    SSP370 = "SSP370"
    SSP585 = "SSP585"


class ClimateModel(enum.Enum):
    """
    Climate models used for future climate predictions
    """

    ACCESS_CM2 = "ACCESS_CM2"
    BCC_CSM2_MR = "BCC_CSM2_MR"
    CMCC_ESM2 = "CMCC_ESM2"
    EC_EARTH3_VEG = "EC-Earth3-Veg"
    FIO_ESM_2_0 = "FIO_ESM_2_0"
    GFDL_ESM4 = "GFDL_ESM4"
    GISS_E2_1_G = "GISS_E2_1_G"
    HADGEM3_GC31_LL = "HadGEM3-GC31-LL"
    INM_CM5_0 = "INM_CM5_0"
    IPSL_CM6A_LR = "IPSL_CM6A_LR"
    MIROC6 = "MIROC6"
    MPI_ESM1_2_HR = "MPI_ESM1_2_HR"
    MRI_ESM2_0 = "MRI_ESM2_0"
    UKESM1_0_LL = "UKESM1_0_LL"


class ClimateVariable(BaseModel):
    name: str
    display_name: str
    unit: str
    filename: str


CLIMATE_VARIABLES: Dict[ClimateVarKey, ClimateVariable] = {
    ClimateVarKey.PRECIPITATION: ClimateVariable(
        name="Precipitation", display_name="Precipitation", unit="mm/day", filename="prec"
    ),
    ClimateVarKey.T_MAX: ClimateVariable(
        name="Tmax", display_name="Temperature Max", unit="°C", filename="tmax"
    ),
    ClimateVarKey.T_MIN: ClimateVariable(
        name="Tmin", display_name="Temperature Min", unit="°C", filename="tmin"
    ),
    ClimateVarKey.CLOUD_COVER: ClimateVariable(
        name="CloudCover", display_name="Cloud Cover", unit="%", filename="cloud"
    ),
    ClimateVarKey.WET_DAYS: ClimateVariable(
        name="WetDays", display_name="Wet Days", unit="days", filename="wetdays"
    ),
    ClimateVarKey.WIND_SPEED: ClimateVariable(
        name="WindSpeed", display_name="Wind Speed", unit="m/s", filename="wind"
    ),
    ClimateVarKey.RADIATION: ClimateVariable(
        name="Radiation", display_name="Radiation", unit="W/m^2", filename="radiation"
    ),
}


CLIMATE_CONTOUR_CONFIGS: Dict[ClimateVarKey, ContourPlotConfig] = {
    ClimateVarKey.PRECIPITATION: ContourPlotConfig(
        level_lower=0.1,
        level_upper=16,
        colormap=plt.cm.jet_r,
        title="Precipitation",
        unit="mm/day",
        log_scale=True,
    ),
    ClimateVarKey.T_MAX: ContourPlotConfig(
        level_lower=-20, level_upper=45, colormap=plt.cm.jet, title="Max. temperature", unit="C"
    ),
    ClimateVarKey.T_MIN: ContourPlotConfig(
        level_lower=-30, level_upper=28, colormap=plt.cm.jet, title="Min. temperature", unit="C"
    ),
    ClimateVarKey.CLOUD_COVER: ContourPlotConfig(
        level_lower=0, level_upper=100, colormap=plt.cm.jet_r, title="Cloud coverage", unit="%"
    ),
    ClimateVarKey.WET_DAYS: ContourPlotConfig(
        level_lower=0, level_upper=30, colormap=plt.cm.jet_r, title="Wet days", unit="days"
    ),
    ClimateVarKey.WIND_SPEED: ContourPlotConfig(
        level_lower=0, level_upper=9, colormap=plt.cm.jet, title="Wind speed", unit="m/s"
    ),
    ClimateVarKey.RADIATION: ContourPlotConfig(
        level_lower=0, level_upper=300, colormap=plt.cm.jet, title="Radiation", unit="W/m^2"
    ),
}

# Contour configurations for difference maps (future - historical)
# Only includes variables that have both historical and future data available
CLIMATE_DIFFERENCE_CONTOUR_CONFIGS: Dict[ClimateVarKey, ContourPlotConfig] = {
    ClimateVarKey.PRECIPITATION: ContourPlotConfig(
        level_lower=-5,
        level_upper=5,
        colormap=plt.cm.RdBu_r,  # Red-Blue diverging colormap
        title="Precipitation Change",
        unit="mm/day",
        log_scale=False,
    ),
    ClimateVarKey.T_MAX: ContourPlotConfig(
        level_lower=-8,
        level_upper=8,
        colormap=plt.cm.RdBu_r,
        title="Max. Temperature Change",
        unit="°C",
    ),
    ClimateVarKey.T_MIN: ContourPlotConfig(
        level_lower=-5,
        level_upper=5,
        colormap=plt.cm.RdBu_r,
        title="Min. Temperature Change",
        unit="°C",
    ),
}


def convert_per_month_to_per_day(
    v: npt.NDArray[np.floating], month: int
) -> npt.NDArray[np.floating]:
    days_in_month = calendar.monthrange(2025, month)[1]
    return v / days_in_month


@dataclass
class ClimateDataConfig:
    variable_type: ClimateVarKey
    filepath: str
    format: DataFormat
    resolution: SpatialResolution
    year_range: Tuple[int, int]
    conversion_function: Callable[[npt.NDArray[np.floating], int], npt.NDArray[np.floating]] = None
    conversion_factor: float = 1
    source: Optional[str] = None

    @property
    def variable(self) -> ClimateVariable:
        return CLIMATE_VARIABLES[self.variable_type]

    @property
    def data_type_slug(self) -> str:
        return f"{self.variable.name}_{self.year_range[0]}_{self.year_range[1]}_{self.resolution.value}".lower().replace(
            ".", "_"
        )

    @property
    def contour_config(self) -> ContourPlotConfig:
        return CLIMATE_CONTOUR_CONFIGS[self.variable_type]


@dataclass
class FutureClimateDataConfig(ClimateDataConfig):
    climate_scenario: ClimateScenario = field(default=None)
    climate_model: ClimateModel = field(default=None)

    @property
    def data_type_slug(self) -> str:
        base_slug = super().data_type_slug
        return f"{base_slug}_{self.climate_scenario.name}_{self.climate_model.name}".lower()


@dataclass
class ClimateDifferenceDataConfig(ClimateDataConfig):
    """
    Configuration for climate difference maps (future - historical)
    """

    historical_config: ClimateDataConfig = field(default=None)
    future_config: FutureClimateDataConfig = field(default=None)

    @property
    def data_type_slug(self) -> str:
        if self.future_config and self.historical_config:
            return f"difference_{self.variable.name}_{self.historical_config.year_range[0]}_{self.historical_config.year_range[1]}_to_{self.future_config.year_range[0]}_{self.future_config.year_range[1]}_{self.resolution.value}_{self.future_config.climate_scenario.name}_{self.future_config.climate_model.name}".lower().replace(
                ".", "_"
            )
        return super().data_type_slug

    @property
    def contour_config(self) -> ContourPlotConfig:
        return CLIMATE_DIFFERENCE_CONTOUR_CONFIGS[self.variable_type]


@dataclass
class ClimateDataConfigGroup:
    variable_types: List[ClimateVarKey]
    format: DataFormat
    resolutions: List[SpatialResolution]
    year_ranges: List[Tuple[int, int]]
    conversion_function: Callable[[npt.NDArray[np.floating], int], npt.NDArray[np.floating]] = None
    conversion_factor: float = 1
    source: Optional[str] = None
    configs: List[ClimateDataConfig] = ()
    filepath_template: Optional[str] = None

    def __post_init__(self):
        for cfg in self.configs:
            cfg.group = self

    def create_configs(self) -> List[ClimateDataConfig]:
        configs: List[ClimateDataConfig] = []
        for variable_type in self.variable_types:
            for year_range in self.year_ranges:
                for resolution in self.resolutions:
                    config = ClimateDataConfig(
                        variable_type=variable_type,
                        format=self.format,
                        resolution=resolution,
                        year_range=year_range,
                        filepath=self.filepath_template.format(
                            resolution=resolution.value,
                            year_range=year_range,
                            variable_name=CLIMATE_VARIABLES[variable_type].filename.lower(),
                        ),
                        conversion_function=self.conversion_function,
                        conversion_factor=self.conversion_factor,
                    )
                    configs.append(config)
        return configs


@dataclass
class FutureClimateDataConfigGroup(ClimateDataConfigGroup):
    climate_scenarios: List[ClimateScenario] = field(default_factory=list)
    climate_models: List[ClimateModel] = field(default_factory=list)
    configs: List[FutureClimateDataConfig] = field(default_factory=list)

    def create_configs(self) -> List[FutureClimateDataConfig]:
        configs: List[FutureClimateDataConfig] = []
        for variable_type in self.variable_types:
            for year_range in self.year_ranges:
                for resolution in self.resolutions:
                    for climate_scenario in self.climate_scenarios:
                        for climate_model in self.climate_models:
                            config = FutureClimateDataConfig(
                                variable_type=variable_type,
                                format=self.format,
                                resolution=resolution,
                                year_range=year_range,
                                climate_scenario=climate_scenario,
                                climate_model=climate_model,
                                filepath=self.filepath_template.format(
                                    resolution=resolution.value,
                                    year_range=year_range,
                                    variable_name=CLIMATE_VARIABLES[variable_type].filename.lower(),
                                    climate_scenario=climate_scenario.name.lower(),
                                    climate_model=climate_model.value.replace("_", "-"),
                                ),
                                conversion_function=self.conversion_function,
                                conversion_factor=self.conversion_factor,
                                source=self.source,
                            )
                            configs.append(config)
        return configs


# CLIMATE_MODEL_DATA_SETS = [
#     ClimateDataConfig(
#         variable_type=ClimateVarKey.PRECIPITATION,
#         filepath="data/climate_models/wc2.1_10m_prec_ACCESS-CM2_ssp126_2021-2040.tif",
#         year_range=(2021, 2040),
#         resolution=SpatialResolution.MIN10,
#         conversion_function=convert_per_month_to_per_day,
#         format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
#         source="https://www.worldclim.org/data/cmip6/cmip6_clim10m.html",
#     )
# ]

HISTORIC_DATA_GROUPS: List[ClimateDataConfigGroup] = [
    ClimateDataConfigGroup(
        variable_types=[ClimateVarKey.T_MAX, ClimateVarKey.T_MIN, ClimateVarKey.PRECIPITATION],
        format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
        source="https://www.worldclim.org/data/worldclim21.html",
        resolutions=[SpatialResolution.MIN10, SpatialResolution.MIN5, SpatialResolution.MIN2_5],
        year_ranges=[(1970, 2000)],
        filepath_template="data/raw/worldclim/history/wc2.1_{resolution}_{variable_name}",
    ),
]

FUTURE_DATA_GROUPS: List[FutureClimateDataConfigGroup] = [
    FutureClimateDataConfigGroup(
        variable_types=[ClimateVarKey.T_MIN],
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source="https://www.worldclim.org/data/cmip6/cmip6climate.html",
        resolutions=[SpatialResolution.MIN10],
        year_ranges=[(2021, 2040), (2041, 2060), (2081, 2100)],
        climate_scenarios=[
            ClimateScenario.SSP126,
            # ClimateScenario.SSP245,
            # ClimateScenario.SSP370,
            ClimateScenario.SSP585,
        ],
        climate_models=[ClimateModel.EC_EARTH3_VEG],
        filepath_template="data/raw/worldclim/future/wc2.1_{resolution}_{variable_name}_{climate_model}_{climate_scenario}_{year_range[0]}-{year_range[1]}.tif",
    ),
]

HISTORIC_DATA_SETS: List[ClimateDataConfig] = [
    cfg for data_group in HISTORIC_DATA_GROUPS for cfg in data_group.create_configs()
]

FUTURE_DATA_SETS: List[FutureClimateDataConfig] = [
    cfg for data_group in FUTURE_DATA_GROUPS for cfg in data_group.create_configs()
]


def create_difference_map_configs() -> List[ClimateDifferenceDataConfig]:
    """
    Create difference map configurations by pairing historical and future data
    """
    difference_configs = []

    for future_config in FUTURE_DATA_SETS:
        # Find matching historical config with same variable and resolution
        historical_config = None
        for hist_config in HISTORIC_DATA_SETS:
            if (
                hist_config.variable_type == future_config.variable_type
                and hist_config.resolution == future_config.resolution
            ):
                historical_config = hist_config
                break

        if historical_config:
            diff_config = ClimateDifferenceDataConfig(
                variable_type=future_config.variable_type,
                filepath="",  # Not used for difference maps
                format=future_config.format,
                resolution=future_config.resolution,
                year_range=future_config.year_range,
                conversion_function=None,
                conversion_factor=1,
                source=f"Difference: {future_config.source} - {historical_config.source}",
                historical_config=historical_config,
                future_config=future_config,
            )
            difference_configs.append(diff_config)

    return difference_configs


DIFFERENCE_DATA_SETS: List[ClimateDifferenceDataConfig] = create_difference_map_configs()

# IPCC_HISTORIC_SETS = [
#     ClimateMapConfig(
#         data_type='precipitation',
#         filepath='data/precipitation/cpre6190.dat',
#         conversion_factor=0.1,  # (millimetres/day) *10
#         config=ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
#         format=DataFormat.IPCC_GRID,
#         source="https://www.ipcc-data.org/observ/clim/get_30yr_means.html",
#     ),
#     ClimateMapConfig(
#         data_type='cloud',
#         filepath='data/cloud/ccld6190.dat',
#         conversion_factor=1,
#         config=ContourPlotConfig(0, 100, colormap=plt.cm.jet_r, title='Cloud coverage', unit='%'),
#         format=DataFormat.IPCC_GRID,
#         source="https://www.ipcc-data.org/observ/clim/get_30yr_means.html",
#     ),
#     ClimateMapConfig(
#         data_type='mintemp',
#         filepath='data/mintemp/ctmn6190.dat',
#         conversion_factor=0.1,
#         config=ContourPlotConfig(-30, 28, colormap=plt.cm.jet, title='Min. temperature', unit='C'),
#         format=DataFormat.IPCC_GRID,
#         source="https://www.ipcc-data.org/observ/clim/get_30yr_means.html",
#     ),
#     ClimateMapConfig(
#         data_type='meantemp',
#         filepath='data/meantemp/ctmp6190.dat',
#         conversion_factor=0.1,
#         config=ContourPlotConfig(-30, 35, colormap=plt.cm.jet, title='Mean temperature', unit='C'),
#         format=DataFormat.IPCC_GRID,
#         source="https://www.ipcc-data.org/observ/clim/get_30yr_means.html",
#     ),
#     ClimateMapConfig(
#         data_type='maxtemp',
#         filepath='data/maxtemp/ctmx6190.dat',
#         conversion_factor=0.1,
#         config=ContourPlotConfig(-20, 45, colormap=plt.cm.jet, title='Max. temperature', unit='C'),
#         format=DataFormat.IPCC_GRID,
#         source="https://www.ipcc-data.org/observ/clim/get_30yr_means.html",
#     ),
#     ClimateMapConfig(
#         data_type='diurnaltemprange',
#         filepath='data/diurnaltemprange/cdtr6190.dat',
#         conversion_factor=0.1,
#         config=ContourPlotConfig(5, 20, colormap=plt.cm.jet, title='Diurnal temperature range', unit='C'),
#         format=DataFormat.IPCC_GRID,
#         source="https://www.ipcc-data.org/observ/clim/get_30yr_means.html",
#     ),
#     ClimateMapConfig(
#         data_type='wetdays',
#         filepath='data/wetdays/cwet6190.dat',
#         conversion_factor=0.1,
#         config=ContourPlotConfig(0, 30, colormap=plt.cm.jet_r, title='Wet days', unit='days'),
#         format=DataFormat.IPCC_GRID,
#         source="https://www.ipcc-data.org/observ/clim/get_30yr_means.html",
#     ),
#     ClimateMapConfig(
#         data_type='wind',
#         filepath='data/wind/cwnd6190.dat',
#         conversion_factor=0.1,
#         config=ContourPlotConfig(0, 9, colormap=plt.cm.jet, title='Wind speed', unit='m/s'),
#         format=DataFormat.IPCC_GRID,
#         source="https://www.ipcc-data.org/observ/clim/get_30yr_means.html",
#     ),
#     ClimateMapConfig(
#         data_type='radiation',
#         filepath='data/radiation/crad6190.dat',
#         conversion_factor=1,
#         config=ContourPlotConfig(0, 300, colormap=plt.cm.jet, title='Radiation', unit='W/m^2'),
#         format=DataFormat.IPCC_GRID,
#         source="https://www.ipcc-data.org/observ/clim/get_30yr_means.html",
#     ),
#     ClimateMapConfig(
#         data_type='vapourpressure',
#         filepath='data/vapourpressure/cvap6190.dat',
#         conversion_factor=0.1,
#         config=ContourPlotConfig(1, 34, colormap=plt.cm.jet, title='Vapour pressure', unit='hPa'),
#         format=DataFormat.IPCC_GRID,
#         source="https://www.ipcc-data.org/observ/clim/get_30yr_means.html",
#     ),
# ]
