#!/usr/bin/env python3

import argparse
from pathlib import Path
from typing import List

import numpy as np
import rasterio
from rasterio.transform import Affine

from climatemaps.datasets import (
    CLIMATE_VARIABLES,
    ClimateModel,
    ClimateScenario,
    ClimateVarKey,
    SpatialResolution,
)
from climatemaps.logger import logger


def get_model_filepath(
    base_dir: Path,
    resolution: str,
    variable: str,
    model: str,
    scenario: str,
    year_range: tuple[int, int],
) -> Path:
    filename = (
        f"wc2.1_{resolution}_{variable}_{model}_{scenario}_{year_range[0]}-{year_range[1]}.tif"
    )
    return base_dir / filename


def get_available_models(
    base_dir: Path,
    resolution: str,
    variable: str,
    scenario: str,
    year_range: tuple[int, int],
    exclude_models: List[ClimateModel] = None,
) -> List[Path]:
    available_files = []
    exclude_models = exclude_models or []

    for model_enum in ClimateModel:
        if model_enum in exclude_models:
            continue

        model_name = model_enum.value.replace("_", "-")
        filepath = get_model_filepath(
            base_dir, resolution, variable, model_name, scenario, year_range
        )

        if filepath.exists():
            available_files.append(filepath)
            logger.info(f"Found model file: {filepath.name}")
        else:
            logger.debug(f"Model file not found: {filepath.name}")

    return available_files


def compute_ensemble_mean(
    base_dir: Path,
    resolution: str,
    variable: str,
    scenario: str,
    year_range: tuple[int, int],
    output_dir: Path,
) -> Path:
    logger.info(f"Computing ensemble mean for {variable} {scenario} {year_range}")

    available_files = get_available_models(
        base_dir,
        resolution,
        variable,
        scenario,
        year_range,
        exclude_models=[ClimateModel.ENSEMBLE_MEAN],
    )

    if not available_files:
        logger.error(f"No model files found for {variable} {scenario} {year_range}")
        raise FileNotFoundError(f"No model files found for {variable} {scenario} {year_range}")

    logger.info(f"Found {len(available_files)} model files to average")

    with rasterio.open(available_files[0]) as src:
        metadata = src.meta.copy()
        num_bands = src.count
        width = src.width
        height = src.height
        transform = src.transform

    ensemble_data = np.zeros((num_bands, height, width), dtype=np.float32)

    for band_idx in range(num_bands):
        band_data_list = []

        for filepath in available_files:
            with rasterio.open(filepath) as src:
                band_data = src.read(band_idx + 1).astype(np.float32)
                band_data_list.append(band_data)

        band_stack = np.stack(band_data_list, axis=0)
        ensemble_data[band_idx] = np.nanmean(band_stack, axis=0)

        logger.info(f"Processed band {band_idx + 1}/{num_bands}")

    output_filepath = get_model_filepath(
        output_dir, resolution, variable, "ensemble-mean", scenario, year_range
    )
    output_filepath.parent.mkdir(parents=True, exist_ok=True)

    metadata.update({"dtype": "float32", "compress": "lzw"})

    with rasterio.open(output_filepath, "w", **metadata) as dst:
        for band_idx in range(num_bands):
            dst.write(ensemble_data[band_idx], band_idx + 1)

    logger.info(f"Ensemble mean written to: {output_filepath}")
    return output_filepath


def generate_all_ensemble_means(
    base_dir: Path,
    output_dir: Path,
    variables: List[ClimateVarKey] = None,
    scenarios: List[ClimateScenario] = None,
    resolutions: List[SpatialResolution] = None,
) -> None:
    if variables is None:
        variables = [ClimateVarKey.T_MIN, ClimateVarKey.T_MAX, ClimateVarKey.PRECIPITATION]

    if scenarios is None:
        scenarios = [
            ClimateScenario.SSP126,
            ClimateScenario.SSP245,
            ClimateScenario.SSP370,
            ClimateScenario.SSP585,
        ]

    if resolutions is None:
        resolutions = [SpatialResolution.MIN10]

    year_ranges = [(2021, 2040), (2041, 2060), (2061, 2080), (2081, 2100)]

    total = len(variables) * len(scenarios) * len(resolutions) * len(year_ranges)
    processed = 0

    for variable in variables:
        for scenario in scenarios:
            for resolution in resolutions:
                for year_range in year_ranges:
                    processed += 1
                    logger.info(f"\nProcessing {processed}/{total}")

                    variable_name = CLIMATE_VARIABLES[variable].filename.lower()
                    scenario_name = scenario.name.lower()
                    resolution_name = resolution.value

                    try:
                        compute_ensemble_mean(
                            base_dir,
                            resolution_name,
                            variable_name,
                            scenario_name,
                            year_range,
                            output_dir,
                        )
                    except FileNotFoundError as e:
                        logger.warning(f"Skipping: {e}")
                        continue
                    except Exception as e:
                        logger.error(
                            f"Error processing {variable_name} {scenario_name} {year_range}: {e}"
                        )
                        continue

    logger.info(f"\nCompleted processing {processed} combinations")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate ensemble mean climate data from individual climate models"
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("data/raw/worldclim/future"),
        help="Base directory containing individual model files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw/worldclim/future"),
        help="Output directory for ensemble mean files",
    )

    args = parser.parse_args()

    generate_all_ensemble_means(
        base_dir=args.base_dir,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
