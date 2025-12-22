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
from climatemaps.geotiff import verify_geotiff_file
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


def _download_file(url: str, destination: Path, verify: bool = True) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading from {url}")
    logger.info(f"Saving to {destination}")

    try:
        urlretrieve(url, destination)
        logger.info(f"Successfully downloaded {destination}")

        if verify and destination.suffix.lower() in [".tif", ".tiff"]:
            if not verify_geotiff_file(destination):
                logger.warning(
                    f"Downloaded file {destination} failed verification, deleting and will retry"
                )
                destination.unlink()
                raise ValueError(f"Downloaded file {destination} failed verification")
    except Exception as e:
        if isinstance(e, ValueError) and "failed verification" in str(e):
            raise
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


def _get_cru_ts_url(variable: ClimateVarKey, year_range: tuple[int, int]) -> str:
    base_url = "https://dap.ceda.ac.uk/badc/ipcc-ddc/data/obs/cru_ts2_1/clim_30"

    abbr = CRU_TS_FILE_ABBREVIATIONS.get(variable)
    if not abbr:
        raise ValueError(f"Unsupported CRU-TS variable: {variable}")

    filename = f"cru_{abbr}_clim_{year_range[0]}-{year_range[1]}.zip"

    return f"{base_url}/{abbr}/{filename}"


def _get_chelsa_url(variable: ClimateVarKey, year_range: tuple[int, int], month: int = 1) -> str:
    base_url = "https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/1981-2010"

    # Use the variable mapping from datasets.py
    from climatemaps.datasets import CHELSA_FILE_ABBREVIATIONS

    var_str = CHELSA_FILE_ABBREVIATIONS.get(variable)
    if not var_str:
        raise ValueError(f"Unsupported CHELSA variable: {variable}")

    # RADIATION variable has a different filename format: month comes after year range
    if variable == ClimateVarKey.RADIATION:
        filename = f"CHELSA_{var_str}_{year_range[0]}-{year_range[1]}_{month:02d}_V.2.1.tif"
    else:
        filename = f"CHELSA_{var_str}_{month:02d}_{year_range[0]}-{year_range[1]}_V.2.1.tif"

    return f"{base_url}/{var_str}/{filename}"


def download_cru_ts_data(config: ClimateDataConfig, force_redownload: bool = False) -> None:
    abbr = CRU_TS_FILE_ABBREVIATIONS.get(config.variable_type)
    if not abbr:
        raise ValueError(f"Unsupported CRU-TS variable: {config.variable_type}")

    data_dir = Path(config.filepath)
    year_str = f"{config.year_range[0]}-{config.year_range[1]}"
    file_pattern = f"cru_{abbr}_clim_{year_str}_{{:02d}}.tif"
    first_month_file = data_dir / file_pattern.format(1)

    if first_month_file.exists() and not force_redownload:
        if verify_geotiff_file(first_month_file):
            logger.info(f"CRU-TS data already exists and is valid at {config.filepath}")
            return
        logger.warning("CRU-TS data exists but is corrupted, will re-download")
        for month in range(1, 13):
            (data_dir / file_pattern.format(month)).unlink(missing_ok=True)

    logger.info(f"CRU-TS data not found or invalid at {config.filepath}, downloading...")

    try:
        url = _get_cru_ts_url(config.variable_type, config.year_range)
    except ValueError as e:
        logger.error(f"Cannot download data: {e}")
        raise

    data_dir.mkdir(parents=True, exist_ok=True)
    temp_zip = data_dir / f"cru_{abbr}_clim_{year_str}.zip"

    _download_file(url, temp_zip, verify=False)
    _extract_zip(temp_zip, data_dir)

    for month in range(1, 13):
        month_file = data_dir / file_pattern.format(month)
        if month_file.exists() and not verify_geotiff_file(month_file):
            logger.warning(f"Extracted CRU-TS file for month {month:02d} failed verification")
            raise ValueError(f"Extracted CRU-TS file for month {month:02d} failed verification")


