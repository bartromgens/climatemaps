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
    load_climate_data,
    load_climate_data_for_difference,
)
from climatemaps.datasets import ClimateModel
from climatemaps.datasets import ClimateScenario
from climatemaps.datasets import ClimateVarKey
from climatemaps.datasets import ClimateDataConfig
from climatemaps.datasets import ClimateDifferenceDataConfig
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

DEFAULT_TEST_SET_HISTORIC = {
    "variable_type": ClimateVarKey.WET_DAYS,
    "resolution": SpatialResolution.MIN30,
    "climate_scenario": ClimateScenario.SSP126,
    "climate_model": ClimateModel.EC_EARTH3_VEG,
    "year_range": (1961, 1990),
}

DEFAULT_TEST_SET_FUTURE = {
    "variable_type": ClimateVarKey.T_MAX,
    "resolution": SpatialResolution.MIN10,
    "climate_scenario": ClimateScenario.SSP126,
    "climate_model": ClimateModel.ENSEMBLE_MEAN,
    "year_range": (2021, 2040),
}


def _apply_historic_test_set(
    data_sets: List[ClimateDataConfig], test_set_criteria: dict
) -> List[ClimateDataConfig]:
    """Apply test set criteria to regular climate data sets."""
    return list(
        filter(
            lambda x: (
                x.variable_type == test_set_criteria["variable_type"]
                and x.resolution == test_set_criteria["resolution"]
                and x.year_range == test_set_criteria["year_range"]
            ),
            data_sets,
        )
    )


def _apply_future_test_set(
    data_sets: List[ClimateDataConfig], test_set_criteria: dict
) -> List[ClimateDataConfig]:
    """Apply test set criteria to future climate data sets."""
    return list(
        filter(
            lambda x: (
                x.variable_type == test_set_criteria["variable_type"]
                and x.resolution == test_set_criteria["resolution"]
                and x.climate_scenario == test_set_criteria["climate_scenario"]
                and x.climate_model == test_set_criteria["climate_model"]
                and x.year_range == test_set_criteria["year_range"]
            ),
            data_sets,
        )
    )


def _apply_difference_test_set(
    data_sets: List[ClimateDataConfig], test_set_criteria: dict
) -> List[ClimateDataConfig]:
    """Apply test set criteria to difference climate data sets."""
    return list(
        filter(
            lambda x: (
                x.variable_type == test_set_criteria["variable_type"]
                and x.resolution == test_set_criteria["resolution"]
                and x.future_config.climate_scenario == test_set_criteria["climate_scenario"]
                and x.future_config.climate_model == test_set_criteria["climate_model"]
                and x.future_config.year_range == test_set_criteria["year_range"]
            ),
            data_sets,
        )
    )


def main(force_recreate: bool = False, apply_test_set: bool = False):
    """
    Main function to create contour tiles for all data set types.

    Args:
        force_recreate: Force recreation of existing tiles
        apply_test_set: Whether to apply the default test set for development testing
    """
    all_tasks = []
    month_upper = 1 if settings.DEV_MODE else 12

    # Process historic data sets
    historic_data_sets = HISTORIC_DATA_SETS_AVAILABLE
    if apply_test_set:
        historic_data_sets = _apply_historic_test_set(historic_data_sets, DEFAULT_TEST_SET_HISTORIC)

    historic_tasks = [
        (contour_config, month, force_recreate)
        for contour_config in historic_data_sets
        for month in range(1, month_upper + 1)
    ]
    all_tasks.extend(historic_tasks)
    logger.info(f"Added {len(historic_tasks)} historic tasks")

    # Process future data sets
    future_data_sets = FUTURE_DATA_SETS_AVAILABLE
    if apply_test_set:
        future_data_sets = _apply_future_test_set(future_data_sets, DEFAULT_TEST_SET_FUTURE)

    future_tasks = [
        (contour_config, month, force_recreate)
        for contour_config in future_data_sets
        for month in range(1, month_upper + 1)
    ]
    all_tasks.extend(future_tasks)
    logger.info(f"Added {len(future_tasks)} future tasks")

    # Process difference data sets
    difference_data_sets = DIFFERENCE_DATA_SETS_AVAILABLE
    if apply_test_set:
        difference_data_sets = _apply_difference_test_set(
            difference_data_sets, DEFAULT_TEST_SET_FUTURE
        )

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
    executor = None
    try:
        executor = concurrent.futures.ProcessPoolExecutor(max_workers=num_processes)
        futures = {executor.submit(process, *task): task for task in tasks}
        for counter, future in enumerate(concurrent.futures.as_completed(futures)):
            result = future.result()  # May raise if process fails
            progress = counter / total * 100.0
            logger.info(f"Completed: {result} | Progress: {int(progress)}%")
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt received! Attempting to shut down executor...")

        # Cancel all pending futures
        for future in futures:
            future.cancel()

        # Shutdown the executor immediately
        if executor:
            executor.shutdown(wait=False, cancel_futures=True)

        # Terminate all child processes
        terminate_process_pool_children()

        raise  # Re-raise to let caller handle or exit
    finally:
        # Ensure executor is properly shut down
        if executor:
            executor.shutdown(wait=True)


def terminate_process_pool_children():
    """Forcefully kill any subprocesses started by the current process."""
    children = multiprocessing.active_children()
    if not children:
        logger.info("No child processes to terminate.")
        return

    logger.info(f"Terminating {len(children)} child processes...")
    for proc in children:
        logger.info(f"Terminating child process PID={proc.pid}")
        proc.terminate()

    # Wait for processes to terminate gracefully
    for proc in children:
        try:
            proc.join(timeout=3)  # Wait up to 3 seconds for graceful termination
        except:
            pass  # Ignore errors during cleanup

    # Force kill any remaining processes
    remaining = [p for p in children if p.is_alive()]
    if remaining:
        logger.warning(f"Force killing {len(remaining)} remaining processes...")
        for proc in remaining:
            logger.warning(f"Force killing process PID={proc.pid}")
            proc.kill()
            try:
                proc.join(timeout=2)
            except:
                pass

    logger.info("All child processes terminated.")


def process(config, month: int, force_recreate: bool):
    """Process either regular or difference climate data configs."""
    logger.info(f'Creating image and tiles for "{config.data_type_slug}" and month {month}')

    try:
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
    except Exception as e:
        logger.error(f"Failed to process {config.data_type_slug}, month {month}: {e}")
        raise


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
        "--test-set",
        action="store_true",
        default=False,
        help="Use default test set for development testing (process only a subset of data sets).",
    )
    args = parser.parse_args()
    main(force_recreate=args.force_recreate, apply_test_set=args.test_set)
