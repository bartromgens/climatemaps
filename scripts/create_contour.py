#!/usr/bin/env python3
import argparse
import gc
import os
import subprocess
import sys
from datetime import datetime

import numpy as np

module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

from climatemaps.bbox import BoundingBox, Region, get_region_bbox
from climatemaps.config import ClimateMapsConfig, get_config
from climatemaps.contour import ContourTileBuilder
from climatemaps.data import load_climate_data, load_climate_data_for_difference
from climatemaps.datasets import (
    ClimateDataConfig,
    ClimateDifferenceDataConfig,
    ClimateModel,
    ClimateScenario,
    ClimateVarKey,
)
from climatemaps.gdal import GdalCalculator
from climatemaps.geogrid import GeoGrid
from climatemaps.logger import logger
from climatemaps.tile import difference_tile_files_exist, tile_files_exist

from scripts.utils import (
    check_if_mbtiles_older_than,
    create_tasks,
    filter_datasets,
    pre_download_all_data,
    run_tasks_in_parallel,
)


maps_config: ClimateMapsConfig = get_config()
np.set_printoptions(3, threshold=100, suppress=True)


def main(
    force_recreate: bool = False,
    climate_model: ClimateModel | None = None,
    variable_type: ClimateVarKey | None = None,
    if_older_than: datetime | None = None,
    processes: int = 1,
    dataset_type: str | None = None,
    month: int | None = None,
    region: Region | None = None,
    future_date_range: tuple[int, int] | None = None,
    climate_scenario: ClimateScenario | None = None,
) -> None:
    month_lower, month_upper = _get_month_range(month)

    bbox = get_region_bbox(region) if region else None
    if bbox:
        logger.info(
            f"Processing region {region.value}: "
            f"lon=[{bbox.lon_min}, {bbox.lon_max}], lat=[{bbox.lat_min}, {bbox.lat_max}]"
        )

    datasets = filter_datasets(
        climate_model, variable_type, dataset_type, future_date_range, climate_scenario
    )
    if not datasets:
        return

    tasks = create_tasks(datasets, month_lower, month_upper, force_recreate, if_older_than, bbox)

    logger.info("Pre-ensuring all data files exist before multiprocessing")
    pre_download_all_data(datasets, month_upper)

    logger.info(f"Processing {len(datasets)} datasets with {len(tasks)} total tasks")
    run_tasks_in_parallel(tasks, _process_single_task, processes)


def _get_month_range(month: int | None) -> tuple[int, int]:
    if month is not None:
        logger.info(f"Processing only month {month}")
        return month, month
    return 1, 12


def _process_single_task(
    config: ClimateDataConfig | ClimateDifferenceDataConfig,
    month: int,
    force_recreate: bool,
    if_older_than: datetime | None = None,
    bbox: BoundingBox | None = None,
) -> str:
    logger.info(f'Creating tiles for "{config.data_type_slug}" - month {month}')

    try:
        should_create = force_recreate or not _tile_files_exist(config, month)

        if not should_create and if_older_than is not None:
            should_create = check_if_mbtiles_older_than(config, month, if_older_than, maps_config)
            if should_create:
                logger.info(
                    f'Recreating "{config.data_type_slug}" - {month} '
                    f"(files older than {if_older_than.date()})"
                )

        if should_create:
            _create_contour_tiles(config, month, bbox)
        else:
            logger.info(f'Skip creation of "{config.data_type_slug}" - {month} (already exists)')

        return f"{config.data_type_slug}-{month}"

    except Exception as e:
        logger.exception(f"Failed to process {config.data_type_slug}, month {month}: {e}")
        raise


def _tile_files_exist(config: ClimateDataConfig | ClimateDifferenceDataConfig, month: int) -> bool:
    if isinstance(config, ClimateDifferenceDataConfig):
        return difference_tile_files_exist(config, month, maps_config)
    return tile_files_exist(config, month, maps_config)


