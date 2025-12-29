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
from climatemaps.sunshine import calculate_sunshine_hours


def chelsa_temperature_conversion(
    values: npt.NDArray[np.floating], month: int
) -> npt.NDArray[np.floating]:
    """
    Convert CHELSA temperature data from tenths of Kelvin to Celsius.

    CHELSA temperature data is stored in tenths of Kelvin, so we need to:
    1. Convert from tenths of Kelvin to Kelvin (already done by conversion_factor=0.1)
    2. Convert from Kelvin to Celsius (subtract 273.15)
    """
    return values - 273.15


class DataFormat(enum.Enum):
    GEOTIFF_WORLDCLIM_CMIP6 = "GEOTIFF_WORLDCLIM_CMIP6"
    GEOTIFF_WORLDCLIM_HISTORY = "GEOTIFF_WORLDCLIM_HISTORY"
    CRU_TS = "CRU_TS"  # Climatic Research Unit (CRU) Time-Series (TS)
    CHELSA = "CHELSA"  # CHELSA climate data


class SpatialResolution(enum.Enum):
    MIN30 = "30m"
    MIN10 = "10m"
    MIN5 = "5m"
    MIN2_5 = "2.5m"
    MIN0_5 = "0.5m"


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
    RELATIVE_HUMIDITY = "RELATIVE_HUMIDITY"
    POTENTIAL_EVAPOTRANSPIRATION = "POTENTIAL_EVAPOTRANSPIRATION"
    MOISTURE_INDEX = "MOISTURE_INDEX"
    VAPOUR_PRESSURE_DEFICIT = "VAPOUR_PRESSURE_DEFICIT"
    APPARENT_TEMPERATURE = "APPARENT_TEMPERATURE"
    SUNSHINE_HOURS = "SUNSHINE_HOURS"


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
    ENSEMBLE_STD_DEV = "ENSEMBLE_STD_DEV"
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

    @property
    def filename(self) -> str:
        return self.value.replace("_", "-")


class ClimateVariable(BaseModel):
    name: str
    display_name: str
    unit: str
    filename: str


