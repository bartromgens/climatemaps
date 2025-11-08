from pathlib import Path
from typing import List

import numpy as np
import rasterio

from climatemaps.datasets import (
    CLIMATE_VARIABLES,
    ClimateModel,
    ClimateScenario,
    ClimateVarKey,
    DataFormat,
    FutureClimateDataConfig,
    SpatialResolution,
)
from climatemaps.logger import logger

"""
Why this mix? 
It gives broad institutional and physical diversity, 
covers low/medium/high effective climate sensitivity (ECS), 
and avoids double‑counting very similar models, which can bias means. 
IPCC AR6 assessed ECS values for these models 
[table 7.SM.5](https://www.ipcc.ch/report/ar6/wg1/downloads/report/IPCC_AR6_WGI_Chapter07_SM.pdf) back up the spread noted above.
"""
INCLUDE_MODELS = [
    ClimateModel.BCC_CSM2_MR,
    ClimateModel.CMCC_ESM2,
    ClimateModel.EC_EARTH3_VEG,
    ClimateModel.GFDL_ESM4,
    ClimateModel.GISS_E2_1_G,
    ClimateModel.IPSL_CM6A_LR,
    ClimateModel.MIROC6,
    ClimateModel.MPI_ESM1_2_HR,
    ClimateModel.MRI_ESM2_0,
    ClimateModel.UKESM1_0_LL,
]


def get_model_filepath(
    base_dir: Path,
    resolution: SpatialResolution,
    variable: ClimateVarKey,
    model: str,
    scenario: ClimateScenario,
    year_range: tuple[int, int],
) -> Path:
    resolution_str = resolution.value
    variable_str = CLIMATE_VARIABLES[variable].filename.lower()
    scenario_str = scenario.name.lower()

    filename = f"wc2.1_{resolution_str}_{variable_str}_{model}_{scenario_str}_{year_range[0]}-{year_range[1]}.tif"
    return base_dir / filename


def get_available_models(
    base_dir: Path,
    resolution: SpatialResolution,
    variable: ClimateVarKey,
    scenario: ClimateScenario,
    year_range: tuple[int, int],
) -> List[Path]:
    from climatemaps.download import download_future_data

    available_files = []

    for model_enum in INCLUDE_MODELS:

        model_name = model_enum.filename
        filepath = get_model_filepath(
            base_dir, resolution, variable, model_name, scenario, year_range
        )

        if filepath.exists():
            available_files.append(filepath)
            logger.info(f"Found model file: {filepath.name}")
        else:
            logger.info(f"Model file not found: {filepath.name}, attempting to download...")

            config = FutureClimateDataConfig(
                variable_type=variable,
                resolution=resolution,
                year_range=year_range,
                climate_model=model_enum,
                climate_scenario=scenario,
                format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
                filepath=str(filepath),
            )

            try:
                download_future_data(config)
                if filepath.exists():
                    available_files.append(filepath)
                    logger.info(f"Downloaded model file: {filepath.name}")
            except Exception as e:
                # Not all models are available for all scenarios and variables. Example: https://geodata.ucdavis.edu/cmip6/10m/GFDL-ESM4/
                logger.error(f"Failed to download {filepath.name}: {e}")

    return available_files


def compute_ensemble_mean(
    base_dir: Path,
    resolution: SpatialResolution,
    variable: ClimateVarKey,
    scenario: ClimateScenario,
    year_range: tuple[int, int],
    output_dir: Path,
) -> Path:
    logger.info(f"Computing ensemble mean for {variable.name} {scenario.name} {year_range}")

    available_files = get_available_models(
        base_dir,
        resolution,
        variable,
        scenario,
        year_range,
    )

    if not available_files:
        logger.error(f"No model files found for {variable.name} {scenario.name} {year_range}")
        raise FileNotFoundError(
            f"No model files found for {variable.name} {scenario.name} {year_range}"
        )

    logger.info(f"Found {len(available_files)} model files to average")

    with rasterio.open(available_files[0]) as src:
        metadata = src.meta.copy()
        num_bands = src.count
        width = src.width
        height = src.height

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
        output_dir,
        resolution,
        variable,
        ClimateModel.ENSEMBLE_MEAN.filename,
        scenario,
        year_range,
    )
    output_filepath.parent.mkdir(parents=True, exist_ok=True)

    metadata.update({"dtype": "float32", "compress": "lzw"})

    with rasterio.open(output_filepath, "w", **metadata) as dst:
        for band_idx in range(num_bands):
            dst.write(ensemble_data[band_idx], band_idx + 1)

    logger.info(f"Ensemble mean written to: {output_filepath}")
    return output_filepath


def compute_ensemble_std_dev(
    base_dir: Path,
    resolution: SpatialResolution,
    variable: ClimateVarKey,
    scenario: ClimateScenario,
    year_range: tuple[int, int],
    output_dir: Path,
) -> Path:
    logger.info(
        f"Computing ensemble standard deviation for {variable.name} {scenario.name} {year_range}"
    )

    available_files = get_available_models(
        base_dir,
        resolution,
        variable,
        scenario,
        year_range,
    )

    if not available_files:
        logger.error(f"No model files found for {variable.name} {scenario.name} {year_range}")
        raise FileNotFoundError(
            f"No model files found for {variable.name} {scenario.name} {year_range}"
        )

    logger.info(f"Found {len(available_files)} model files to compute standard deviation")

    with rasterio.open(available_files[0]) as src:
        metadata = src.meta.copy()
        num_bands = src.count
        width = src.width
        height = src.height

    ensemble_data = np.zeros((num_bands, height, width), dtype=np.float32)

    for band_idx in range(num_bands):
        band_data_list = []

        for filepath in available_files:
            with rasterio.open(filepath) as src:
                band_data = src.read(band_idx + 1).astype(np.float32)
                band_data_list.append(band_data)

        band_stack = np.stack(band_data_list, axis=0)
        ensemble_data[band_idx] = np.nanstd(band_stack, axis=0)

        logger.info(f"Processed band {band_idx + 1}/{num_bands}")

    output_filepath = get_model_filepath(
        output_dir,
        resolution,
        variable,
        ClimateModel.ENSEMBLE_STD_DEV.filename,
        scenario,
        year_range,
    )
    output_filepath.parent.mkdir(parents=True, exist_ok=True)

    metadata.update({"dtype": "float32", "compress": "lzw"})

    with rasterio.open(output_filepath, "w", **metadata) as dst:
        for band_idx in range(num_bands):
            dst.write(ensemble_data[band_idx], band_idx + 1)

    logger.info(f"Ensemble standard deviation written to: {output_filepath}")
    return output_filepath
