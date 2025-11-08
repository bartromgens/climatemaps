import zipfile
from pathlib import Path
from urllib.request import urlretrieve

from climatemaps.datasets import (
    ClimateDataConfig,
    ClimateModel,
    ClimateScenario,
    ClimateVarKey,
    DataFormat,
    FutureClimateDataConfig,
    CRU_TS_FILE_ABBREVIATIONS,
    SpatialResolution,
)
from climatemaps.ensemble import compute_ensemble_mean, compute_ensemble_std_dev
from climatemaps.logger import logger


def _get_worldclim_historical_url(resolution: SpatialResolution, variable: ClimateVarKey) -> str:
    base_url = "https://geodata.ucdavis.edu/climate/worldclim/2_1/base"

    resolution_map = {
        SpatialResolution.MIN10: "10m",
        SpatialResolution.MIN5: "5m",
        SpatialResolution.MIN2_5: "2.5m",
    }

    variable_map = {
        ClimateVarKey.T_MIN: "tmin",
        ClimateVarKey.T_MAX: "tmax",
        ClimateVarKey.PRECIPITATION: "prec",
    }

    res_str = resolution_map.get(resolution)
    var_str = variable_map.get(variable)

    if not res_str or not var_str:
        raise ValueError(f"Unsupported resolution {resolution} or variable {variable}")

    return f"{base_url}/wc2.1_{res_str}_{var_str}.zip"


def _get_worldclim_future_url(
    resolution: SpatialResolution,
    variable: ClimateVarKey,
    climate_model: ClimateModel,
    climate_scenario: ClimateScenario,
    year_range: tuple[int, int],
) -> str:
    base_url = "https://geodata.ucdavis.edu/cmip6"

    resolution_map = {
        SpatialResolution.MIN10: "10m",
        SpatialResolution.MIN5: "5m",
        SpatialResolution.MIN2_5: "2.5m",
    }

    variable_map = {
        ClimateVarKey.T_MIN: "tmin",
        ClimateVarKey.T_MAX: "tmax",
        ClimateVarKey.PRECIPITATION: "prec",
    }

    res_str = resolution_map.get(resolution)
    var_str = variable_map.get(variable)
    model_str = climate_model.filename
    scenario_str = climate_scenario.name.lower()
    year_str = f"{year_range[0]}-{year_range[1]}"

    if not res_str or not var_str:
        raise ValueError(f"Unsupported resolution {resolution} or variable {variable}")

    return f"{base_url}/{res_str}/{model_str}/{scenario_str}/wc2.1_{res_str}_{var_str}_{model_str}_{scenario_str}_{year_str}.tif"


def _download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading from {url}")
    logger.info(f"Saving to {destination}")

    try:
        urlretrieve(url, destination)
        logger.info(f"Successfully downloaded {destination}")
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        raise


def _extract_zip(zip_path: Path, extract_to: Path) -> None:
    logger.info(f"Extracting {zip_path} to {extract_to}")

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)

    logger.info(f"Successfully extracted to {extract_to}")

    # Remove the zip file after extraction
    zip_path.unlink()
    logger.info(f"Removed temporary file {zip_path}")


def _check_historical_data_exists(filepath: str) -> bool:
    data_dir = Path(filepath)
    if not data_dir.exists():
        return False

    # Check if at least the first month file exists
    data_type = filepath.split("/")[-1]
    first_month_file = data_dir / f"{data_type}_01.tif"
    return first_month_file.exists()


def _check_future_data_exists(filepath: str) -> bool:
    return Path(filepath).exists()


def _check_cru_ts_data_exists(filepath: str, year_range: tuple[int, int], abbr: str) -> bool:
    data_dir = Path(filepath)
    if not data_dir.exists():
        return False

    first_month_file = data_dir / f"cru_{abbr}_clim_{year_range[0]}-{year_range[1]}_01.tif"
    return first_month_file.exists()


def _get_cru_ts_url(variable: ClimateVarKey, year_range: tuple[int, int]) -> str:
    base_url = "https://dap.ceda.ac.uk/badc/ipcc-ddc/data/obs/cru_ts2_1/clim_30"

    abbr = CRU_TS_FILE_ABBREVIATIONS.get(variable)
    if not abbr:
        raise ValueError(f"Unsupported CRU-TS variable: {variable}")

    filename = f"cru_{abbr}_clim_{year_range[0]}-{year_range[1]}.zip"

    return f"{base_url}/{abbr}/{filename}"


