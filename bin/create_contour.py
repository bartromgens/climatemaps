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
        'config': climatemaps.contour.ContourPlotConfig(0, 120, colormap=plt.cm.jet_r)
    },
    'cloud': {
        'filepath': 'data/cloud/ccld6190.dat',
        'config': climatemaps.contour.ContourPlotConfig(10, 90, colormap=plt.cm.jet_r)
    },
    'mintemp': {
        'filepath': 'data/mintemp/ctmn6190.dat',
        'config': climatemaps.contour.ContourPlotConfig(-300, 300, colormap=plt.cm.jet)
    },
    'maxtemp': {
        'filepath': 'data/maxtemp/ctmx6190.dat',
        'config': climatemaps.contour.ContourPlotConfig(-200, 400, colormap=plt.cm.jet)
    },
    # 'cloud': './data/cloud/ccld6190.dat',
    # 'mintemp': './data/mintemp/ctmn6190.dat',
    # 'maxtemp': './data/maxtemp/ctmx6190.dat',
}


def main():
    for data_type, settings in TYPES.items():
        for month in range(1, 13):
            latrange, lonrange, Z = climatemaps.data.import_climate_data(settings['filepath'], month)
            filepath_out = os.path.join(DATA_OUT_DIR, 'contour_' + data_type +'_' + str(month) + '.json')
            test_config = climatemaps.contour.ContourPlotConfig()
            contourmap = climatemaps.contour.Contour(settings['config'], lonrange, latrange, Z)
            contourmap.create_contour_data(filepath_out)


if __name__ == "__main__":
    main()
