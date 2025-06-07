#!/usr/bin/env python3
import sys

from climatemaps.datasets import ContourConfig

sys.path.append('../climatemaps')

import climatemaps
from climatemaps.logger import logger


DATA_OUT_DIR = 'website/data'
DEV_MODE = True

ZOOM_MIN = 1
ZOOM_MAX = 5 if DEV_MODE else 10
ZOOM_FACTOR = None if DEV_MODE else 2.0
# ZOOM_FACTOR = 2.0
# CREATE_IMAGES = not DEV_MODE
CREATE_IMAGES = True


CONTOUR_TYPES = climatemaps.datasets.CLIMATE_MODEL_DATA_SETS + climatemaps.datasets.HISTORIC_DATA_SETS
CONTOUR_TYPES = list(filter(lambda x: x.data_type == 'model_precipitation_5m_ssp585_2081_2100', CONTOUR_TYPES))


def main():
    month_upper = 1
    n_data_sets = len(CONTOUR_TYPES) * month_upper
    counter = 0
    for config in CONTOUR_TYPES:
        for month in range(1, month_upper+1):
            logger.info('create image and tiles for "' + config.data_type + '" and month ' + str(month))
            progress = counter/n_data_sets * 100.0
            logger.info(f"progress: {(int(progress))} %")
            _create_contour(config, month)
            counter += 1


def _create_contour(config: ContourConfig, month: int):
    lat_range, lon_range, values = None, None, None
    if config.format == climatemaps.datasets.DataFormat.IPCC_GRID:
        lat_range, lon_range, values = climatemaps.data.import_climate_data(config.filepath, month)
    elif config.format == climatemaps.datasets.DataFormat.GEOTIFF:
        lon_range, lat_range, values = climatemaps.geotiff.read_geotiff_month(config.filepath, month - 1)
        lat_range = lat_range * -1
    else:
        assert f'DataFormat {config.format} is not supported'
    values = values * config.conversion_factor
    contour_map = climatemaps.contour.Contour(
        config.config, lon_range, lat_range, values, zoom_min=ZOOM_MIN, zoom_max=ZOOM_MAX
    )
    contour_map.create_contour_data(
        DATA_OUT_DIR,
        config.data_type,
        month,
        figure_dpi=1200,
        create_images=CREATE_IMAGES,
        zoomfactor=ZOOM_FACTOR
    )


if __name__ == "__main__":
    main()