def _create_contour_tiles(
    config: ClimateDataConfig | ClimateDifferenceDataConfig,
    month: int,
    bbox: BoundingBox | None = None,
) -> None:
    if isinstance(config, ClimateDifferenceDataConfig):
        geo_grid = load_climate_data_for_difference(
            config.historical_config, config.future_config, month, bbox
        )
    else:
        geo_grid = load_climate_data(config, month, bbox)

    _log_max_zoom_level(geo_grid)

    contour_map = ContourTileBuilder(
        config.contour_config,
        geo_grid=geo_grid,
        zoom_min=maps_config.zoom_min,
        zoom_max_vector=maps_config.zoom_max_vector,
        target_resolution_vector=config.target_resolution_vector,
    )
    contour_map.create_tiles(
        maps_config.data_dir_out,
        config.data_type_slug,
        month,
        zoom_factor=config.zoom_factor,
    )


def _log_max_zoom_level(geo_grid: GeoGrid) -> None:
    width_pixels = len(geo_grid.lon_range)
    height_pixels = len(geo_grid.lat_range)
    max_zoom_level = GdalCalculator.calculate_max_zoom_level_from_pixels(
        width_pixels, height_pixels
    )
    logger.info(
        f"Max zoom level for geo_grid (resolution: {width_pixels}x{height_pixels}): "
        f"{max_zoom_level}"
    )


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create climate map contour tiles for all data set types."
    )
    parser.add_argument(
        "--force-recreate",
        action="store_true",
        help="Force recreation of existing tiles",
    )
    parser.add_argument(
        "--climate-model",
        type=str,
        choices=[model.value for model in ClimateModel],
        help="Process only datasets for a specific climate model",
    )
    parser.add_argument(
        "--variable-type",
        type=str,
        choices=[var.value for var in ClimateVarKey],
        help="Process only datasets for a specific variable type",
    )
    parser.add_argument(
        "--if-older-than",
        type=str,
        metavar="YYYY-MM-DD",
        help="Only update tiles older than the specified date (format: YYYY-MM-DD)",
    )
    parser.add_argument(
        "--processes",
        type=int,
        default=1,
        help="Number of parallel processes to use (default: 1)",
    )
    parser.add_argument(
        "--dataset-type",
        type=str,
        choices=["historic", "future", "difference"],
        help="Process only specific dataset type (default: all types)",
    )
    parser.add_argument(
        "--month",
        type=int,
        choices=range(1, 13),
        metavar="1-12",
        help="Process only a specific month 1-12 (default: all months)",
    )
    parser.add_argument(
        "--region",
        type=str,
        choices=[region.value for region in Region],
        help=(
            "Process only a specific geographic region for faster feedback "
            "(e.g., 'europe-africa'). This loads only the relevant portion of the data "
            "while maintaining full resolution and zoom levels."
        ),
    )
    parser.add_argument(
        "--future-date-range",
        type=str,
        choices=["2021-2040", "2041-2060", "2061-2080", "2081-2100"],
        help="Process only datasets for a specific future date range (e.g., '2021-2040')",
    )
    parser.add_argument(
        "--climate-scenario",
        type=str,
        choices=[scenario.value for scenario in ClimateScenario],
        help="Process only datasets for a specific climate scenario (e.g., 'SSP126', 'SSP585')",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_arguments()

    climate_model = ClimateModel(args.climate_model) if args.climate_model else None
    variable_type = ClimateVarKey(args.variable_type) if args.variable_type else None
    region = Region(args.region) if args.region else None
    climate_scenario = ClimateScenario(args.climate_scenario) if args.climate_scenario else None

    if_older_than = None
    if args.if_older_than:
        try:
            if_older_than = datetime.strptime(args.if_older_than, "%Y-%m-%d")
        except ValueError as e:
            print(f"Error: Invalid date format '{args.if_older_than}'. Expected: YYYY-MM-DD")
            sys.exit(1)

    future_date_range = None
    if args.future_date_range:
        start_year, end_year = args.future_date_range.split("-")
        future_date_range = (int(start_year), int(end_year))

    main(
        force_recreate=args.force_recreate,
        climate_model=climate_model,
        variable_type=variable_type,
        if_older_than=if_older_than,
        processes=args.processes,
        dataset_type=args.dataset_type,
        month=args.month,
        region=region,
        future_date_range=future_date_range,
        climate_scenario=climate_scenario,
    )

    logger.info("Running create_tileserver_config.py --dev-only")
    tileserver_script = os.path.join(os.path.dirname(__file__), "create_tileserver_config.py")
    subprocess.run(
        [sys.executable, tileserver_script, "--dev-only"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
