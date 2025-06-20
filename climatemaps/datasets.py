import enum
from dataclasses import dataclass
from typing import Optional
from typing import Tuple

import matplotlib.pyplot as plt
from pydantic import BaseModel

import climatemaps


class DataFormat(enum.Enum):
    GEOTIFF_WORLDCLIM_CMIP6 = 0
    GEOTIFF_WORLDCLIM_HISTORY = 1
    IPCC_GRID = 2


class ClimateVariable(BaseModel):
    name: str
    display_name: str
    unit: str


precipitation = ClimateVariable(name="Precipitation", display_name="Precipitation", unit="mm/day")
temperature_max = ClimateVariable(name="Tmax", display_name="Temperature Max", unit="C")


@dataclass
class ClimateDataSetConfig:
    data_type: str
    filepath: str
    variable: ClimateVariable
    year_range: Tuple[int, int]
    resolution: float  # minutes
    contour_config: climatemaps.contour.ContourPlotConfig
    format: DataFormat
    conversion_factor: float = 1.0
    source: Optional[str] = None


CLIMATE_MODEL_DATA_SETS = [
    ClimateDataSetConfig(
        data_type="model_precipitation_10m_2021_2040",
        filepath="data/climate_models/wc2.1_10m_prec_ACCESS-CM2_ssp126_2021-2040.tif",
        variable=precipitation,
        year_range=(2021, 2040),
        resolution=10,
        conversion_factor=1 / 30,  # value is per month, convert to day
        contour_config=climatemaps.contour.ContourPlotConfig(
            0.1, 16, colormap=plt.cm.jet_r, title="Precipitation", unit="mm/day", logscale=True
        ),
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source="https://www.worldclim.org/data/cmip6/cmip6_clim10m.html",
    ),
    ClimateDataSetConfig(
        data_type="model_precipitation_5m_2021_2040",
        filepath="data/climate_models/wc2.1_5m_prec_ACCESS-CM2_ssp126_2021-2040.tif",
        variable=precipitation,
        year_range=(2021, 2040),
        resolution=5,
        conversion_factor=1 / 30,  # value is per month, convert to day
        contour_config=climatemaps.contour.ContourPlotConfig(
            0.1, 16, colormap=plt.cm.jet_r, title="Precipitation", unit="mm/day", logscale=True
        ),
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source="https://www.worldclim.org/data/cmip6/cmip6_clim5m.html",
    ),
    ClimateDataSetConfig(
        data_type="model_precipitation_5m_ssp585_2021_2040",
        filepath="data/climate_models/wc2.1_5m_prec_ACCESS-CM2_ssp585_2021-2040.tif",
        variable=precipitation,
        year_range=(2021, 2040),
        resolution=5,
        conversion_factor=1 / 30,  # value is per month, convert to day
        contour_config=climatemaps.contour.ContourPlotConfig(
            0.1, 16, colormap=plt.cm.jet_r, title="Precipitation", unit="mm/day", logscale=True
        ),
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source="https://www.worldclim.org/data/cmip6/cmip6_clim5m.html",
    ),
    ClimateDataSetConfig(
        data_type="model_precipitation_5m_ssp585_2081_2100",
        filepath="data/climate_models/wc2.1_5m_prec_ACCESS-CM2_ssp585_2081-2100.tif",
        variable=precipitation,
        year_range=(2081, 2100),
        resolution=5,
        conversion_factor=1 / 30,  # value is per month, convert to day
        contour_config=climatemaps.contour.ContourPlotConfig(
            0.1, 16, colormap=plt.cm.jet_r, title="Precipitation", unit="mm/day", logscale=True
        ),
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source="https://www.worldclim.org/data/cmip6/cmip6_clim5m.html",
    ),
    ClimateDataSetConfig(
        data_type="model_precipitation_5m_2041_2060",
        filepath="data/climate_models/wc2.1_5m_prec_ACCESS-CM2_ssp126_2041-2060.tif",
        variable=precipitation,
        year_range=(2040, 2060),
        resolution=5,
        conversion_factor=1 / 30,  # value is per month, convert to day
        contour_config=climatemaps.contour.ContourPlotConfig(
            0.1, 16, colormap=plt.cm.jet_r, title="Precipitation", unit="mm/day", logscale=True
        ),
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
    #     resolution=2.5,
    #     conversion_factor=1/30,  # value is per month, convert to day
    #     config=climatemaps.contour.ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
    #     format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
    #     source="https://www.worldclim.org/data/worldclim21.html"
    # ),
    # ClimateMapConfig(
    #     data_type='precipitation_worldclim_5m',
    #     filepath='data/worldclim/history/wc2.1_5m_prec',
    #     variable=precipitation,
    #     year_range=(1970, 2000),
    #     resolution=5,
    #     conversion_factor=1/30,  # value is per month, convert to day
    #     config=climatemaps.contour.ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
    #     format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
    #     source="https://www.worldclim.org/data/worldclim21.html"
    # ),
    # ClimateMapConfig(
    #     data_type='precipitation_worldclim_10m',
    #     filepath='data/worldclim/history/wc2.1_10m_prec',
    #     variable=precipitation,
    #     year_range=(1970, 2000),
    #     resolution=10,
    #     conversion_factor=1/30,  # value is per month, convert to day
    #     config=climatemaps.contour.ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
    #     format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
    #     source="https://www.worldclim.org/data/worldclim21.html"
    # ),
    ClimateDataSetConfig(
        data_type="temperature_max_worldclim_10m",
        filepath="data/worldclim/history/wc2.1_10m_tmax",
        variable=temperature_max,
        year_range=(1970, 2000),
        resolution=10,
        # conversion_factor=1
        contour_config=climatemaps.contour.ContourPlotConfig(
            -20, 45, colormap=plt.cm.jet, title="Max. temperature", unit="C"
        ),
        format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
        source="https://www.worldclim.org/data/worldclim21.html",
    ),
    ClimateDataSetConfig(
        data_type="temperature_max_worldclim_5m",
        filepath="data/worldclim/history/wc2.1_5m_tmax",
        variable=temperature_max,
        year_range=(1970, 2000),
        resolution=5,
        # conversion_factor=1
        contour_config=climatemaps.contour.ContourPlotConfig(
            -20, 45, colormap=plt.cm.jet, title="Max. temperature", unit="C"
        ),
        format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
        source="https://www.worldclim.org/data/worldclim21.html",
    ),
    # ClimateMapConfig(
    #     data_type='temperature_max_worldclim_2.5m',
    #     filepath='data/worldclim/history/wc2.1_2.5m_tmax',
    #     variable=temperature_max,
    #     year_range=(1970, 2000),
    #     resolution=2.5,
    #     config=climatemaps.contour.ContourPlotConfig(-20, 45, colormap=plt.cm.jet, title='Max. temperature', unit='C'),
    #     format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
    #     source="https://www.worldclim.org/data/worldclim21.html"
    # ),
    # ClimateMapConfig(
    #     data_type='precipitation',
    #     filepath='data/precipitation/cpre6190.dat',
    #     conversion_factor=0.1,  # (millimetres/day) *10
    #     config=climatemaps.contour.ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
    #     format=DataFormat.IPCC_GRID
    # ),
    # ClimateMapConfig(
    #     data_type='cloud',
    #     filepath='data/cloud/ccld6190.dat',
    #     conversion_factor=1,
    #     config=climatemaps.contour.ContourPlotConfig(0, 100, colormap=plt.cm.jet_r, title='Cloud coverage', unit='%'),
    #     format=DataFormat.IPCC_GRID
    # ),
    # ClimateMapConfig(
    #     data_type='mintemp',
    #     filepath='data/mintemp/ctmn6190.dat',
    #     conversion_factor=0.1,
    #     config=climatemaps.contour.ContourPlotConfig(-30, 28, colormap=plt.cm.jet, title='Min. temperature', unit='C'),
    #     format=DataFormat.IPCC_GRID
    # ),
    # ClimateMapConfig(
    #     data_type='meantemp',
    #     filepath='data/meantemp/ctmp6190.dat',
    #     conversion_factor=0.1,
    #     config=climatemaps.contour.ContourPlotConfig(-30, 35, colormap=plt.cm.jet, title='Mean temperature', unit='C'),
    #     format=DataFormat.IPCC_GRID
    # ),
    # ClimateMapConfig(
    #     data_type='maxtemp',
    #     filepath='data/maxtemp/ctmx6190.dat',
    #     conversion_factor=0.1,
    #     config=climatemaps.contour.ContourPlotConfig(-20, 45, colormap=plt.cm.jet, title='Max. temperature', unit='C'),
    #     format=DataFormat.IPCC_GRID
    # ),
    # ClimateMapConfig(
    #     data_type='diurnaltemprange',
    #     filepath='data/diurnaltemprange/cdtr6190.dat',
    #     conversion_factor=0.1,
    #     config=climatemaps.contour.ContourPlotConfig(5, 20, colormap=plt.cm.jet, title='Diurnal temperature range', unit='C'),
    #     format=DataFormat.IPCC_GRID
    # ),
    # ClimateMapConfig(
    #     data_type='wetdays',
    #     filepath='data/wetdays/cwet6190.dat',
    #     conversion_factor=0.1,
    #     config=climatemaps.contour.ContourPlotConfig(0, 30, colormap=plt.cm.jet_r, title='Wet days', unit='days'),
    #     format=DataFormat.IPCC_GRID
    # ),
    # ClimateMapConfig(
    #     data_type='wind',
    #     filepath='data/wind/cwnd6190.dat',
    #     conversion_factor=0.1,
    #     config=climatemaps.contour.ContourPlotConfig(0, 9, colormap=plt.cm.jet, title='Wind speed', unit='m/s'),
    #     format=DataFormat.IPCC_GRID
    # ),
    # ClimateMapConfig(
    #     data_type='radiation',
    #     filepath='data/radiation/crad6190.dat',
    #     conversion_factor=1,
    #     config=climatemaps.contour.ContourPlotConfig(0, 300, colormap=plt.cm.jet, title='Radiation', unit='W/m^2'),
    #     format=DataFormat.IPCC_GRID
    # ),
    # ClimateMapConfig(
    #     data_type='vapourpressure',
    #     filepath='data/vapourpressure/cvap6190.dat',
    #     conversion_factor=0.1,
    #     config=climatemaps.contour.ContourPlotConfig(1, 34, colormap=plt.cm.jet, title='Vapour pressure', unit='hPa'),
    #     format=DataFormat.IPCC_GRID
    # ),
]
