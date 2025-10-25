import numpy

from climatemaps.datasets import (
    ClimateDataConfig,
    DataFormat,
    FutureClimateDataConfig,
    SpatialResolution,
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


def load_climate_data(data_config: ClimateDataConfig, month: int) -> GeoGrid:
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

        if data_config.resolution == SpatialResolution.MIN0_5:
            factor = 4
            logger.info(
                f"Downsampling {data_config.data_type_slug} from {data_config.resolution} with factor {factor}"
            )
            return GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values).downsample(
                factor
            )

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


def load_climate_data_for_difference(
    historical_config: ClimateDataConfig, future_config: FutureClimateDataConfig, month: int
) -> GeoGrid:
    historical_grid = load_climate_data(historical_config, month)
    future_grid = load_climate_data(future_config, month)

    # Ensure coordinate arrays match
    if not numpy.allclose(historical_grid.lon_range, future_grid.lon_range) or not numpy.allclose(
        historical_grid.lat_range, future_grid.lat_range
    ):
        raise ValueError("Coordinate arrays don't match between historical and future data")

    return future_grid.difference(historical_grid)
