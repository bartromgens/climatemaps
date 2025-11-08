#!/usr/bin/env python3
import argparse
import multiprocessing
import os
import sys
import concurrent.futures
from datetime import datetime
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
from climatemaps.download import ensure_data_available


maps_config: ClimateMapsConfig = get_config()

np.set_printoptions(3, threshold=100, suppress=True)  # .3f

DEFAULT_TEST_SET_HISTORIC = {
    "variable_type": ClimateVarKey.T_MAX,
    "resolution": SpatialResolution.MIN10,
}

DEFAULT_TEST_SET_FUTURE = {
    "variable_type": ClimateVarKey.PRECIPITATION,
    "resolution": SpatialResolution.MIN10,
    "climate_scenario": ClimateScenario.SSP370,
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
            or getattr(config, "climate_scenario", None) == criteria["climate_scenario"]
        )
        model_match = (
            criteria.get("climate_model") is None
            or getattr(config, "climate_model", None) == criteria["climate_model"]
        )

        return year_match and scenario_match and model_match

    return [ds for ds in data_sets if matches(ds)]


def _create_tasks_for_datasets(
    data_sets: List[ClimateDataConfig],
    month_upper: int,
    force_recreate: bool,
    name: str,
    if_older_than: datetime | None = None,
) -> List[tuple]:
    tasks = [
        (config, month, force_recreate, if_older_than)
        for config in data_sets
        for month in range(1, month_upper + 1)
    ]
    logger.info(f"Added {len(tasks)} {name} tasks")
    return tasks


def _pre_ensure_all_data_available(data_sets: List[ClimateDataConfig]) -> None:
    unique_configs = set()

    for config in data_sets:
        if isinstance(config, ClimateDifferenceDataConfig):
            unique_configs.add(id(config.historical_config))
            unique_configs.add(id(config.future_config))
        else:
            unique_configs.add(id(config))

    logger.info(f"Pre-downloading/generating data for {len(unique_configs)} unique configurations")

    processed_configs = set()
    failed_downloads = []

    def try_ensure_data(cfg: ClimateDataConfig, description: str) -> None:
        if id(cfg) in processed_configs:
            return

        logger.info(f"Ensuring data available for {description}: {cfg.data_type_slug}")
        try:
            ensure_data_available(cfg)
            processed_configs.add(id(cfg))
        except Exception as e:
            failed_downloads.append((cfg.data_type_slug, str(e)))
            logger.warning(f"Failed to ensure data for {description} {cfg.data_type_slug}: {e}")

    for config in data_sets:
        if isinstance(config, ClimateDifferenceDataConfig):
            try_ensure_data(config.historical_config, "historical")
            try_ensure_data(config.future_config, "future")
        else:
            try_ensure_data(config, "")

    if failed_downloads:
        logger.error(f"Failed to download/generate {len(failed_downloads)} dataset(s):")
        for data_slug, error in failed_downloads:
            logger.error(f"  - {data_slug}: {error}")

    logger.info(
        f"Data pre-download/generation completed ({len(processed_configs)} successful, {len(failed_downloads)} failed)"
    )


def _mbtiles_are_older_than_date(
    config: ClimateDataConfig, month: int, threshold_date: datetime
) -> bool:
    directory = os.path.join(maps_config.data_dir_out, config.data_type_slug)

    mbtiles_files = [
        os.path.join(directory, f"{month}_raster.mbtiles"),
        os.path.join(directory, f"{month}_vector.mbtiles"),
    ]

    for file_path in mbtiles_files:
        if not os.path.isfile(file_path):
            return True

        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        if file_mtime < threshold_date:
            return True

    return False


def main(
    force_recreate: bool = False,
    limited_test_set: bool = False,
    climate_model: ClimateModel | None = None,
    if_older_than: datetime | None = None,
    processes: int = 1,
) -> None:
    month_upper = 1 if limited_test_set else 12
    all_tasks = []
    all_datasets = []

    dataset_groups = [
        (HISTORIC_DATA_SETS, DEFAULT_TEST_SET_HISTORIC, False, "historic"),
        (FUTURE_DATA_SETS, DEFAULT_TEST_SET_FUTURE, False, "future"),
        (DIFFERENCE_DATA_SETS, DEFAULT_TEST_SET_FUTURE, True, "difference"),
    ]

    for datasets, criteria, is_diff, name in dataset_groups:
        if limited_test_set:
            datasets = _filter_by_criteria(datasets, criteria, is_diff)
        elif climate_model is not None:
            if name == "historic":
                datasets = []
            elif is_diff:
                datasets = [
                    ds for ds in datasets if ds.future_config.climate_model == climate_model
                ]
            else:
                datasets = [ds for ds in datasets if ds.climate_model == climate_model]
        all_datasets.extend(datasets)
        all_tasks.extend(
            _create_tasks_for_datasets(datasets, month_upper, force_recreate, name, if_older_than)
        )

    logger.info("Pre-ensuring all data files exist before multiprocessing")
    _pre_ensure_all_data_available(all_datasets)

    logger.info(f"Processing all data sets with {len(all_tasks)} total tasks")
    run_tasks_with_process_pool(all_tasks, process, processes)


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


def process(config, month: int, force_recreate: bool, if_older_than: datetime | None = None) -> str:
    logger.info(f'Creating image and tiles for "{config.data_type_slug}" and month {month}')

    try:
        if isinstance(config, ClimateDifferenceDataConfig):
            files_exist = difference_tile_files_exist(config, month, maps_config)
        else:
            files_exist = tile_files_exist(config, month, maps_config)

        should_create = force_recreate or not files_exist

        if not should_create and if_older_than is not None and files_exist:
            should_create = _mbtiles_are_older_than_date(config, month, if_older_than)
            if should_create:
                logger.info(
                    f'Recreating "{config.data_type_slug}" - {month} (files older than {if_older_than.date()})'
                )

        if should_create:
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
    parser.add_argument(
        "--climate-model",
        type=str,
        default=None,
        choices=[model.value for model in ClimateModel],
        help="Process only datasets for a specific climate model (e.g., ENSEMBLE_MEAN, EC_Earth3_Veg).",
    )
    parser.add_argument(
        "--if-older-than",
        type=str,
        default=None,
        metavar="YYYY-MM-DD",
        help="Only update tiles if mbtiles files are older than the specified date (format: YYYY-MM-DD).",
    )
    parser.add_argument(
        "--processes",
        type=int,
        default=1,
        help="Number of parallel processes to use for tile creation. Defaults to 1.",
    )
    args = parser.parse_args()

    climate_model = None
    if args.climate_model:
        climate_model = ClimateModel(args.climate_model)

    if_older_than = None
    if args.if_older_than:
        try:
            if_older_than = datetime.strptime(args.if_older_than, "%Y-%m-%d")
        except ValueError:
            parser.error(f"Invalid date format: {args.if_older_than}. Expected format: YYYY-MM-DD")

    main(
        force_recreate=args.force_recreate,
        limited_test_set=args.test_set,
        climate_model=climate_model,
        if_older_than=if_older_than,
        processes=args.processes,
    )
