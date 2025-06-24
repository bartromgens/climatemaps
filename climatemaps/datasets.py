import enum
from dataclasses import dataclass
from typing import Dict
from typing import Optional
from typing import Tuple

import matplotlib.pyplot as plt
from pydantic import BaseModel

from climatemaps.contour_config import ContourPlotConfig


class DataFormat(enum.Enum):
    GEOTIFF_WORLDCLIM_CMIP6 = enum.auto()
    GEOTIFF_WORLDCLIM_HISTORY = enum.auto()
    IPCC_GRID = enum.auto()


class SpatialResolution(enum.Enum):
    MIN10 = "10min"
    MIN5 = "5min"
    MIN2_5 = "2.5min"


class ClimateVarKey(enum.Enum):
    PRECIPITATION = enum.auto()
    T_MAX = enum.auto()


class ClimateVariable(BaseModel):
    name: str
    display_name: str
    unit: str


CLIMATE_VARIABLES: Dict[ClimateVarKey, ClimateVariable] = {
    ClimateVarKey.PRECIPITATION: ClimateVariable(
        name="Precipitation", display_name="Precipitation", unit="mm/day"
    ),
    ClimateVarKey.T_MAX: ClimateVariable(name="Tmax", display_name="Temperature Max", unit="°C"),
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
}


@dataclass
class ClimateDataSetConfig:
    variable_type: ClimateVarKey.PRECIPITATION
    filepath: str
    year_range: Tuple[int, int]
    resolution: SpatialResolution
    format: DataFormat
    conversion_factor: float = 1.0
    source: Optional[str] = None

    @property
    def variable(self) -> ClimateVariable:
        return CLIMATE_VARIABLES[self.variable_type]

    @property
    def data_type(self) -> str:
        return f"{self.variable.name}_{self.year_range[0]}_{self.year_range[1]}_{self.resolution.value}".lower().replace(
            ".", "_"
        )

    @property
    def contour_config(self) -> ContourPlotConfig:
        return CLIMATE_CONTOUR_CONFIGS[self.variable_type]


CLIMATE_MODEL_DATA_SETS = [
    ClimateDataSetConfig(
        variable_type=ClimateVarKey.PRECIPITATION,
        filepath="data/climate_models/wc2.1_10m_prec_ACCESS-CM2_ssp126_2021-2040.tif",
        year_range=(2021, 2040),
        resolution=SpatialResolution.MIN10,
        conversion_factor=1 / 30,  # value is per month, convert to day
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source="https://www.worldclim.org/data/cmip6/cmip6_clim10m.html",
    ),
    ClimateDataSetConfig(
        variable_type=ClimateVarKey.PRECIPITATION,
        filepath="data/climate_models/wc2.1_5m_prec_ACCESS-CM2_ssp126_2021-2040.tif",
        year_range=(2021, 2040),
        resolution=SpatialResolution.MIN5,
        conversion_factor=1 / 30,  # value is per month, convert to day
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source="https://www.worldclim.org/data/cmip6/cmip6_clim5m.html",
    ),
    ClimateDataSetConfig(
        variable_type=ClimateVarKey.PRECIPITATION,
        filepath="data/climate_models/wc2.1_5m_prec_ACCESS-CM2_ssp585_2021-2040.tif",
        year_range=(2021, 2040),
        resolution=SpatialResolution.MIN5,
        conversion_factor=1 / 30,  # value is per month, convert to day
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source="https://www.worldclim.org/data/cmip6/cmip6_clim5m.html",
    ),
    ClimateDataSetConfig(
        variable_type=ClimateVarKey.PRECIPITATION,
        filepath="data/climate_models/wc2.1_5m_prec_ACCESS-CM2_ssp585_2081-2100.tif",
        year_range=(2081, 2100),
        resolution=SpatialResolution.MIN5,
        conversion_factor=1 / 30,  # value is per month, convert to day
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source="https://www.worldclim.org/data/cmip6/cmip6_clim5m.html",
    ),
    ClimateDataSetConfig(
        variable_type=ClimateVarKey.PRECIPITATION,
        filepath="data/climate_models/wc2.1_5m_prec_ACCESS-CM2_ssp126_2041-2060.tif",
        year_range=(2040, 2060),
        resolution=SpatialResolution.MIN5,
        conversion_factor=1 / 30,  # value is per month, convert to day
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source="https://www.worldclim.org/data/cmip6/cmip6_clim5m.html",
    ),
]

