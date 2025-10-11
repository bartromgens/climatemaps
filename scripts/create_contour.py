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

DEFAULT_TEST_SET_HISTORIC = {
    "variable_type": ClimateVarKey.T_MAX,
    "resolution": SpatialResolution.MIN10,
}

DEFAULT_TEST_SET_FUTURE = {
    "variable_type": ClimateVarKey.T_MAX,
    "resolution": SpatialResolution.MIN10,
    "climate_scenario": ClimateScenario.SSP126,
    "climate_model": ClimateModel.ENSEMBLE_MEAN,
    "year_range": (2021, 2040),
}


def _filter_by_criteria(
    data_sets: List[ClimateDataConfig], criteria: dict, is_difference: bool = False
) -> List[ClimateDataConfig]:
    def matches(config: ClimateDataConfig) -> bool:
        if config.variable_type != criteria["variable_type"]:
            return False
        if config.resolution != criteria["resolution"]:
            return False

        if is_difference:
            return (
                config.future_config.climate_scenario == criteria.get("climate_scenario")
                and config.future_config.climate_model == criteria.get("climate_model")
                and config.future_config.year_range == criteria.get("year_range")
            )

        year_match = (
            criteria.get("year_range") is None or config.year_range == criteria["year_range"]
        )
        scenario_match = (
            criteria.get("climate_scenario") is None
            or config.climate_scenario == criteria["climate_scenario"]
        )
        model_match = (
            criteria.get("climate_model") is None
            or config.climate_model == criteria["climate_model"]
        )

        return year_match and scenario_match and model_match

    return [ds for ds in data_sets if matches(ds)]


def _create_tasks_for_datasets(
    data_sets: List[ClimateDataConfig], month_upper: int, force_recreate: bool, name: str
) -> List[tuple]:
    tasks = [
        (config, month, force_recreate)
        for config in data_sets
        for month in range(1, month_upper + 1)
    ]
    logger.info(f"Added {len(tasks)} {name} tasks")
    return tasks


def main(force_recreate: bool = False, apply_test_set: bool = False) -> None:
    month_upper = 1 if settings.DEV_MODE else 12
    all_tasks = []

    dataset_groups = [
        (HISTORIC_DATA_SETS, DEFAULT_TEST_SET_HISTORIC, False, "historic"),
        (FUTURE_DATA_SETS, DEFAULT_TEST_SET_FUTURE, False, "future"),
        (DIFFERENCE_DATA_SETS, DEFAULT_TEST_SET_FUTURE, True, "difference"),
    ]

    for datasets, criteria, is_diff, name in dataset_groups:
        if apply_test_set:
            datasets = _filter_by_criteria(datasets, criteria, is_diff)
        all_tasks.extend(_create_tasks_for_datasets(datasets, month_upper, force_recreate, name))

    logger.info(f"Processing all data sets with {len(all_tasks)} total tasks")
    run_tasks_with_process_pool(all_tasks, process, settings.CREATE_CONTOUR_PROCESSES)


def run_tasks_with_process_pool(tasks: List[tuple], process, num_processes: int) -> None:
    total = len(tasks)
    executor = None
    try:
        executor = concurrent.futures.ProcessPoolExecutor(max_workers=num_processes)
        futures = {executor.submit(process, *task): task for task in tasks}
        for counter, future in enumerate(concurrent.futures.as_completed(futures)):
            result = future.result()
            progress = int((counter / total) * 100)
            logger.info(f"Completed: {result} | Progress: {progress}%")
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt received! Attempting to shut down executor...")
        for future in futures:
            future.cancel()
        if executor:
            executor.shutdown(wait=False, cancel_futures=True)
        terminate_process_pool_children()
        raise
    finally:
        if executor:
            executor.shutdown(wait=True)


def terminate_process_pool_children() -> None:
    children = multiprocessing.active_children()
    if not children:
        logger.info("No child processes to terminate.")
        return

    logger.info(f"Terminating {len(children)} child processes...")
    for proc in children:
        logger.info(f"Terminating child process PID={proc.pid}")
        proc.terminate()

    for proc in children:
        try:
            proc.join(timeout=3)
        except:
            pass

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


def process(config, month: int, force_recreate: bool) -> str:
    logger.info(f'Creating image and tiles for "{config.data_type_slug}" and month {month}')

    try:
        if isinstance(config, ClimateDifferenceDataConfig):
            files_exist = difference_tile_files_exist(config, month, maps_config)
        else:
            files_exist = tile_files_exist(config, month, maps_config)

        if force_recreate or not files_exist:
            _create_contour(config, month)
        else:
            logger.info(f'Skip creation of "{config.data_type_slug}" - {month} (already exists)')

        return f"{config.data_type_slug}-{month}"
    except Exception as e:
        logger.error(f"Failed to process {config.data_type_slug}, month {month}: {e}")
        raise


def _create_contour(data_set_config, month: int) -> None:
    if isinstance(data_set_config, ClimateDifferenceDataConfig):
        geo_grid = load_climate_data_for_difference(
            data_set_config.historical_config, data_set_config.future_config, month
        )
    else:
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
