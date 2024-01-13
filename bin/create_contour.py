#!/usr/bin/env python3
import enum
import sys
from dataclasses import dataclass
from typing import Optional

import matplotlib.pyplot as plt

sys.path.append('../climatemaps')

import climatemaps
from climatemaps.logger import logger

DATA_OUT_DIR = 'website/data'


class DataFormat(enum.Enum):
    GEOTIFF = 0
    IPCC_GRID = 1


@dataclass
class ContourConfig:
    data_type: str
    filepath: str
    config: climatemaps.contour.ContourPlotConfig
    format: DataFormat
    conversion_factor: float = 1.0
    source: Optional[str] = None


DEV_MODE = True

ZOOM_MIN = 1
ZOOM_MAX = 4 if DEV_MODE else 10
# ZOOM_FACTOR = None if DEV_MODE else 2.0
ZOOM_FACTOR = 2.0
# CREATE_IMAGES = not DEV_MODE
CREATE_IMAGES = True

CLIMATE_MODEL_DATA_SETS = [
    ContourConfig(
        data_type='model_precipitation',
        filepath='data/climate_models/wc2.1_10m_prec_ACCESS-CM2_ssp126_2021-2040.tif',
        conversion_factor=1/30,  # value is per month, convert to day
        config=climatemaps.contour.ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
        format=DataFormat.GEOTIFF,
        source='https://www.worldclim.org/data/cmip6/cmip6_clim10m.html'
    ),
    ContourConfig(
        data_type='model_precipitation_5m',
        filepath='data/climate_models/wc2.1_5m_prec_ACCESS-CM2_ssp126_2021-2040.tif',
        conversion_factor=1/30,  # value is per month, convert to day
        config=climatemaps.contour.ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
        format=DataFormat.GEOTIFF,
        source='https://www.worldclim.org/data/cmip6/cmip6_clim5m.html'
    ),
    ContourConfig(
        data_type='model_precipitation_5m_2041_2060',
        filepath='data/climate_models/wc2.1_5m_prec_ACCESS-CM2_ssp126_2041-2060.tif',
        conversion_factor=1/30,  # value is per month, convert to day
        config=climatemaps.contour.ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True),
        format=DataFormat.GEOTIFF,
        source='https://www.worldclim.org/data/cmip6/cmip6_clim5m.html'
    )
]

HISTORIC_DATA_SETS = [
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
        config=climatemaps.contour.ContourPlotConfig(-40, 28, colormap=plt.cm.jet, title='Min. temperature', unit='C'),
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
        config=climatemaps.contour.ContourPlotConfig(-20, 45, colormap=plt.cm.jet, title='Max. temperature', unit='C'),
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

CONTOUR_TYPES = CLIMATE_MODEL_DATA_SETS + HISTORIC_DATA_SETS


def main():
    month_upper = 1
    n_data_sets = len(CONTOUR_TYPES) * month_upper
    counter = 0
    for config in CONTOUR_TYPES:
        for month in range(1, month_upper+1):
            logger.info('create image and tiles for "' + config.data_type + '" and month ' + str(month))
            progress = counter/n_data_sets*100.0
            logger.info(f"progress: {(int(progress))} %")
            latrange, lonrange, Z = None, None, None
            if config.format == DataFormat.IPCC_GRID:
                latrange, lonrange, Z = climatemaps.data.import_climate_data(config.filepath, month)
            elif config.format == DataFormat.GEOTIFF:
                lonrange, latrange, Z = climatemaps.geotiff.read_geotiff_month(config.filepath, month-1)
                latrange = latrange*-1
            else:
                assert f'DataFormat {config.format} is not supported'
            Z = Z * config.conversion_factor
            logger.info(f"lon: {lonrange}")
            logger.info(f"lat: {latrange}")
            contourmap = climatemaps.contour.Contour(config.config, lonrange, latrange, Z, zoom_min=ZOOM_MIN, zoom_max=ZOOM_MAX)
            contourmap.create_contour_data(
                DATA_OUT_DIR,
                config.data_type,
                month,
                figure_dpi=1200,
                create_images=CREATE_IMAGES,
                zoomfactor=ZOOM_FACTOR
            )
            counter += 1


if __name__ == "__main__":
    main()
