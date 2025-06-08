#!/usr/bin/env python3
import sys
import concurrent.futures

sys.path.append('../climatemaps')

import climatemaps
from climatemaps.config import ClimateMapsConfig
from climatemaps.config import config_dev
from climatemaps.config import config_prod
from climatemaps.datasets import ClimateMapConfig
from climatemaps.logger import logger

DEV_MODE = True
maps_config: ClimateMapsConfig = config_dev if DEV_MODE else config_prod

DATA_SETS = climatemaps.datasets.CLIMATE_MODEL_DATA_SETS + climatemaps.datasets.HISTORIC_DATA_SETS
# CONTOUR_TYPES = list(filter(lambda x: x.data_type == 'model_precipitation', CONTOUR_TYPES))
DATA_SETS = list(filter(lambda x: x.data_type == 'temperature_max_worldclim_10m', DATA_SETS))


def main():
    month_upper = 1 if DEV_MODE else 12
    tasks = [(contour_config, month) for contour_config in DATA_SETS for month in range(1, month_upper + 1)]
    total = len(tasks)

    num_processes = 2
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_processes) as executor:
        futures = {executor.submit(process, task): task for task in tasks}
        for counter, future in enumerate(concurrent.futures.as_completed(futures)):
            result = future.result()
            progress = counter / total * 100.0
            logger.info(f"Completed: {result} | Progress: {int(progress)}%")


def process(config_month_pair):
    config, month = config_month_pair
    logger.info(f'Creating image and tiles for "{config.data_type}" and month {month}')
    _create_contour(config, month)
    return f'{config.data_type}-{month}'  # Just an indicator of progress


def _create_contour(contour_config: ClimateMapConfig, month: int):
    lat_range, lon_range, values = None, None, None
    if contour_config.format == climatemaps.datasets.DataFormat.IPCC_GRID:
        lat_range, lon_range, values = climatemaps.data.import_climate_data(contour_config.filepath, month)
    elif contour_config.format == climatemaps.datasets.DataFormat.GEOTIFF_WORLDCLIM_CMIP6:
        lon_range, lat_range, values = climatemaps.geotiff.read_geotiff_month(contour_config.filepath, month)
        lat_range = lat_range * -1
    elif contour_config.format == climatemaps.datasets.DataFormat.GEOTIFF_WORLDCLIM_HISTORY:
        lon_range, lat_range, values = climatemaps.geotiff.read_geotiff_history(contour_config.filepath, month)
        lat_range = lat_range * -1
    else:
        assert f'DataFormat {contour_config.format} is not supported'
    values = values * contour_config.conversion_factor
    contour_map = climatemaps.contour.Contour(
        contour_config.config, lon_range, lat_range, values, zoom_min=maps_config.zoom_min, zoom_max=maps_config.zoom_max
    )
    contour_map.create_contour_data(
        maps_config.data_dir_out,
        contour_config.data_type,
        month,
        figure_dpi=maps_config.figure_dpi,
        zoomfactor=maps_config.zoom_factor
    )


if __name__ == "__main__":
    main()
