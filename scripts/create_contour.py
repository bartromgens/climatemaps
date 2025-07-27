#!/usr/bin/env python3
import argparse
import multiprocessing
import os
import sys
import concurrent.futures
from typing import List

import numpy as np


module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

from climatemaps.config import ClimateMapsConfig
from climatemaps.config import get_config
from climatemaps.contour import ContourTileBuilder
from climatemaps.data import import_climate_data
from climatemaps.datasets import ClimateVarKey
from climatemaps.datasets import ClimateDataConfig
from climatemaps.datasets import DataFormat
from climatemaps.datasets import HISTORIC_DATA_SETS
from climatemaps.datasets import SpatialResolution
from climatemaps.geogrid import GeoGrid
from climatemaps.geotiff import read_geotiff_history
from climatemaps.geotiff import read_geotiff_month
from climatemaps.settings import settings
from climatemaps.logger import logger
from climatemaps.tile import tile_files_exist


maps_config: ClimateMapsConfig = get_config()

np.set_printoptions(3, threshold=100, suppress=True)  # .3f

# DATA_SETS = CLIMATE_MODEL_DATA_SETS + HISTORIC_DATA_SETS
DATA_SETS: List[ClimateDataConfig] = HISTORIC_DATA_SETS
# DATA_SETS = list(
#     filter(
#         lambda x: x.variable_type == ClimateVarKey.T_MAX and x.resolution == SpatialResolution.MIN5,
#         DATA_SETS,
#     )
# )


def main(force_recreate: bool = False):
    month_upper = 1 if settings.DEV_MODE else 12
    tasks = [
        (contour_config, month, force_recreate)
        for contour_config in DATA_SETS
        for month in range(1, month_upper + 1)
    ]

    num_processes = settings.CREATE_CONTOUR_PROCESSES
    run_tasks_with_process_pool(tasks, process, num_processes)


def run_tasks_with_process_pool(tasks, process, num_processes):
    total = len(tasks)
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_processes) as executor:
        try:
            futures = {executor.submit(process, *task): task for task in tasks}
            for counter, future in enumerate(concurrent.futures.as_completed(futures)):
                result = future.result()  # May raise if process fails
                progress = counter / total * 100.0
                logger.info(f"Completed: {result} | Progress: {int(progress)}%")
        except KeyboardInterrupt:
            logger.warning("KeyboardInterrupt received! Attempting to shut down executor...")

            # Shutdown the executor immediately
            executor.shutdown(wait=False, cancel_futures=True)

            # Terminate all child processes (optional but safer)
            terminate_process_pool_children()

            raise  # Re-raise to let caller handle or exit


def terminate_process_pool_children():
    """Forcefully kill any subprocesses started by the current process."""
    for proc in multiprocessing.active_children():
        logger.info(f"Terminating child process PID={proc.pid}")
        proc.terminate()
    logger.info("All child processes terminated.")


def process(config: ClimateDataConfig, month: int, force_recreate: bool):
    logger.info(f'Creating image and tiles for "{config.data_type_slug}" and month {month}')
    if force_recreate or not tile_files_exist(config, month, maps_config):
        _create_contour(config, month)
    else:
        logger.info(
            f'Skip creation of "{config.data_type_slug}" - {month} because it already exist'
        )
    return f"{config.data_type_slug}-{month}"  # Just an indicator of progress


def _create_contour(data_set_config: ClimateDataConfig, month: int):
    lat_range, lon_range, values = None, None, None
    if data_set_config.format == DataFormat.IPCC_GRID:
        lat_range, lon_range, values = import_climate_data(data_set_config.filepath, month)
    elif data_set_config.format == DataFormat.GEOTIFF_WORLDCLIM_CMIP6:
        lon_range, lat_range, values = read_geotiff_month(data_set_config.filepath, month)
    elif data_set_config.format == DataFormat.GEOTIFF_WORLDCLIM_HISTORY:
        lon_range, lat_range, values = read_geotiff_history(data_set_config.filepath, month)
    else:
        assert f"DataFormat {data_set_config.format} is not supported"
    values = values * data_set_config.conversion_factor
    if data_set_config.conversion_function is not None:
        values = data_set_config.conversion_function(values, month)
    geo_grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)
    contour_map = ContourTileBuilder(
        data_set_config.contour_config,
        geo_grid=geo_grid,
        zoom_min=maps_config.zoom_min,
        zoom_max=maps_config.zoom_max,
    )
    contour_map.create_tiles(
        maps_config.data_dir_out,
        data_set_config.data_type_slug,
        month,
        figure_dpi=maps_config.figure_dpi,
        zoom_factor=maps_config.zoom_factor,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Your script description here.")
    parser.add_argument(
        "--force-recreate",
        action="store_true",
        default=False,
        help="Force recreation of resources. Defaults to False.",
    )
    args = parser.parse_args()
    main(force_recreate=args.force_recreate)
