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
    read_geotiff_chelsa_point,
)
from climatemaps.geogrid import GeoGrid
from climatemaps.logger import logger


def _load_climate_data_base(data_config: ClimateDataConfig, month: int) -> GeoGrid:
    """Base function to load climate data without post-processing."""
    ensure_data_available(data_config, month_upper=month)

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


def load_climate_data(data_config: ClimateDataConfig, month: int) -> GeoGrid:
    geo_grid = _load_climate_data_base(data_config, month)

    logger.info(f"Grid data size size: {geo_grid.values.size/1_000_000:.1f} mega pixels")
    if (
        data_config.target_resolution_raster is not None
        and geo_grid.values.size > data_config.target_resolution_raster
    ):
        downsample_factor = float(
            numpy.sqrt(geo_grid.values.size / data_config.target_resolution_raster)
        )
        logger.info(
            f"Downsampling {data_config.data_type_slug} from {data_config.resolution_input} with factor {downsample_factor}"
        )
        geo_grid = geo_grid.downsample(downsample_factor)

    if data_config.format == DataFormat.CHELSA:
        geo_grid = geo_grid.apply_land_mask()

    return geo_grid


def load_climate_data_for_single_value(data_config: ClimateDataConfig, month: int) -> GeoGrid:
    return _load_climate_data_base(data_config, month)


def load_single_point_value(
    data_config: ClimateDataConfig, month: int, lon: float, lat: float
) -> float:
    ensure_data_available(data_config, month_upper=month, skip_verification=True)

    if data_config.format == DataFormat.CHELSA:
        value = read_geotiff_chelsa_point(data_config.filepath, month, lon, lat)
    else:
        geo_grid = _load_climate_data_base(data_config, month)
        return geo_grid.get_value_at_coordinate(lon, lat)

    value = value * data_config.conversion_factor

    if data_config.conversion_function is not None:
        value = data_config.conversion_function(numpy.array([value]), month)[0]

    if numpy.isnan(value):
        raise ValueError(f"No data available at coordinates (lat={lat}, lon={lon})")

    return float(value)


def _calculate_difference(
    historical_config: ClimateDataConfig, future_config: FutureClimateDataConfig, month: int
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
