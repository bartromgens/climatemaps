#!/usr/bin/env python3
import sys
import concurrent.futures

from climatemaps.datasets import ContourConfig

sys.path.append('../climatemaps')

import climatemaps
from climatemaps.logger import logger


DATA_OUT_DIR = 'website/data'
DEV_MODE = True

ZOOM_MIN = 1
ZOOM_MAX = 6 if DEV_MODE else 10
ZOOM_FACTOR = None if DEV_MODE else 2.0
FIGURE_DPI = 1000 if DEV_MODE else 5000


CONTOUR_TYPES = climatemaps.datasets.CLIMATE_MODEL_DATA_SETS + climatemaps.datasets.HISTORIC_DATA_SETS
# CONTOUR_TYPES = list(filter(lambda x: x.data_type == 'model_precipitation', CONTOUR_TYPES))
CONTOUR_TYPES = list(filter(lambda x: x.data_type == 'precipitation_worldclim_10m', CONTOUR_TYPES))


def process(config_month_pair):
    config, month = config_month_pair
    logger.info(f'Creating image and tiles for "{config.data_type}" and month {month}')
    _create_contour(config, month)
    return f'{config.data_type}-{month}'  # Just an indicator of progress


def main():
    month_upper = 1 if DEV_MODE else 12
    tasks = [(config, month) for config in CONTOUR_TYPES for month in range(1, month_upper + 1)]
    total = len(tasks)

    num_processes = 1
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_processes) as executor:
        futures = {executor.submit(process, task): task for task in tasks}
        for counter, future in enumerate(concurrent.futures.as_completed(futures)):
            result = future.result()
            progress = counter / total * 100.0
            logger.info(f"Completed: {result} | Progress: {int(progress)}%")


def _create_contour(config: ContourConfig, month: int):
    lat_range, lon_range, values = None, None, None
    if config.format == climatemaps.datasets.DataFormat.IPCC_GRID:
        lat_range, lon_range, values = climatemaps.data.import_climate_data(config.filepath, month)
    elif config.format == climatemaps.datasets.DataFormat.GEOTIFF_WORLDCLIM_CMIP6:
        lon_range, lat_range, values = climatemaps.geotiff.read_geotiff_month(config.filepath, month)
        lat_range = lat_range * -1
    elif config.format == climatemaps.datasets.DataFormat.GEOTIFF_WORLDCLIM_HISTORY:
        lon_range, lat_range, values = climatemaps.geotiff.read_geotiff_history(config.filepath, month)
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
        figure_dpi=FIGURE_DPI,
        zoomfactor=ZOOM_FACTOR
    )


if __name__ == "__main__":
    main()