HISTORIC_DATA_SETS = [
    # ClimateMapConfig(
    #     data_type='precipitation_worldclim_2.5m',
    #     filepath='data/worldclim/history/wc2.1_2.5m_prec',
    #     variable=precipitation,
    #     year_range=(1970, 2000),
    #     resolution=Resolution.MIN2_5,
    #     conversion_factor=1/30,  # value is per month, convert to day
    #     config=ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
    #     format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
    #     source="https://www.worldclim.org/data/worldclim21.html"
    # ),
    # ClimateMapConfig(
    #     data_type='precipitation_worldclim_5m',
    #     filepath='data/worldclim/history/wc2.1_5m_prec',
    #     variable=precipitation,
    #     year_range=(1970, 2000),
    #     resolution=Resolution.MIN5,
    #     conversion_factor=1/30,  # value is per month, convert to day
    #     config=ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
    #     format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
    #     source="https://www.worldclim.org/data/worldclim21.html"
    # ),
    # ClimateMapConfig(
    #     data_type='precipitation_worldclim_10m',
    #     filepath='data/worldclim/history/wc2.1_10m_prec',
    #     variable=precipitation,
    #     year_range=(1970, 2000),
    #     resolution=Resolution.MIN10,
    #     conversion_factor=1/30,  # value is per month, convert to day
    #     config=ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
    #     format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
    #     source="https://www.worldclim.org/data/worldclim21.html"
    # ),
    ClimateDataSetConfig(
        variable_type=ClimateVarKey.T_MAX,
        filepath="data/worldclim/history/wc2.1_10m_tmax",
        year_range=(1970, 2000),
        resolution=SpatialResolution.MIN10,
        # conversion_factor=1
        format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
        source="https://www.worldclim.org/data/worldclim21.html",
    ),
    ClimateDataSetConfig(
        variable_type=ClimateVarKey.T_MAX,
        filepath="data/worldclim/history/wc2.1_5m_tmax",
        year_range=(1970, 2000),
        resolution=SpatialResolution.MIN5,
        # conversion_factor=1
        format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
        source="https://www.worldclim.org/data/worldclim21.html",
    ),
    # ClimateMapConfig(
    #     data_type='temperature_max_worldclim_2.5m',
    #     filepath='data/worldclim/history/wc2.1_2.5m_tmax',
    #     variable=temperature_max,
    #     year_range=(1970, 2000),
    #     resolution=Resolution.MIN2_5,
    #     config=ContourPlotConfig(-20, 45, colormap=plt.cm.jet, title='Max. temperature', unit='C'),
    #     format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
    #     source="https://www.worldclim.org/data/worldclim21.html"
    # ),
    # ClimateMapConfig(
    #     data_type='precipitation',
    #     filepath='data/precipitation/cpre6190.dat',
    #     conversion_factor=0.1,  # (millimetres/day) *10
    #     config=ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
    #     format=DataFormat.IPCC_GRID
    # ),
    # ClimateMapConfig(
    #     data_type='cloud',
    #     filepath='data/cloud/ccld6190.dat',
    #     conversion_factor=1,
    #     config=ContourPlotConfig(0, 100, colormap=plt.cm.jet_r, title='Cloud coverage', unit='%'),
    #     format=DataFormat.IPCC_GRID
    # ),
    # ClimateMapConfig(
    #     data_type='mintemp',
    #     filepath='data/mintemp/ctmn6190.dat',
    #     conversion_factor=0.1,
    #     config=ContourPlotConfig(-30, 28, colormap=plt.cm.jet, title='Min. temperature', unit='C'),
    #     format=DataFormat.IPCC_GRID
    # ),
    # ClimateMapConfig(
    #     data_type='meantemp',
    #     filepath='data/meantemp/ctmp6190.dat',
    #     conversion_factor=0.1,
    #     config=ContourPlotConfig(-30, 35, colormap=plt.cm.jet, title='Mean temperature', unit='C'),
    #     format=DataFormat.IPCC_GRID
    # ),
    # ClimateMapConfig(
    #     data_type='maxtemp',
    #     filepath='data/maxtemp/ctmx6190.dat',
    #     conversion_factor=0.1,
    #     config=ContourPlotConfig(-20, 45, colormap=plt.cm.jet, title='Max. temperature', unit='C'),
    #     format=DataFormat.IPCC_GRID
    # ),
    # ClimateMapConfig(
    #     data_type='diurnaltemprange',
    #     filepath='data/diurnaltemprange/cdtr6190.dat',
    #     conversion_factor=0.1,
    #     config=ContourPlotConfig(5, 20, colormap=plt.cm.jet, title='Diurnal temperature range', unit='C'),
    #     format=DataFormat.IPCC_GRID
    # ),
    # ClimateMapConfig(
    #     data_type='wetdays',
    #     filepath='data/wetdays/cwet6190.dat',
    #     conversion_factor=0.1,
    #     config=ContourPlotConfig(0, 30, colormap=plt.cm.jet_r, title='Wet days', unit='days'),
    #     format=DataFormat.IPCC_GRID
    # ),
    # ClimateMapConfig(
    #     data_type='wind',
    #     filepath='data/wind/cwnd6190.dat',
    #     conversion_factor=0.1,
    #     config=ContourPlotConfig(0, 9, colormap=plt.cm.jet, title='Wind speed', unit='m/s'),
    #     format=DataFormat.IPCC_GRID
    # ),
    # ClimateMapConfig(
    #     data_type='radiation',
    #     filepath='data/radiation/crad6190.dat',
    #     conversion_factor=1,
    #     config=ContourPlotConfig(0, 300, colormap=plt.cm.jet, title='Radiation', unit='W/m^2'),
    #     format=DataFormat.IPCC_GRID
    # ),
    # ClimateMapConfig(
    #     data_type='vapourpressure',
    #     filepath='data/vapourpressure/cvap6190.dat',
    #     conversion_factor=0.1,
    #     config=ContourPlotConfig(1, 34, colormap=plt.cm.jet, title='Vapour pressure', unit='hPa'),
    #     format=DataFormat.IPCC_GRID
    # ),
]
