import numpy

from climatemaps.datasets import ClimateDataConfig, DataFormat, FutureClimateDataConfig
from climatemaps.download import ensure_data_available
from climatemaps.geotiff import read_geotiff_future, read_geotiff_history
from climatemaps.geogrid import GeoGrid
from climatemaps.logger import logger


def read_ippc_grid(filepath, monthnr):
    ncols = 720
    nrows = 360
    digits = 5

    with open(filepath, "r") as filein:
        lines = filein.readlines()
        line_n = 0
        grid_size = 0.50
        # TODO: check if the coordinates should not be in the middle of the grid cell
        xmin = 0.25 - 180
        xmax = 360.25 - 180
        ymin = -89.75
        ymax = 90.25

        lonrange = numpy.arange(xmin, xmax, grid_size)
        latrange = numpy.arange(ymin, ymax, grid_size)
        Z = numpy.zeros((int(latrange.shape[0]), int(lonrange.shape[0])))

        i = 0
        rown = 0

        for line in lines:
            line_n += 1
            if line_n < 3:  # skip header
                continue
            if rown < (monthnr - 1) * nrows or rown >= monthnr * nrows:  # read one month
                rown += 1
                continue

            value = ""
            counter = 1
            j = 0
            for char in line:
                value += char
                if counter % digits == 0:
                    value = float(value)
                    if value == -9999:
                        value = numpy.nan
                    Z[i][j] = value
                    value = ""
                    j += 1
                counter += 1
            i += 1
            rown += 1

        Z_new = numpy.zeros((int(latrange.shape[0]), int(lonrange.shape[0])))
        half_size = int(Z.shape[1] / 2)
        for i in range(0, Z.shape[0]):
            for j in range(0, Z.shape[1]):
                if lonrange[j] >= 0.0:
                    Z_new[i][j - half_size] = Z[i][j]
                else:
                    Z_new[i][j + half_size] = Z[i][j]

        latrange = numpy.flip(latrange)

    return latrange, lonrange, Z_new


def import_ascii_grid_generic(filepath, no_data_value=9e20):
    with open(filepath, "r") as filein:
        lines = filein.readlines()
        line_n = 0
        grid_size = 0.083333333
        xmin = -180.0
        xmax = 180.0
        ymin = -90.0
        ymax = 90.0

        lonrange = numpy.arange(xmin, xmax, grid_size)
        latrange = numpy.arange(ymin, ymax, grid_size)
        Z = numpy.zeros((int(latrange.shape[0]), int(lonrange.shape[0])))

        i = 0
        for line in lines:
            line_n += 1
            if line_n < 7:  # skip header
                continue

            j = 0
            values = line.split()
            for value in values:
                value = float(value)
                if value == no_data_value:
                    value = numpy.nan
                Z[i][j] = value
                j += 1
            i += 1

    print("import_ascii_grid_generic() - END")
    return latrange, lonrange, Z


def load_climate_data(data_config: ClimateDataConfig, month: int) -> GeoGrid:
    try:
        ensure_data_available(data_config)

        if data_config.format == DataFormat.IPCC_GRID:
            lat_range, lon_range, values = read_ippc_grid(data_config.filepath, month)
        elif data_config.format == DataFormat.GEOTIFF_WORLDCLIM_CMIP6:
            lon_range, lat_range, values = read_geotiff_future(data_config.filepath, month)
        elif data_config.format == DataFormat.GEOTIFF_WORLDCLIM_HISTORY:
            lon_range, lat_range, values = read_geotiff_history(data_config.filepath, month)
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
