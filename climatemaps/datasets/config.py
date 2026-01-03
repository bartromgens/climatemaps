from typing import Dict

import matplotlib.pyplot as plt
from pydantic import BaseModel

from climatemaps.contour_config import ContourPlotConfig
from climatemaps.datasets.enums import ClimateVarKey


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
}


CLIMATE_CONTOUR_CONFIGS: Dict[ClimateVarKey, ContourPlotConfig] = {
    ClimateVarKey.PRECIPITATION: ContourPlotConfig(
        level_lower=5,
        level_upper=400,
        colormap=plt.cm.RdYlBu,
        title="Precipitation",
        unit="mm/month",
        log_scale=True,
        n_contours=11,
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
        level_lower=50,
        level_upper=350,
        colormap=plt.cm.RdYlBu_r,
        title="Potential Evapotranspiration",
        unit="mm/month",
        n_contours=8,
    ),
}


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
