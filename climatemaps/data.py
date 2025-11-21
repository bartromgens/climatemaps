import numpy

from climatemaps.datasets import (
    ClimateDataConfig,
    ClimateModel,
    DataFormat,
    FutureClimateDataConfig,
)
from climatemaps.download import ensure_data_available
from climatemaps.geotiff import (
    read_geotiff_future,
    read_geotiff_history,
    read_geotiff_cru_ts,
    read_geotiff_chelsa,
)
from climatemaps.geogrid import GeoGrid
from climatemaps.logger import logger


def _load_climate_data_base(data_config: ClimateDataConfig, month: int) -> GeoGrid:
    """Base function to load climate data without post-processing."""
    try:
        ensure_data_available(data_config)

        if data_config.format == DataFormat.CRU_TS:
            lon_range, lat_range, values = read_geotiff_cru_ts(data_config.filepath, month)
        elif data_config.format == DataFormat.GEOTIFF_WORLDCLIM_CMIP6:
            lon_range, lat_range, values = read_geotiff_future(data_config.filepath, month)
        elif data_config.format == DataFormat.GEOTIFF_WORLDCLIM_HISTORY:
            lon_range, lat_range, values = read_geotiff_history(data_config.filepath, month)
        elif data_config.format == DataFormat.CHELSA:
            lon_range, lat_range, values = read_geotiff_chelsa(data_config.filepath, month)
        else:
            raise ValueError(f"Unsupported data format: {data_config.format}")

        values = values * data_config.conversion_factor

        if data_config.conversion_function is not None:
            values = data_config.conversion_function(values, month)

        return GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)
    except FileNotFoundError as e:
        logger.exception(
            f"Failed to load climate data for {data_config.data_type_slug}, month {month}, file: {data_config.filepath}: {e}"
        )
        raise
    except Exception as e:
        logger.exception(
            f"Unexpected error loading climate data for {data_config.data_type_slug}, month {month}, file: {data_config.filepath}: {e}"
        )
        raise


def load_climate_data(data_config: ClimateDataConfig, month: int) -> GeoGrid:
    geo_grid = _load_climate_data_base(data_config, month)

    if geo_grid.values.size > 150_000_000:
        factor = 3
        logger.info(
            f"Downsampling {data_config.data_type_slug} from {data_config.resolution} with factor {factor}"
        )
        geo_grid = geo_grid.downsample(factor)

    if data_config.format == DataFormat.CHELSA:
        geo_grid = geo_grid.apply_land_mask()

    return geo_grid


def load_climate_data_for_single_value(data_config: ClimateDataConfig, month: int) -> GeoGrid:
    """Load climate data for single value extraction without downsampling or land masking."""
    return _load_climate_data_base(data_config, month)


def _calculate_difference(
    historical_config: ClimateDataConfig,
    future_config: FutureClimateDataConfig,
    month: int,
    load_function,
) -> GeoGrid:
    future_grid = load_climate_data(future_config, month)

    if future_config.climate_model == ClimateModel.ENSEMBLE_STD_DEV:
        return future_grid

    historical_grid = load_climate_data(historical_config, month)

    if not numpy.allclose(historical_grid.lon_range, future_grid.lon_range) or not numpy.allclose(
        historical_grid.lat_range, future_grid.lat_range
    ):
        raise ValueError("Coordinate arrays don't match between historical and future data")

    return future_grid.difference(historical_grid)


def load_climate_data_for_difference(
    historical_config: ClimateDataConfig, future_config: FutureClimateDataConfig, month: int
) -> GeoGrid:
    return _calculate_difference(historical_config, future_config, month, load_climate_data)


def load_climate_data_for_difference_single_value(
    historical_config: ClimateDataConfig, future_config: FutureClimateDataConfig, month: int
) -> GeoGrid:
    """Load climate data for difference calculation without downsampling or land masking for single value extraction."""
    return _calculate_difference(
        historical_config, future_config, month, load_climate_data_for_single_value
    )
