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
    CRU_TS = "CRU_TS"  # Climatic Research Unit (CRU) Time-Series (TS)


class SpatialResolution(enum.Enum):
    MIN30 = "30m"
    MIN10 = "10m"
    MIN5 = "5m"
    MIN2_5 = "2.5m"


class ClimateVarKey(enum.Enum):
    PRECIPITATION = "PRECIPITATION"
    T_MAX = "T_MAX"
    T_MIN = "T_MIN"
    CLOUD_COVER = "CLOUD_COVER"
    WET_DAYS = "WET_DAYS"
    FROST_DAYS = "FROST_DAYS"
    WIND_SPEED = "WIND_SPEED"
    RADIATION = "RADIATION"
    DIURNAL_TEMP_RANGE = "DIURNAL_TEMP_RANGE"
    VAPOUR_PRESSURE = "VAPOUR_PRESSURE"


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

    ENSEMBLE_MEAN = "ENSEMBLE_MEAN"
    ACCESS_CM2 = "ACCESS_CM2"
    BCC_CSM2_MR = "BCC_CSM2_MR"
    CMCC_ESM2 = "CMCC_ESM2"
    EC_EARTH3_VEG = "EC_Earth3_Veg"
    FIO_ESM_2_0 = "FIO_ESM_2_0"
    GFDL_ESM4 = "GFDL_ESM4"
    GISS_E2_1_G = "GISS_E2_1_G"
    HADGEM3_GC31_LL = "HadGEM3_GC31_LL"
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
    ClimateVarKey.FROST_DAYS: ClimateVariable(
        name="FrostDays", display_name="Frost Days", unit="days", filename="frostdays"
    ),
    ClimateVarKey.RADIATION: ClimateVariable(
        name="Radiation", display_name="Radiation", unit="W/m^2", filename="radiation"
    ),
    ClimateVarKey.DIURNAL_TEMP_RANGE: ClimateVariable(
        name="DiurnalTempRange",
        display_name="Diurnal Temperature Range",
        unit="°C",
        filename="diurnaltemprange",
    ),
    ClimateVarKey.VAPOUR_PRESSURE: ClimateVariable(
        name="VapourPressure", display_name="Vapour Pressure", unit="hPa", filename="vapourpressure"
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
    ClimateVarKey.FROST_DAYS: ContourPlotConfig(
        level_lower=0, level_upper=30, colormap=plt.cm.jet_r, title="Frost days", unit="days"
    ),
    ClimateVarKey.RADIATION: ContourPlotConfig(
        level_lower=0, level_upper=300, colormap=plt.cm.jet, title="Radiation", unit="W/m^2"
    ),
    ClimateVarKey.DIURNAL_TEMP_RANGE: ContourPlotConfig(
        level_lower=5,
        level_upper=20,
        colormap=plt.cm.jet,
        title="Diurnal temperature range",
        unit="C",
    ),
    ClimateVarKey.VAPOUR_PRESSURE: ContourPlotConfig(
        level_lower=1, level_upper=34, colormap=plt.cm.jet, title="Vapour pressure", unit="hPa"
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
                    variable = CLIMATE_VARIABLES[variable_type]
                    config = ClimateDataConfig(
                        variable_type=variable_type,
                        format=self.format,
                        resolution=resolution,
                        year_range=year_range,
                        filepath=self.filepath_template.format(
                            resolution=resolution.value,
                            year_range=year_range,
                            variable_name=variable.filename.lower(),
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


CRU_TS_FILE_ABBREVIATIONS: Dict[ClimateVarKey, str] = {
    ClimateVarKey.CLOUD_COVER: "cld",
    ClimateVarKey.DIURNAL_TEMP_RANGE: "dtr",
    ClimateVarKey.WET_DAYS: "wet",
    ClimateVarKey.FROST_DAYS: "frs",
    ClimateVarKey.VAPOUR_PRESSURE: "vap",
    ClimateVarKey.T_MAX: "tmx",
    ClimateVarKey.T_MIN: "tmn",
    ClimateVarKey.PRECIPITATION: "pre",
}


@dataclass
class CRUTSClimateDataConfigGroup(ClimateDataConfigGroup):
    def create_configs(self) -> List[ClimateDataConfig]:
        configs: List[ClimateDataConfig] = []
        for variable_type in self.variable_types:
            for year_range in self.year_ranges:
                for resolution in self.resolutions:
                    abbr = CRU_TS_FILE_ABBREVIATIONS[variable_type]
                    config = ClimateDataConfig(
                        variable_type=variable_type,
                        format=self.format,
                        resolution=resolution,
                        year_range=year_range,
                        filepath=f"data/raw/cruts/cru_{abbr}_clim_{year_range[0]}-{year_range[1]}",
                        conversion_function=self.conversion_function,
                        conversion_factor=self.conversion_factor,
                        source=self.source,
                    )
                    configs.append(config)
        return configs


HISTORIC_DATA_GROUPS: List[ClimateDataConfigGroup] = [
    ClimateDataConfigGroup(
        variable_types=[ClimateVarKey.T_MAX, ClimateVarKey.T_MIN],
        format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
        source="https://www.worldclim.org/data/worldclim21.html",
        resolutions=[SpatialResolution.MIN10, SpatialResolution.MIN5],
        year_ranges=[(1970, 2000)],
        filepath_template="data/raw/worldclim/history/wc2.1_{resolution}_{variable_name}",
    ),
    CRUTSClimateDataConfigGroup(
        variable_types=[
            ClimateVarKey.WET_DAYS,
            ClimateVarKey.FROST_DAYS,
        ],
        format=DataFormat.CRU_TS,
        source="https://ipcc-browser.ipcc-data.org/browser/dataset/653/0",
        resolutions=[SpatialResolution.MIN30],
        year_ranges=[(1961, 1990)],
        conversion_factor=0.124,
    ),
    CRUTSClimateDataConfigGroup(
        variable_types=[
            ClimateVarKey.DIURNAL_TEMP_RANGE,
        ],
        format=DataFormat.CRU_TS,
        source="https://ipcc-browser.ipcc-data.org/browser/dataset/653/0",
        resolutions=[SpatialResolution.MIN30],
        year_ranges=[(1961, 1990)],
        conversion_factor=0.16,
    ),
    CRUTSClimateDataConfigGroup(
        variable_types=[
            ClimateVarKey.VAPOUR_PRESSURE,
        ],
        format=DataFormat.CRU_TS,
        source="https://ipcc-browser.ipcc-data.org/browser/dataset/653/0",
        resolutions=[SpatialResolution.MIN30],
        year_ranges=[(1961, 1990)],
        conversion_factor=0.2,
    ),
    CRUTSClimateDataConfigGroup(
        variable_types=[ClimateVarKey.CLOUD_COVER],
        format=DataFormat.CRU_TS,
        source="https://ipcc-browser.ipcc-data.org/browser/dataset/653/0",
        resolutions=[SpatialResolution.MIN30],
        year_ranges=[(1961, 1990)],
        conversion_factor=0.4,  # https://www.ipcc-data.org/obs/info/cru10/cru_cld_clim_1901-1910.html
    ),
]


FUTURE_FILE_TEMPLATE = "data/raw/worldclim/future/wc2.1_{resolution}_{variable_name}_{climate_model}_{climate_scenario}_{year_range[0]}-{year_range[1]}.tif"
FUTURE_DATE_RANGES = [(2021, 2040), (2041, 2060), (2061, 2080), (2081, 2100)]

FUTURE_DATA_GROUPS: List[FutureClimateDataConfigGroup] = [
    FutureClimateDataConfigGroup(
        variable_types=[ClimateVarKey.T_MIN, ClimateVarKey.T_MAX],
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
    ),
    FutureClimateDataConfigGroup(
        variable_types=[ClimateVarKey.T_MIN, ClimateVarKey.T_MAX],
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
            ClimateModel.EC_EARTH3_VEG,
            ClimateModel.ACCESS_CM2,
        ],
        filepath_template=FUTURE_FILE_TEMPLATE,
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
