#!/usr/bin/env python3

import sys
import os

sys.path.append('./climatemaps')

import climatemaps


DATA_DIR = './website/data'


def test():
    latrange, lonrange, Z = climatemaps.data.import_climate_data()
    filepath_out = os.path.join(DATA_DIR, 'contour_test.json')
    test_config = climatemaps.contour.ContourPlotConfig()
    contourmap = climatemaps.contour.Contour(test_config, lonrange, latrange, Z)
    contourmap.create_contour_data(filepath_out)


if __name__ == "__main__":
    test()
