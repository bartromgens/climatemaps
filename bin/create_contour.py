#!/usr/bin/env python3

import sys
import os

sys.path.append('./climatemaps')

import climatemaps


DATA_OUT_DIR = './website/data'

TYPES = {
    'precipitation': './data/precipitation/cpre6190.dat',
    'cloud': './data/cloud/ccld6190.dat',
}


def main():
    for data_type, filepath in TYPES.items():
        for month in range(1, 13):
            latrange, lonrange, Z = climatemaps.data.import_climate_data(filepath, month)
            filepath_out = os.path.join(DATA_OUT_DIR, 'contour_' + data_type +'_' + str(month) + '.json')
            test_config = climatemaps.contour.ContourPlotConfig()
            contourmap = climatemaps.contour.Contour(test_config, lonrange, latrange, Z)
            contourmap.create_contour_data(filepath_out)


if __name__ == "__main__":
    main()
