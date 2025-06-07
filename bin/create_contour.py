#!/usr/bin/env python3
import sys

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
            progress = counter/n_data_sets*100.0
            logger.info(f"progress: {(int(progress))} %")
            latrange, lonrange, Z = None, None, None
            if config.format == climatemaps.datasets.DataFormat.IPCC_GRID:
                latrange, lonrange, Z = climatemaps.data.import_climate_data(config.filepath, month)
            elif config.format == climatemaps.datasets.DataFormat.GEOTIFF:
                lonrange, latrange, Z = climatemaps.geotiff.read_geotiff_month(config.filepath, month-1)
                latrange = latrange*-1
            else:
                assert f'DataFormat {config.format} is not supported'
            Z = Z * config.conversion_factor
            # logger.info(f"lon: {lonrange}")
            # logger.info(f"lat: {latrange}")
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
