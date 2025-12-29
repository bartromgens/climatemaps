import gc

import numpy

from climatemaps.datasets import (
    ClimateDataConfig,
    ClimateModel,
    ClimateVarKey,
    DataFormat,
    DerivedClimateDataConfig,
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
from climatemaps.sunshine import interpolate_terrain_to_grid


def _maybe_downsample(grid: GeoGrid, target_resolution: int | None) -> GeoGrid:
    if target_resolution is None or grid.values.size <= target_resolution:
        return grid
    downsample_factor = float(numpy.sqrt(grid.values.size / target_resolution))
    logger.info(f"Downsampling with factor {downsample_factor:.2f}")
    return grid.downsample(downsample_factor)


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


def _load_derived_climate_data(
    data_config: DerivedClimateDataConfig, month: int, apply_downsampling: bool = True
) -> GeoGrid:
    """Load and compute derived climate data from multiple source variables.

    To avoid memory issues, each source grid is loaded and downsampled individually
    before loading the next one. The computation is then performed on the
    downsampled grids.
    """
    target_resolution = data_config.target_resolution_raster if apply_downsampling else None
    source_grids: dict[ClimateVarKey, GeoGrid] = {}

    for var_key, source_cfg in data_config.source_configs.items():
        logger.info(f"Loading source variable {var_key.value} for derived computation")
        grid = _load_climate_data_base(source_cfg, month)
        grid = _maybe_downsample(grid, target_resolution)
        gc.collect()
        source_grids[var_key] = grid

    first_grid = next(iter(source_grids.values()))
    source_values = [source_grids[var_key].values for var_key in data_config.source_configs.keys()]

    if data_config.needs_lat_and_month:
        lat_grid = numpy.tile(
            first_grid.lat_range[:, numpy.newaxis], (1, first_grid.values.shape[1])
        )

        if data_config.needs_terrain:
            terrain_data = interpolate_terrain_to_grid(first_grid.lon_range, first_grid.lat_range)
            if terrain_data is not None:
                slope, aspect = terrain_data
                logger.info("Applying slope correction to derived computation")
                computed_values = data_config.compute_function(
                    *source_values, lat_grid, month, slope, aspect
                )
            else:
                logger.info("No terrain data available, using horizontal surface assumption")
                computed_values = data_config.compute_function(*source_values, lat_grid, month)
        else:
            computed_values = data_config.compute_function(*source_values, lat_grid, month)
    else:
        computed_values = data_config.compute_function(*source_values)

    return GeoGrid(
        lon_range=first_grid.lon_range,
        lat_range=first_grid.lat_range,
        values=computed_values,
    )


def load_climate_data(data_config: ClimateDataConfig, month: int) -> GeoGrid:
    if isinstance(data_config, DerivedClimateDataConfig):
        geo_grid = _load_derived_climate_data(data_config, month, apply_downsampling=True)
    else:
        geo_grid = _load_climate_data_base(data_config, month)
        geo_grid = _maybe_downsample(geo_grid, data_config.target_resolution_raster)

    if data_config.format == DataFormat.CHELSA:
        geo_grid = geo_grid.apply_land_mask()

    return geo_grid


def load_climate_data_for_single_value(data_config: ClimateDataConfig, month: int) -> GeoGrid:
    if isinstance(data_config, DerivedClimateDataConfig):
        return _load_derived_climate_data(data_config, month, apply_downsampling=False)
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


def load_climate_data_for_difference(
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


def load_climate_data_for_difference_single_value(
    historical_config: ClimateDataConfig, future_config: FutureClimateDataConfig, month: int
) -> GeoGrid:
    future_grid = load_climate_data_for_single_value(future_config, month)

    if future_config.climate_model == ClimateModel.ENSEMBLE_STD_DEV:
        return future_grid

    historical_grid = load_climate_data_for_single_value(historical_config, month)

    if not numpy.allclose(historical_grid.lon_range, future_grid.lon_range) or not numpy.allclose(
        historical_grid.lat_range, future_grid.lat_range
    ):
        raise ValueError("Coordinate arrays don't match between historical and future data")

    return future_grid.difference(historical_grid)
