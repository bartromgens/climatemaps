import os

import numpy
from geotiff import GeoTiff


def _process_coordinate_arrays(geo_tiff: GeoTiff):
    lon_array, lat_array = geo_tiff.get_coord_arrays(geo_tiff.tif_bBox)
    lon_array = lon_array[0, :]
    lat_array = lat_array[:, 0]

    # Apply coordinate adjustment for consistency
    bin_width = 360.0 / len(lon_array)
    lon_array += bin_width / 2
    lat_array -= bin_width / 2

    return lon_array, lat_array


def read_geotiff_month(filepath: str, month: int):
    geo_tiff = GeoTiff(filepath)
    zarr_array = geo_tiff.read()
    array = numpy.array(zarr_array, dtype=float)
    array = array[:, :, month + 1]

    lon_array, lat_array = _process_coordinate_arrays(geo_tiff)
    return lon_array, lat_array, array


def read_geotiff_history(filepath: str, month: int):
    data_type = filepath.split("/")[-1]
    filepath = os.path.join(filepath, f"{data_type}_{month:02d}.tif")
    geo_tiff = GeoTiff(filepath)
    zarr_array = geo_tiff.read()
    array = numpy.array(zarr_array, dtype=float)

    array[array == -32768] = numpy.nan  # Sea
    array[array <= -300] = numpy.nan  # Sea

    lon_array, lat_array = _process_coordinate_arrays(geo_tiff)
    return lon_array, lat_array, array
