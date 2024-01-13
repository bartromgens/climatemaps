#!/usr/bin/env python3

import sys
import math

import numpy
import matplotlib.pyplot as plt

sys.path.append('../climatemaps')

import climatemaps
from climatemaps.logger import logger

DATA_OUT_DIR = 'website/data'

ZOOM_MAX = 5

TYPES = {
    'precipitation': {
        'filepath': 'data/precipitation/cpre6190.dat',
        'conversion_factor': 0.1,  # (millimetres/day) *10
        'config': climatemaps.contour.ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, title='Precipitation', unit='mm/day', logscale=True)
    },
    'cloud': {
        'filepath': 'data/cloud/ccld6190.dat',
        'conversion_factor': 1,
        'config': climatemaps.contour.ContourPlotConfig(0, 100, colormap=plt.cm.jet_r, title='Cloud coverage', unit='%')
    },
    'mintemp': {
        'filepath': 'data/mintemp/ctmn6190.dat',
        'conversion_factor': 0.1,
        'config': climatemaps.contour.ContourPlotConfig(-40, 28, colormap=plt.cm.jet, title='Min. temperature', unit='C')
    },
    'meantemp': {
        'filepath': 'data/meantemp/ctmp6190.dat',
        'conversion_factor': 0.1,
        'config': climatemaps.contour.ContourPlotConfig(-30, 35, colormap=plt.cm.jet, title='Mean temperature', unit='C')
    },
    'maxtemp': {
        'filepath': 'data/maxtemp/ctmx6190.dat',
        'conversion_factor': 0.1,
        'config': climatemaps.contour.ContourPlotConfig(-20, 45, colormap=plt.cm.jet, title='Max. temperature', unit='C')
    },
    'diurnaltemprange': {
        'filepath': 'data/diurnaltemprange/cdtr6190.dat',
        'conversion_factor': 0.1,
        'config': climatemaps.contour.ContourPlotConfig(5, 20, colormap=plt.cm.jet, title='Diurnal temperature range', unit='C')
    },
    'wetdays': {
        'filepath': 'data/wetdays/cwet6190.dat',
        'conversion_factor': 0.1,
        'config': climatemaps.contour.ContourPlotConfig(0, 30, colormap=plt.cm.jet_r, title='Wet days', unit='days')
    },
    'wind': {
        'filepath': 'data/wind/cwnd6190.dat',
        'conversion_factor': 0.1,
        'config': climatemaps.contour.ContourPlotConfig(0, 9, colormap=plt.cm.jet, title='Wind speed', unit='m/s')
    },
    'radiation': {
        'filepath': 'data/radiation/crad6190.dat',
        'conversion_factor': 1.0,
        'config': climatemaps.contour.ContourPlotConfig(0, 300, colormap=plt.cm.jet, title='Radiation', unit='W/m^2')
    },
    'vapourpressure': {
        'filepath': 'data/vapourpressure/cvap6190.dat',
        'conversion_factor': 0.1,
        'config': climatemaps.contour.ContourPlotConfig(1, 34, colormap=plt.cm.jet, title='Vapour pressure', unit='hPa')
    },
}


def main():
    month_upper = 12
    n_data_sets = len(TYPES) * month_upper
    counter = 0
    for data_type, settings in TYPES.items():
        for month in range(1, month_upper+1):
            logger.info('create image and tiles for "' + data_type + '" and month ' + str(month))
            progress = counter/n_data_sets*100.0
            logger.info("progress: " + str(int(progress)) + '%')
            latrange, lonrange, Z = climatemaps.data.import_climate_data(settings['filepath'], month, settings['conversion_factor'])
            contourmap = climatemaps.contour.Contour(settings['config'], lonrange, latrange, Z, zoom_min=0, zoom_max=ZOOM_MAX)
            contourmap.create_contour_data(
                DATA_OUT_DIR,
                data_type,
                month,
                figure_dpi=1200
            )
            counter += 1
    # for month in range(1, 13):
    #     create_optimal_map(month)


def create_optimal_map(month):
    settings = TYPES['precipitation']
    latrange, lonrange, Zpre = climatemaps.data.import_climate_data(settings['filepath'], month, settings['conversion_factor'])

    settings = TYPES['cloud']
    latrange, lonrange, Zcloud = climatemaps.data.import_climate_data(settings['filepath'], month, settings['conversion_factor'])

    settings = TYPES['maxtemp']
    latrange, lonrange, Ztmax = climatemaps.data.import_climate_data(settings['filepath'], month, settings['conversion_factor'])

    for x in numpy.nditer(Zpre, op_flags=['readwrite']):
        if x/16.0 > 1.0:
            x[...] = 0.0
        else:
            x[...] = 1.0 - x/16.0

    for x in numpy.nditer(Ztmax, op_flags=['readwrite']):
        temp_ideal = 22
        x[...] = 1.0 - math.pow((x-temp_ideal)/10.0, 2)

    Zscore_cloud = (100 - Zcloud)/100

    Z = (Zpre + Zscore_cloud + Ztmax) / 3.0 * 10.0

    for x in numpy.nditer(Z, op_flags=['readwrite']):
        x[...] = max(x, 0.0)

    config = climatemaps.contour.ContourPlotConfig(0.0, 9.0, colormap=plt.cm.RdYlGn, unit='')
    contourmap = climatemaps.contour.Contour(config, lonrange, latrange, Z)
    contourmap.create_contour_data(
        DATA_OUT_DIR,
        'optimal',
        month,
        figure_dpi=1000
    )
    print('month done: ' + str(month))


if __name__ == "__main__":
    main()
