import enum
from dataclasses import dataclass
from typing import Optional

import matplotlib.pyplot as plt

import climatemaps


class DataFormat(enum.Enum):
    GEOTIFF_WORLDCLIM_CMIP6 = 0
    GEOTIFF_WORLDCLIM_HISTORY = 1
    IPCC_GRID = 2


class DataType(enum.Enum):
    model_precipitation_5m_2021_2040 = 0
    model_precipitation_10m_2021_2040 = 1


@dataclass
class ContourConfig:
    data_type: str
    filepath: str
    config: climatemaps.contour.ContourPlotConfig
    format: DataFormat
    conversion_factor: float = 1.0
    source: Optional[str] = None


CLIMATE_MODEL_DATA_SETS = [
    ContourConfig(
        data_type='model_precipitation_10m_2021_2040',
        filepath='data/climate_models/wc2.1_10m_prec_ACCESS-CM2_ssp126_2021-2040.tif',
        conversion_factor=1/30,  # value is per month, convert to day
        config=climatemaps.contour.ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source='https://www.worldclim.org/data/cmip6/cmip6_clim10m.html'
    ),
    ContourConfig(
        data_type='model_precipitation_5m_2021_2040',
        filepath='data/climate_models/wc2.1_5m_prec_ACCESS-CM2_ssp126_2021-2040.tif',
        conversion_factor=1/30,  # value is per month, convert to day
        config=climatemaps.contour.ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source='https://www.worldclim.org/data/cmip6/cmip6_clim5m.html'
    ),
    ContourConfig(
        data_type='model_precipitation_5m_ssp585_2021_2040',
        filepath='data/climate_models/wc2.1_5m_prec_ACCESS-CM2_ssp585_2021-2040.tif',
        conversion_factor=1/30,  # value is per month, convert to day
        config=climatemaps.contour.ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source='https://www.worldclim.org/data/cmip6/cmip6_clim5m.html'
    ),
    ContourConfig(
        data_type='model_precipitation_5m_ssp585_2081_2100',
        filepath='data/climate_models/wc2.1_5m_prec_ACCESS-CM2_ssp585_2081-2100.tif',
        conversion_factor=1/30,  # value is per month, convert to day
        config=climatemaps.contour.ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source='https://www.worldclim.org/data/cmip6/cmip6_clim5m.html'
    ),
    ContourConfig(
        data_type='model_precipitation_5m_2041_2060',
        filepath='data/climate_models/wc2.1_5m_prec_ACCESS-CM2_ssp126_2041-2060.tif',
        conversion_factor=1/30,  # value is per month, convert to day
        config=climatemaps.contour.ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source='https://www.worldclim.org/data/cmip6/cmip6_clim5m.html'
    )
]

HISTORIC_DATA_SETS = [
    ContourConfig(
        data_type='precipitation_worldclim_2.5m',
        filepath='data/worldclim/history/wc2.1_2.5m_prec',
        conversion_factor=1/30,  # value is per month, convert to day
        config=climatemaps.contour.ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
        format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
        source="https://www.worldclim.org/data/worldclim21.html"
    ),
    ContourConfig(
        data_type='precipitation_worldclim_5m',
        filepath='data/worldclim/history/wc2.1_5m_prec',
        conversion_factor=1/30,  # value is per month, convert to day
        config=climatemaps.contour.ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
        format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
        source="https://www.worldclim.org/data/worldclim21.html"
    ),
    ContourConfig(
        data_type='precipitation_worldclim_10m',
        filepath='data/worldclim/history/wc2.1_10m_prec',
        conversion_factor=1/30,  # value is per month, convert to day
        config=climatemaps.contour.ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
        format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
        source="https://www.worldclim.org/data/worldclim21.html"
    ),
    ContourConfig(
        data_type='temperature_max_worldclim_10m',
        filepath='data/worldclim/history/wc2.1_10m_tmax',
        # conversion_factor=1
        config=climatemaps.contour.ContourPlotConfig(-20, 45, colormap=plt.cm.jet, title='Max. temperature', unit='C'),
        format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
        source="https://www.worldclim.org/data/worldclim21.html"
    ),
    ContourConfig(
        data_type='precipitation',
        filepath='data/precipitation/cpre6190.dat',
        conversion_factor=0.1,  # (millimetres/day) *10
        config=climatemaps.contour.ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
        format=DataFormat.IPCC_GRID
    ),
    ContourConfig(
        data_type='cloud',
        filepath='data/cloud/ccld6190.dat',
        conversion_factor=1,
        config=climatemaps.contour.ContourPlotConfig(0, 100, colormap=plt.cm.jet_r, title='Cloud coverage', unit='%'),
        format=DataFormat.IPCC_GRID
    ),
    ContourConfig(
        data_type='mintemp',
        filepath='data/mintemp/ctmn6190.dat',
        conversion_factor=0.1,
        config=climatemaps.contour.ContourPlotConfig(-30, 28, colormap=plt.cm.jet, title='Min. temperature', unit='C'),
        format=DataFormat.IPCC_GRID
    ),
    ContourConfig(
        data_type='meantemp',
        filepath='data/meantemp/ctmp6190.dat',
        conversion_factor=0.1,
        config=climatemaps.contour.ContourPlotConfig(-30, 35, colormap=plt.cm.jet, title='Mean temperature', unit='C'),
        format=DataFormat.IPCC_GRID
    ),
    ContourConfig(
        data_type='maxtemp',
        filepath='data/maxtemp/ctmx6190.dat',
        conversion_factor=0.1,
        config=climatemaps.contour.ContourPlotConfig(-20, 45, colormap=plt.cm.jet, title='Max. temperature', unit='C'),
        format=DataFormat.IPCC_GRID
    ),
    ContourConfig(
        data_type='diurnaltemprange',
        filepath='data/diurnaltemprange/cdtr6190.dat',
        conversion_factor=0.1,
        config=climatemaps.contour.ContourPlotConfig(5, 20, colormap=plt.cm.jet, title='Diurnal temperature range', unit='C'),
        format=DataFormat.IPCC_GRID
    ),
    ContourConfig(
        data_type='wetdays',
        filepath='data/wetdays/cwet6190.dat',
        conversion_factor=0.1,
        config=climatemaps.contour.ContourPlotConfig(0, 30, colormap=plt.cm.jet_r, title='Wet days', unit='days'),
        format=DataFormat.IPCC_GRID
    ),
    ContourConfig(
        data_type='wind',
        filepath='data/wind/cwnd6190.dat',
        conversion_factor=0.1,
        config=climatemaps.contour.ContourPlotConfig(0, 9, colormap=plt.cm.jet, title='Wind speed', unit='m/s'),
        format=DataFormat.IPCC_GRID
    ),
    ContourConfig(
        data_type='radiation',
        filepath='data/radiation/crad6190.dat',
        conversion_factor=1,
        config=climatemaps.contour.ContourPlotConfig(0, 300, colormap=plt.cm.jet, title='Radiation', unit='W/m^2'),
        format=DataFormat.IPCC_GRID
    ),
    ContourConfig(
        data_type='vapourpressure',
        filepath='data/vapourpressure/cvap6190.dat',
        conversion_factor=0.1,
        config=climatemaps.contour.ContourPlotConfig(1, 34, colormap=plt.cm.jet, title='Vapour pressure', unit='hPa'),
        format=DataFormat.IPCC_GRID
    ),
]
