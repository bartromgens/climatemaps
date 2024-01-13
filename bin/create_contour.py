#!/usr/bin/env python3

import sys
from dataclasses import dataclass

import matplotlib.pyplot as plt

sys.path.append('../climatemaps')

import climatemaps
from climatemaps.logger import logger

DATA_OUT_DIR = 'website/data'


@dataclass
class ContourConfig:
    data_type: str
    filepath: str
    conversion_factor: float
    config: climatemaps.contour.ContourPlotConfig


DEV_MODE = True

ZOOM_MAX = 7 if DEV_MODE else 13
CREATE_IMAGES = not DEV_MODE

CONTOUR_TYPES = [
    ContourConfig(
        data_type='precipitation',
        filepath='data/precipitation/cpre6190.dat',
        conversion_factor=0.1,  # (millimetres/day) *10
        config=climatemaps.contour.ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True)
    ),
    # ContourConfig(
    #     data_type='cloud',
    #     filepath='data/cloud/ccld6190.dat',
    #     conversion_factor=1,
    #     config=climatemaps.contour.ContourPlotConfig(0, 100, colormap=plt.cm.jet_r, title='Cloud coverage', unit='%')
    # )

    # 'mintemp': {
    #     'filepath': 'data/mintemp/ctmn6190.dat',
    #     'conversion_factor': 0.1,
    #     'config': climatemaps.contour.ContourPlotConfig(-40, 28, colormap=plt.cm.jet, title='Min. temperature', unit='C')
    # },
    # 'meantemp': {
    #     'filepath': 'data/meantemp/ctmp6190.dat',
    #     'conversion_factor': 0.1,
    #     'config': climatemaps.contour.ContourPlotConfig(-30, 35, colormap=plt.cm.jet, title='Mean temperature', unit='C')
    # },
    # 'maxtemp': {
    #     'filepath': 'data/maxtemp/ctmx6190.dat',
    #     'conversion_factor': 0.1,
    #     'config': climatemaps.contour.ContourPlotConfig(-20, 45, colormap=plt.cm.jet, title='Max. temperature', unit='C')
    # },
    # 'diurnaltemprange': {
    #     'filepath': 'data/diurnaltemprange/cdtr6190.dat',
    #     'conversion_factor': 0.1,
    #     'config': climatemaps.contour.ContourPlotConfig(5, 20, colormap=plt.cm.jet, title='Diurnal temperature range', unit='C')
    # },
    # 'wetdays': {
    #     'filepath': 'data/wetdays/cwet6190.dat',
    #     'conversion_factor': 0.1,
    #     'config': climatemaps.contour.ContourPlotConfig(0, 30, colormap=plt.cm.jet_r, title='Wet days', unit='days')
    # },
    # 'wind': {
    #     'filepath': 'data/wind/cwnd6190.dat',
    #     'conversion_factor': 0.1,
    #     'config': climatemaps.contour.ContourPlotConfig(0, 9, colormap=plt.cm.jet, title='Wind speed', unit='m/s')
    # },
    # 'radiation': {
    #     'filepath': 'data/radiation/crad6190.dat',
    #     'conversion_factor': 1.0,
    #     'config': climatemaps.contour.ContourPlotConfig(0, 300, colormap=plt.cm.jet, title='Radiation', unit='W/m^2')
    # },
    # 'vapourpressure': {
    #     'filepath': 'data/vapourpressure/cvap6190.dat',
    #     'conversion_factor': 0.1,
    #     'config': climatemaps.contour.ContourPlotConfig(1, 34, colormap=plt.cm.jet, title='Vapour pressure', unit='hPa')
    # },
]


def main():
    month_upper = 1
    n_data_sets = len(CONTOUR_TYPES) * month_upper
    counter = 0
    for config in CONTOUR_TYPES:
        for month in range(1, month_upper+1):
            logger.info('create image and tiles for "' + config.data_type + '" and month ' + str(month))
            progress = counter/n_data_sets*100.0
            logger.info("progress: " + str(int(progress)) + '%')
            latrange, lonrange, Z = climatemaps.data.import_climate_data(config.filepath, month, config.conversion_factor)
            contourmap = climatemaps.contour.Contour(config.config, lonrange, latrange, Z, zoom_min=0, zoom_max=ZOOM_MAX)
            contourmap.create_contour_data(
                DATA_OUT_DIR,
                config.data_type,
                month,
                figure_dpi=1200,
                create_images=CREATE_IMAGES
            )
            counter += 1


if __name__ == "__main__":
    main()