def download_cru_ts_data(config: ClimateDataConfig) -> None:
    abbr = CRU_TS_FILE_ABBREVIATIONS.get(config.variable_type)
    if not abbr:
        raise ValueError(f"Unsupported CRU-TS variable: {config.variable_type}")

    if _check_cru_ts_data_exists(config.filepath, config.year_range, abbr):
        logger.info(f"CRU-TS data already exists at {config.filepath}")
        return

    logger.info(f"CRU-TS data not found at {config.filepath}, downloading...")

    try:
        url = _get_cru_ts_url(config.variable_type, config.year_range)
    except ValueError as e:
        logger.error(f"Cannot download data: {e}")
        raise

    data_dir = Path(config.filepath)
    data_dir.mkdir(parents=True, exist_ok=True)

    temp_zip = data_dir / f"cru_{abbr}_clim_{config.year_range[0]}-{config.year_range[1]}.zip"

    _download_file(url, temp_zip)
    _extract_zip(temp_zip, data_dir)


def download_historical_data(config: ClimateDataConfig) -> None:
    if _check_historical_data_exists(config.filepath):
        logger.info(f"Historical data already exists at {config.filepath}")
        return

    logger.info(f"Historical data not found at {config.filepath}, downloading...")

    try:
        url = _get_worldclim_historical_url(config.resolution, config.variable_type)
    except ValueError as e:
        logger.error(f"Cannot download data: {e}")
        raise

    # Download to temporary location
    data_dir = Path(config.filepath)
    temp_zip = data_dir.parent / f"{data_dir.name}.zip"

    _download_file(url, temp_zip)
    _extract_zip(temp_zip, data_dir)


def _create_ensemble_mean(config: FutureClimateDataConfig) -> None:
    logger.info(f"Creating ensemble mean for {config.data_type_slug}")

    base_dir = Path(config.filepath).parent
    output_dir = base_dir

    compute_ensemble_mean(
        base_dir=base_dir,
        resolution=config.resolution,
        variable=config.variable_type,
        scenario=config.climate_scenario,
        year_range=config.year_range,
        output_dir=output_dir,
    )


def _create_ensemble_std_dev(config: FutureClimateDataConfig) -> None:
    logger.info(f"Creating ensemble standard deviation for {config.data_type_slug}")

    base_dir = Path(config.filepath).parent
    output_dir = base_dir

    compute_ensemble_std_dev(
        base_dir=base_dir,
        resolution=config.resolution,
        variable=config.variable_type,
        scenario=config.climate_scenario,
        year_range=config.year_range,
        output_dir=output_dir,
    )


def download_future_data(config: FutureClimateDataConfig) -> None:
    if _check_future_data_exists(config.filepath):
        logger.info(f"Future data already exists at {config.filepath}")
        return

    if config.climate_model == ClimateModel.ENSEMBLE_MEAN:
        logger.info("Ensemble mean requested, creating from available models...")
        _create_ensemble_mean(config)
        return

    if config.climate_model == ClimateModel.ENSEMBLE_STD_DEV:
        logger.info("Ensemble standard deviation requested, creating from available models...")
        _create_ensemble_std_dev(config)
        return

    logger.info(f"Future data not found at {config.filepath}, downloading...")

    try:
        url = _get_worldclim_future_url(
            config.resolution,
            config.variable_type,
            config.climate_model,
            config.climate_scenario,
            config.year_range,
        )
    except ValueError as e:
        logger.error(f"Cannot download data: {e}")
        raise

    destination = Path(config.filepath)
    _download_file(url, destination)


def ensure_data_available(config: ClimateDataConfig) -> None:
    if config.format == DataFormat.GEOTIFF_WORLDCLIM_HISTORY:
        download_historical_data(config)
    elif config.format == DataFormat.GEOTIFF_WORLDCLIM_CMIP6:
        if isinstance(config, FutureClimateDataConfig):
            download_future_data(config)
        else:
            logger.warning(f"Future data format but not FutureClimateDataConfig: {config}")
    elif config.format == DataFormat.CRU_TS:
        download_cru_ts_data(config)
    else:
        logger.warning(f"Unsupported format for auto-download: {config.format}")
