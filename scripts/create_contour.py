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
from climatemaps.data import (
    import_climate_data,
    load_climate_data,
    load_climate_data_for_difference,
)
from climatemaps.datasets import ClimateScenario
from climatemaps.datasets import ClimateVarKey
from climatemaps.datasets import ClimateModel
from climatemaps.datasets import ClimateDataConfig
from climatemaps.datasets import ClimateDifferenceDataConfig
from climatemaps.datasets import DataFormat
from climatemaps.datasets import HISTORIC_DATA_SETS
from climatemaps.datasets import FUTURE_DATA_SETS
from climatemaps.datasets import DIFFERENCE_DATA_SETS
from climatemaps.datasets import SpatialResolution
from climatemaps.settings import settings
from climatemaps.logger import logger
from climatemaps.tile import tile_files_exist, difference_tile_files_exist


maps_config: ClimateMapsConfig = get_config()

np.set_printoptions(3, threshold=100, suppress=True)  # .3f

# Available data sets
HISTORIC_DATA_SETS_AVAILABLE = HISTORIC_DATA_SETS
FUTURE_DATA_SETS_AVAILABLE = FUTURE_DATA_SETS
DIFFERENCE_DATA_SETS_AVAILABLE = DIFFERENCE_DATA_SETS

# Default filter for testing (can be overridden via command line)
DEFAULT_FILTER = {
    "variable_type": ClimateVarKey.T_MIN,
    "resolution": SpatialResolution.MIN10,
    "climate_scenario": ClimateScenario.SSP126,
    "year_range": (2021, 2040),
}


def _apply_filter(
    data_sets: List[ClimateDataConfig], filter_criteria: dict
) -> List[ClimateDataConfig]:
    """Apply filter criteria to regular climate data sets."""
    return list(
        filter(
            lambda x: (
                x.variable_type == filter_criteria["variable_type"]
                and x.resolution == filter_criteria["resolution"]
                and getattr(x, "climate_scenario", None) == filter_criteria["climate_scenario"]
                and x.year_range == filter_criteria["year_range"]
            ),
            data_sets,
        )
    )


def _apply_difference_filter(
    data_sets: List[ClimateDifferenceDataConfig], filter_criteria: dict
) -> List[ClimateDifferenceDataConfig]:
    """Apply filter criteria to difference climate data sets."""
    return list(
        filter(
            lambda x: (
                x.variable_type == filter_criteria["variable_type"]
                and x.resolution == filter_criteria["resolution"]
                and x.future_config.climate_scenario == filter_criteria["climate_scenario"]
                and x.future_config.year_range == filter_criteria["year_range"]
            ),
            data_sets,
        )
    )


def main(force_recreate: bool = False, apply_filter: bool = False):
    """
    Main function to create contour tiles for all data set types.

    Args:
        force_recreate: Force recreation of existing tiles
        apply_filter: Whether to apply the default filter for development testing
    """
    all_tasks = []
    month_upper = 1 if settings.DEV_MODE else 12

    # Process historic data sets
    historic_data_sets = HISTORIC_DATA_SETS_AVAILABLE
    if apply_filter:
        historic_data_sets = _apply_filter(historic_data_sets, DEFAULT_FILTER)

    historic_tasks = [
        (contour_config, month, force_recreate)
        for contour_config in historic_data_sets
        for month in range(1, month_upper + 1)
    ]
    all_tasks.extend(historic_tasks)
    logger.info(f"Added {len(historic_tasks)} historic tasks")

    # Process future data sets
    future_data_sets = FUTURE_DATA_SETS_AVAILABLE
    if apply_filter:
        future_data_sets = _apply_filter(future_data_sets, DEFAULT_FILTER)

    future_tasks = [
        (contour_config, month, force_recreate)
        for contour_config in future_data_sets
        for month in range(1, month_upper + 1)
    ]
    all_tasks.extend(future_tasks)
    logger.info(f"Added {len(future_tasks)} future tasks")

    # Process difference data sets
    difference_data_sets = DIFFERENCE_DATA_SETS_AVAILABLE
    if apply_filter:
        difference_data_sets = _apply_difference_filter(difference_data_sets, DEFAULT_FILTER)

    difference_tasks = [
        (contour_config, month, force_recreate)
        for contour_config in difference_data_sets
        for month in range(1, month_upper + 1)
    ]
    all_tasks.extend(difference_tasks)
    logger.info(f"Added {len(difference_tasks)} difference tasks")

    logger.info(f"Processing all data sets with {len(all_tasks)} total tasks")
    num_processes = settings.CREATE_CONTOUR_PROCESSES
    run_tasks_with_process_pool(all_tasks, process, num_processes)


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


def process(config, month: int, force_recreate: bool):
    """Process either regular or difference climate data configs."""
    logger.info(f'Creating image and tiles for "{config.data_type_slug}" and month {month}')

    # Check if files exist using appropriate function
    if isinstance(config, ClimateDifferenceDataConfig):
        files_exist = difference_tile_files_exist(config, month, maps_config)
    else:
        files_exist = tile_files_exist(config, month, maps_config)

    if force_recreate or not files_exist:
        _create_contour(config, month)
    else:
        logger.info(
            f'Skip creation of "{config.data_type_slug}" - {month} because it already exist'
        )
    return f"{config.data_type_slug}-{month}"  # Just an indicator of progress


def _create_contour(data_set_config, month: int):
    """Create contour tiles for either regular or difference climate data."""
    if isinstance(data_set_config, ClimateDifferenceDataConfig):
        _create_difference_contour(data_set_config, month)
    else:
        _create_regular_contour(data_set_config, month)


def _create_regular_contour(data_set_config: ClimateDataConfig, month: int):
    """Create contour tiles for regular climate data."""
    geo_grid = load_climate_data(data_set_config, month)
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


def _create_difference_contour(data_set_config: ClimateDifferenceDataConfig, month: int):
    """Create contour tiles for climate difference maps."""
    difference_grid = load_climate_data_for_difference(
        data_set_config.historical_config, data_set_config.future_config, month
    )

    contour_map = ContourTileBuilder(
        data_set_config.contour_config,
        geo_grid=difference_grid,
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
    parser = argparse.ArgumentParser(
        description="Create climate map contour tiles for all data set types."
    )
    parser.add_argument(
        "--force-recreate",
        action="store_true",
        default=False,
        help="Force recreation of resources. Defaults to False.",
    )
    parser.add_argument(
        "--filter",
        action="store_true",
        default=False,
        help="Apply default filtering for development testing (process only a subset of data sets).",
    )
    args = parser.parse_args()
    main(force_recreate=args.force_recreate, apply_filter=args.filter)