def download_chelsa_data(config: ClimateDataConfig, force_redownload: bool = False, month_upper: int = 12) -> None:
    # Create the base directory for CHELSA data
    base_dir = Path(config.filepath)
    base_dir.mkdir(parents=True, exist_ok=True)

    # Download data for months 1 to month_upper
    for month in range(1, month_upper + 1):
        # Construct the filename for this month
        from climatemaps.datasets import CHELSA_FILE_ABBREVIATIONS

        var_str = CHELSA_FILE_ABBREVIATIONS.get(config.variable_type)
        if not var_str:
            raise ValueError(f"Unsupported CHELSA variable: {config.variable_type}")

        filename = f"CHELSA_{var_str}_{config.year_range[0]}-{config.year_range[1]}_{month:02d}.tif"

        destination = base_dir / filename

        # Check if this month's data already exists and is valid
        if destination.exists() and not force_redownload:
            if verify_geotiff_file(destination):
                logger.info(
                    f"CHELSA data for month {month:02d} already exists and is valid at {destination}"
                )
                continue
            else:
                logger.warning(
                    f"CHELSA data for month {month:02d} exists but is corrupted, will re-download"
                )
                destination.unlink()

        logger.info(f"Downloading CHELSA data for month {month:02d}...")

        try:
            url = _get_chelsa_url(config.variable_type, config.year_range, month)
            _download_file(url, destination)
        except ValueError as e:
            logger.error(f"Cannot download data for month {month:02d}: {e}")
            raise


def download_historical_data(config: ClimateDataConfig, force_redownload: bool = False) -> None:
    data_dir = Path(config.filepath)
    data_type = config.filepath.split("/")[-1]
    first_month_file = data_dir / f"{data_type}_01.tif"

    if first_month_file.exists() and not force_redownload:
        if verify_geotiff_file(first_month_file):
            logger.info(f"Historical data already exists and is valid at {config.filepath}")
            return
        else:
            logger.warning(f"Historical data exists but is corrupted, will re-download")
            # Delete all month files
            for month in range(1, 13):
                month_file = data_dir / f"{data_type}_{month:02d}.tif"
                if month_file.exists():
                    month_file.unlink()

    logger.info(f"Historical data not found or invalid at {config.filepath}, downloading...")

    try:
        url = _get_worldclim_historical_url(config.resolution, config.variable_type)
    except ValueError as e:
        logger.error(f"Cannot download data: {e}")
        raise

    # Download to temporary location
    temp_zip = data_dir.parent / f"{data_dir.name}.zip"

    _download_file(url, temp_zip, verify=False)
    _extract_zip(temp_zip, data_dir)

    # Verify extracted files
    for month in range(1, 13):
        month_file = data_dir / f"{data_type}_{month:02d}.tif"
        if month_file.exists() and not verify_geotiff_file(month_file):
            logger.warning(f"Extracted historical file for month {month:02d} failed verification")
            raise ValueError(f"Extracted historical file for month {month:02d} failed verification")


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


def download_future_data(config: FutureClimateDataConfig, force_redownload: bool = False) -> None:
    destination = Path(config.filepath)

    if destination.exists() and not force_redownload:
        if verify_geotiff_file(destination):
            logger.info(f"Future data already exists and is valid at {config.filepath}")
            return
        else:
            logger.warning(f"Future data exists but is corrupted, will re-download")
            destination.unlink()

    if config.climate_model == ClimateModel.ENSEMBLE_MEAN:
        logger.info("Ensemble mean requested, creating from available models...")
        _create_ensemble_mean(config)
        return

    if config.climate_model == ClimateModel.ENSEMBLE_STD_DEV:
        logger.info("Ensemble standard deviation requested, creating from available models...")
        _create_ensemble_std_dev(config)
        return

    logger.info(f"Future data not found or invalid at {config.filepath}, downloading...")

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

    _download_file(url, destination)


def ensure_data_available(config: ClimateDataConfig, force_redownload: bool = False, month_upper: int = 12) -> None:
    if config.format == DataFormat.GEOTIFF_WORLDCLIM_HISTORY:
        download_historical_data(config, force_redownload)
    elif config.format == DataFormat.GEOTIFF_WORLDCLIM_CMIP6:
        if isinstance(config, FutureClimateDataConfig):
            download_future_data(config, force_redownload)
        else:
            logger.warning(f"Future data format but not FutureClimateDataConfig: {config}")
    elif config.format == DataFormat.CRU_TS:
        download_cru_ts_data(config, force_redownload)
    elif config.format == DataFormat.CHELSA:
        download_chelsa_data(config, force_redownload, month_upper)
    else:
        logger.warning(f"Unsupported format for auto-download: {config.format}")