CLIMATE_VARIABLES: Dict[ClimateVarKey, ClimateVariable] = {
    ClimateVarKey.PRECIPITATION: ClimateVariable(
        name="Precipitation", display_name="Precipitation", unit="mm/month", filename="prec"
    ),
    ClimateVarKey.T_MAX: ClimateVariable(
        name="Tmax", display_name="Temperature (Day)", unit="°C", filename="tmax"
    ),
    ClimateVarKey.T_MIN: ClimateVariable(
        name="Tmin", display_name="Temperature (Night)", unit="°C", filename="tmin"
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
    ClimateVarKey.WIND_SPEED: ClimateVariable(
        name="WindSpeed", display_name="Wind Speed", unit="m/s", filename="wind"
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
    ClimateVarKey.RELATIVE_HUMIDITY: ClimateVariable(
        name="RelativeHumidity",
        display_name="Relative Humidity",
        unit="%",
        filename="relativehumidity",
    ),
    ClimateVarKey.MOISTURE_INDEX: ClimateVariable(
        name="MoistureIndex",
        display_name="Moisture Index",
        unit="mm/month",
        filename="moistureindex",
    ),
    ClimateVarKey.VAPOUR_PRESSURE_DEFICIT: ClimateVariable(
        name="VapourPressureDeficit",
        display_name="Vapour Pressure Deficit",
        unit="Pa",
        filename="vapourpressuredeficit",
    ),
    ClimateVarKey.POTENTIAL_EVAPOTRANSPIRATION: ClimateVariable(
        name="PotentialEvapotranspiration",
        display_name="Potential Evapotranspiration",
        unit="mm/month",
        filename="pet",
    ),
    ClimateVarKey.APPARENT_TEMPERATURE: ClimateVariable(
        name="ApparentTemperature",
        display_name="Apparent Temperature",
        unit="°C",
        filename="apparenttemp",
    ),
    ClimateVarKey.SUNSHINE_HOURS: ClimateVariable(
        name="SunshineHours",
        display_name="Sunshine Hours",
        unit="hours/day",
        filename="sunshinehours",
    ),
}


CLIMATE_CONTOUR_CONFIGS: Dict[ClimateVarKey, ContourPlotConfig] = {
    ClimateVarKey.PRECIPITATION: ContourPlotConfig(
        level_lower=5,
        level_upper=400,
        colormap=plt.cm.RdYlBu,
        title="Precipitation",
        unit="mm/month",
        log_scale=True,
    ),
    ClimateVarKey.T_MAX: ContourPlotConfig(
        level_lower=-20, level_upper=45, colormap=plt.cm.jet, title="Temperature (Day)", unit="C"
    ),
    ClimateVarKey.T_MIN: ContourPlotConfig(
        level_lower=-30, level_upper=28, colormap=plt.cm.jet, title="Temperature (Night)", unit="C"
    ),
    ClimateVarKey.CLOUD_COVER: ContourPlotConfig(
        level_lower=10,
        level_upper=90,
        colormap=plt.cm.RdYlBu,
        title="Cloud coverage",
        unit="%",
        n_contours=11,
    ),
    ClimateVarKey.WET_DAYS: ContourPlotConfig(
        level_lower=0, level_upper=30, colormap=plt.cm.RdYlBu, title="Wet days", unit="days"
    ),
    ClimateVarKey.FROST_DAYS: ContourPlotConfig(
        level_lower=0, level_upper=30, colormap=plt.cm.RdYlBu, title="Frost days", unit="days"
    ),
    ClimateVarKey.WIND_SPEED: ContourPlotConfig(
        level_lower=0, level_upper=8, colormap=plt.cm.viridis, title="Wind Speed", unit="m/s"
    ),
    ClimateVarKey.RADIATION: ContourPlotConfig(
        level_lower=0, level_upper=320, colormap=plt.cm.RdYlBu_r, title="Radiation", unit="W/m^2"
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
    ClimateVarKey.RELATIVE_HUMIDITY: ContourPlotConfig(
        level_lower=25, level_upper=100, colormap=plt.cm.RdYlBu, title="Relative Humidity", unit="%"
    ),
    ClimateVarKey.MOISTURE_INDEX: ContourPlotConfig(
        level_lower=-250,
        level_upper=250,
        colormap=plt.cm.viridis,
        title="Moisture Index",
        unit="mm/month",
        n_contours=16,
    ),
    ClimateVarKey.VAPOUR_PRESSURE_DEFICIT: ContourPlotConfig(
        level_lower=0,
        level_upper=2500,
        colormap=plt.cm.viridis,
        title="Vapour Pressure Deficit",
        unit="Pa",
        n_contours=16,
    ),
    ClimateVarKey.POTENTIAL_EVAPOTRANSPIRATION: ContourPlotConfig(
        level_lower=10,
        level_upper=300,
        colormap=plt.cm.RdYlBu,
        title="Potential Evapotranspiration",
        unit="mm/month",
        log_scale=True,
    ),
    ClimateVarKey.APPARENT_TEMPERATURE: ContourPlotConfig(
        level_lower=-25,
        level_upper=50,
        colormap=plt.cm.jet,
        title="Apparent Temperature",
        unit="°C",
    ),
    ClimateVarKey.SUNSHINE_HOURS: ContourPlotConfig(
        level_lower=0,
        level_upper=14,
        colormap=plt.cm.YlOrRd,
        title="Sunshine Hours",
        unit="hours/day",
        n_contours=15,
    ),
}

# Contour configurations for difference maps (future - historical)
# Only includes variables that have both historical and future data available
CLIMATE_DIFFERENCE_CONTOUR_CONFIGS: Dict[ClimateVarKey, ContourPlotConfig] = {
    ClimateVarKey.PRECIPITATION: ContourPlotConfig(
        level_lower=-35,
        level_upper=35,
        colormap=plt.cm.RdBu,
        title="Precipitation Change",
        unit="mm/month",
    ),
    ClimateVarKey.T_MAX: ContourPlotConfig(
        level_lower=-6,
        level_upper=6,
        colormap=plt.cm.RdYlBu_r,
        title="Temperature (Day) Change",
        unit="°C",
    ),
    ClimateVarKey.T_MIN: ContourPlotConfig(
        level_lower=-5,
        level_upper=5,
        colormap=plt.cm.RdYlBu_r,
        title="Temperature (Night) Change",
        unit="°C",
    ),
}

# Contour configurations for ensemble std dev difference maps
# Uses smaller ranges for temperature variables (-2 to 2)
CLIMATE_DIFFERENCE_CONTOUR_CONFIGS_STD_DEV: Dict[ClimateVarKey, ContourPlotConfig] = {
    ClimateVarKey.PRECIPITATION: ContourPlotConfig(
        level_lower=1,
        level_upper=75,
        colormap=plt.cm.RdYlGn_r,
        title="Precipitation Change",
        unit="mm/month",
        log_scale=True,
    ),
    ClimateVarKey.T_MAX: ContourPlotConfig(
        level_lower=0,
        level_upper=2,
        colormap=plt.cm.RdYlGn_r,
        title="Temperature (Day) Change",
        unit="°C",
    ),
    ClimateVarKey.T_MIN: ContourPlotConfig(
        level_lower=0,
        level_upper=2,
        colormap=plt.cm.RdYlGn_r,
        title="Temperature (Night) Change",
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
    resolution_input: SpatialResolution
    year_range: Tuple[int, int]
    conversion_function: Callable[[npt.NDArray[np.floating], int], npt.NDArray[np.floating]] = None
    conversion_factor: float = 1
    source: Optional[str] = None
    TARGET_ZOOM_LEVEL = 6

    @property
    def variable(self) -> ClimateVariable:
        return CLIMATE_VARIABLES[self.variable_type]

    @property
    def data_type_slug(self) -> str:
        return f"{self.variable.name}_{self.year_range[0]}_{self.year_range[1]}_{self.resolution_input.value}".lower().replace(
            ".", "_"
        )

    @property
    def contour_config(self) -> ContourPlotConfig:
        return CLIMATE_CONTOUR_CONFIGS[self.variable_type]

    @property
    def target_resolution_raster(self) -> int | None:
        """Target maximum number of pixels to reduce memory usage for contour maps"""
        from climatemaps.gdal import GdalCalculator

        world_width_minutes = 360 * 60
        world_height_minutes = 180 * 60
        width, height = GdalCalculator.calculate_min_resolution_for_zoom_level(
            self.TARGET_ZOOM_LEVEL,
            aspect_ratio_width=world_width_minutes,
            aspect_ratio_height=world_height_minutes,
        )
        return width * height

    @property
    def target_resolution_vector(self) -> int:
        """Target maximum number of pixels for vector contour downsampling"""
        return 25_000_000

    @property
    def resolution_effective(self) -> float:
        """Calculate the effective spatial resolution in minutes after potential downsampling.

        Returns the original resolution if no downsampling would occur, otherwise
        calculates the coarser resolution that results from downsampling.
        """
        # Calculate original grid size
        resolution_minutes = float(self.resolution_input.value.rstrip("m"))
        world_width_minutes = 360 * 60
        world_height_minutes = 180 * 60
        width_pixels = int(world_width_minutes / resolution_minutes)
        height_pixels = int(world_height_minutes / resolution_minutes)
        original_size = width_pixels * height_pixels

        # Check if downsampling would occur
        if self.target_resolution_raster is None or original_size <= self.target_resolution_raster:
            return resolution_minutes

        # Calculate downsample factor (same logic as in load_climate_data)
        downsample_factor = float(np.sqrt(original_size / self.target_resolution_raster))

        # Calculate new resolution after downsampling
        return resolution_minutes * downsample_factor

    def get_climate_model(self) -> Optional[ClimateModel]:
        return None

    def get_variable_type(self) -> ClimateVarKey:
        return self.variable_type

    def get_climate_scenario(self) -> Optional[ClimateScenario]:
        return None

    def get_year_range(self) -> Tuple[int, int]:
        return self.year_range


@dataclass
class FutureClimateDataConfig(ClimateDataConfig):
    climate_scenario: ClimateScenario = field(default=None)
    climate_model: ClimateModel = field(default=None)

    @property
    def data_type_slug(self) -> str:
        base_slug = super().data_type_slug
        return f"{base_slug}_{self.climate_scenario.name}_{self.climate_model.name}".lower()

    def get_climate_model(self) -> Optional[ClimateModel]:
        return self.climate_model

    def get_climate_scenario(self) -> Optional[ClimateScenario]:
        return self.climate_scenario


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
            return f"difference_{self.variable.name}_{self.historical_config.year_range[0]}_{self.historical_config.year_range[1]}_to_{self.future_config.year_range[0]}_{self.future_config.year_range[1]}_{self.resolution_input.value}_{self.future_config.climate_scenario.name}_{self.future_config.climate_model.name}".lower().replace(
                ".", "_"
            )
        return super().data_type_slug

    @property
    def contour_config(self) -> ContourPlotConfig:
        if self.future_config and self.future_config.climate_model == ClimateModel.ENSEMBLE_STD_DEV:
            return CLIMATE_DIFFERENCE_CONTOUR_CONFIGS_STD_DEV[self.variable_type]
        return CLIMATE_DIFFERENCE_CONTOUR_CONFIGS[self.variable_type]

    def get_climate_model(self) -> Optional[ClimateModel]:
        if self.future_config:
            return self.future_config.climate_model
        return None

    def get_variable_type(self) -> ClimateVarKey:
        if self.future_config:
            return self.future_config.variable_type
        return self.variable_type

    def get_climate_scenario(self) -> Optional[ClimateScenario]:
        if self.future_config:
            return self.future_config.climate_scenario
        return None

    def get_year_range(self) -> Tuple[int, int]:
        if self.future_config:
            return self.future_config.year_range
        return self.year_range


def calculate_apparent_temperature(
    temp_max: npt.NDArray[np.floating],
    relative_humidity: npt.NDArray[np.floating],
    wind_speed: npt.NDArray[np.floating],
) -> npt.NDArray[np.floating]:
    """
    Calculate the Apparent Temperature (AT) using the Australian Bureau of Meteorology formula.

    AT = Ta + 0.33 × e - 0.70 × ws - 4.00

    Where:
    - Ta = dry bulb temperature (°C)
    - e = water vapor pressure (hPa)
    - ws = wind speed (m/s) at 10m height

    The vapor pressure is calculated from relative humidity and temperature:
    e = (rh/100) × 6.105 × exp(17.27 × Ta / (237.7 + Ta))

    This formula accounts for both:
    - Heat stress at high temperatures (humidity makes it feel hotter)
    - Wind chill at all temperatures (wind makes it feel cooler)
    """
    rh_fraction = relative_humidity / 100.0
    vapor_pressure = rh_fraction * 6.105 * np.exp((17.27 * temp_max) / (237.7 + temp_max))
    apparent_temp = temp_max + 0.33 * vapor_pressure - 0.70 * wind_speed - 4.00
    return apparent_temp


@dataclass
class DerivedClimateDataConfig(ClimateDataConfig):
    source_configs: Dict[ClimateVarKey, ClimateDataConfig] = field(default_factory=dict)
    compute_function: Callable[..., npt.NDArray[np.floating]] = None
    needs_lat_and_month: bool = False
    needs_terrain: bool = False

    @property
    def data_type_slug(self) -> str:
        return f"{self.variable.name}_{self.year_range[0]}_{self.year_range[1]}_{self.resolution_input.value}".lower().replace(
            ".", "_"
        )

    @property
    def contour_config(self) -> ContourPlotConfig:
        return CLIMATE_CONTOUR_CONFIGS[self.variable_type]


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
                        resolution_input=resolution,
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
                                resolution_input=resolution,
                                year_range=year_range,
                                climate_scenario=climate_scenario,
                                climate_model=climate_model,
                                filepath=self.filepath_template.format(
                                    resolution=resolution.value,
                                    year_range=year_range,
                                    variable_name=CLIMATE_VARIABLES[variable_type].filename.lower(),
                                    climate_scenario=climate_scenario.name.lower(),
                                    climate_model=climate_model.filename,
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
    ClimateVarKey.VAPOUR_PRESSURE_DEFICIT: "vpd",
    ClimateVarKey.T_MAX: "tmx",
    ClimateVarKey.T_MIN: "tmn",
    ClimateVarKey.PRECIPITATION: "pre",
}

CHELSA_FILE_ABBREVIATIONS: Dict[ClimateVarKey, str] = {
    ClimateVarKey.CLOUD_COVER: "clt",
    ClimateVarKey.T_MAX: "tasmax",
    ClimateVarKey.T_MIN: "tasmin",
    ClimateVarKey.PRECIPITATION: "pr",
    ClimateVarKey.WIND_SPEED: "sfcWind",
    ClimateVarKey.RELATIVE_HUMIDITY: "hurs",
    ClimateVarKey.POTENTIAL_EVAPOTRANSPIRATION: "pet",
    ClimateVarKey.RADIATION: "rsds",
    ClimateVarKey.MOISTURE_INDEX: "cmi",
    ClimateVarKey.VAPOUR_PRESSURE_DEFICIT: "vpd",
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
                        resolution_input=resolution,
                        year_range=year_range,
                        filepath=f"data/raw/cruts/cru_{abbr}_clim_{year_range[0]}-{year_range[1]}",
                        conversion_function=self.conversion_function,
                        conversion_factor=self.conversion_factor,
                        source=self.source,
                    )
                    configs.append(config)
        return configs


@dataclass
class CHELSAClimateDataConfigGroup(ClimateDataConfigGroup):
    def create_configs(self) -> List[ClimateDataConfig]:
        configs: List[ClimateDataConfig] = []
        for variable_type in self.variable_types:
            for year_range in self.year_ranges:
                for resolution in self.resolutions:
                    # CHELSA variables use different naming conventions
                    var_str = CHELSA_FILE_ABBREVIATIONS.get(variable_type)
                    if not var_str:
                        raise ValueError(f"Unsupported CHELSA variable: {variable_type}")

                    filepath = f"data/raw/chelsa/CHELSA_{var_str}_{year_range[0]}-{year_range[1]}"

                    # Different conversion factors for different variables
                    conversion_factors = {
                        ClimateVarKey.CLOUD_COVER: 0.01,
                        ClimateVarKey.T_MAX: 0.1,
                        ClimateVarKey.T_MIN: 0.1,
                        ClimateVarKey.PRECIPITATION: 0.1,
                        ClimateVarKey.WIND_SPEED: 0.001,
                        ClimateVarKey.RELATIVE_HUMIDITY: 0.01,
                        ClimateVarKey.RADIATION: 1.0,
                        ClimateVarKey.MOISTURE_INDEX: 0.1,
                        ClimateVarKey.POTENTIAL_EVAPOTRANSPIRATION: 0.1,
                        ClimateVarKey.VAPOUR_PRESSURE_DEFICIT: 0.1,
                    }

                    conversion_factor = conversion_factors.get(
                        variable_type, self.conversion_factor
                    )

                    # Use temperature conversion function for temperature variables
                    conversion_function = self.conversion_function
                    if variable_type in [ClimateVarKey.T_MAX, ClimateVarKey.T_MIN]:
                        conversion_function = chelsa_temperature_conversion

                    config = ClimateDataConfig(
                        variable_type=variable_type,
                        format=self.format,
                        resolution_input=resolution,
                        year_range=year_range,
                        filepath=filepath,
                        conversion_function=conversion_function,
                        conversion_factor=conversion_factor,
                        source=self.source,
                    )
                    configs.append(config)
        return configs


HISTORIC_DATA_GROUPS: List[ClimateDataConfigGroup] = [
    CHELSAClimateDataConfigGroup(
        variable_types=[
            ClimateVarKey.CLOUD_COVER,
            ClimateVarKey.T_MAX,
            ClimateVarKey.T_MIN,
            ClimateVarKey.PRECIPITATION,
            ClimateVarKey.WIND_SPEED,
            ClimateVarKey.RELATIVE_HUMIDITY,
            ClimateVarKey.RADIATION,
            ClimateVarKey.MOISTURE_INDEX,
            ClimateVarKey.POTENTIAL_EVAPOTRANSPIRATION,
            ClimateVarKey.VAPOUR_PRESSURE_DEFICIT,
        ],
        format=DataFormat.CHELSA,
        source="https://www.chelsa-climate.org/datasets/chelsa_climatologies",
        resolutions=[SpatialResolution.MIN0_5],
        year_ranges=[(1981, 2010)],
    ),
]


FUTURE_FILE_TEMPLATE = "data/raw/worldclim/future/wc2.1_{resolution}_{variable_name}_{climate_model}_{climate_scenario}_{year_range[0]}-{year_range[1]}.tif"
FUTURE_DATE_RANGES = [(2021, 2040), (2041, 2060), (2061, 2080), (2081, 2100)]

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
    ),
]

HISTORIC_DATA_SETS: List[ClimateDataConfig] = [
    cfg for data_group in HISTORIC_DATA_GROUPS for cfg in data_group.create_configs()
]


def create_apparent_temperature_configs() -> List[DerivedClimateDataConfig]:
    configs: List[DerivedClimateDataConfig] = []

    tmax_configs = [c for c in HISTORIC_DATA_SETS if c.variable_type == ClimateVarKey.T_MAX]
    rh_configs = [
        c for c in HISTORIC_DATA_SETS if c.variable_type == ClimateVarKey.RELATIVE_HUMIDITY
    ]
    wind_configs = [c for c in HISTORIC_DATA_SETS if c.variable_type == ClimateVarKey.WIND_SPEED]

    for tmax_cfg in tmax_configs:
        rh_cfg = next(
            (
                c
                for c in rh_configs
                if c.year_range == tmax_cfg.year_range
                and c.resolution_input == tmax_cfg.resolution_input
            ),
            None,
        )
        wind_cfg = next(
            (
                c
                for c in wind_configs
                if c.year_range == tmax_cfg.year_range
                and c.resolution_input == tmax_cfg.resolution_input
            ),
            None,
        )

        if rh_cfg and wind_cfg:
            config = DerivedClimateDataConfig(
                variable_type=ClimateVarKey.APPARENT_TEMPERATURE,
                filepath="",
                format=tmax_cfg.format,
                resolution_input=tmax_cfg.resolution_input,
                year_range=tmax_cfg.year_range,
                source=tmax_cfg.source,
                source_configs={
                    ClimateVarKey.T_MAX: tmax_cfg,
                    ClimateVarKey.RELATIVE_HUMIDITY: rh_cfg,
                    ClimateVarKey.WIND_SPEED: wind_cfg,
                },
                compute_function=calculate_apparent_temperature,
            )
            configs.append(config)

    return configs


def create_sunshine_hours_configs() -> List[DerivedClimateDataConfig]:
    configs: List[DerivedClimateDataConfig] = []

    radiation_configs = [
        c for c in HISTORIC_DATA_SETS if c.variable_type == ClimateVarKey.RADIATION
    ]

    for radiation_cfg in radiation_configs:
        config = DerivedClimateDataConfig(
            variable_type=ClimateVarKey.SUNSHINE_HOURS,
            filepath="",
            format=radiation_cfg.format,
            resolution_input=radiation_cfg.resolution_input,
            year_range=radiation_cfg.year_range,
            source=radiation_cfg.source,
            source_configs={
                ClimateVarKey.RADIATION: radiation_cfg,
            },
            compute_function=calculate_sunshine_hours,
            needs_lat_and_month=True,
            needs_terrain=True,
        )
        configs.append(config)

    return configs


DERIVED_DATA_SETS: List[DerivedClimateDataConfig] = (
    create_apparent_temperature_configs() + create_sunshine_hours_configs()
)
HISTORIC_DATA_SETS = HISTORIC_DATA_SETS + DERIVED_DATA_SETS

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
                and hist_config.resolution_input == future_config.resolution_input
            ):
                historical_config = hist_config
                break

        if historical_config:
            diff_config = ClimateDifferenceDataConfig(
                variable_type=future_config.variable_type,
                filepath="",  # Not used for difference maps
                format=future_config.format,
                resolution_input=future_config.resolution_input,
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
