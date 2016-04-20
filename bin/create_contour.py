#!/usr/bin/env python3

import sys
import os

import matplotlib.pyplot as plt

sys.path.append('./climatemaps')

import climatemaps


DATA_OUT_DIR = './website/data'

TYPES = {
    'precipitation': {
        'filepath': 'data/precipitation/cpre6190.dat',
        'conversion_factor': 0.1,  # (millimetres/day) *10
        'config': climatemaps.contour.ContourPlotConfig(0.1, 16, colormap=plt.cm.jet_r, unit='mm/day', logscale=True)
    },
    'cloud': {
        'filepath': 'data/cloud/ccld6190.dat',
        'conversion_factor': 1,
        'config': climatemaps.contour.ContourPlotConfig(0, 100, colormap=plt.cm.jet_r, unit='%')
    },
    'mintemp': {
        'filepath': 'data/mintemp/ctmn6190.dat',
        'conversion_factor': 0.1,
        'config': climatemaps.contour.ContourPlotConfig(-40, 28, colormap=plt.cm.jet, unit='C')
    },
    'maxtemp': {
        'filepath': 'data/maxtemp/ctmx6190.dat',
        'conversion_factor': 0.1,
        'config': climatemaps.contour.ContourPlotConfig(-20, 50, colormap=plt.cm.jet, unit='C')
    },
    'wetdays': {
        'filepath': 'data/wetdays/cwet6190.dat',
        'conversion_factor': 0.1,
        'config': climatemaps.contour.ContourPlotConfig(0, 30, colormap=plt.cm.jet_r, unit='days')
    },
}


def main():
    for data_type, settings in TYPES.items():
        for month in range(1, 13):
            latrange, lonrange, Z = climatemaps.data.import_climate_data(settings['filepath'], month, settings['conversion_factor'])
            filepath_out = os.path.join(DATA_OUT_DIR, 'contour_' + data_type +'_' + str(month))
            contourmap = climatemaps.contour.Contour(settings['config'], lonrange, latrange, Z)
            contourmap.create_contour_data(filepath_out)


if __name__ == "__main__":
    main()
