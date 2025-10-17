import os
from typing import Tuple

import numpy as np
import rasterio


def _process_coordinate_arrays(transform, width: int, height: int) -> Tuple[np.ndarray, np.ndarray]:
    # Create coordinate arrays using rasterio's transform
    lon_array = np.linspace(transform.c, transform.c + width * transform.a, width, endpoint=False)
    lat_array = np.linspace(transform.f, transform.f + height * transform.e, height, endpoint=False)

    bin_width = 360.0 / len(lon_array)
    lon_array += bin_width / 2
    lat_array -= bin_width / 2

    return lon_array, lat_array


def read_geotiff_future(filepath: str, month: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    assert month > 0 and month <= 12, f"Month must be between 1 and 12, got {month}"

    with rasterio.open(filepath) as src:
        array = src.read(month).astype(float)

        lon_array, lat_array = _process_coordinate_arrays(src.transform, src.width, src.height)

    return lon_array, lat_array, array


def read_geotiff_history(filepath: str, month: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    data_type = filepath.split("/")[-1]
    filepath = os.path.join(filepath, f"{data_type}_{month:02d}.tif")

    with rasterio.open(filepath) as src:
        array = src.read(1).astype(float)

        array[array == -32768] = np.nan  # Sea
        array[array <= -300] = np.nan  # Sea

        lon_array, lat_array = _process_coordinate_arrays(src.transform, src.width, src.height)

    return lon_array, lat_array, array


def read_geotiff_cru_ts(filepath: str, month: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    data_type = filepath.split("/")[-1]
    filepath = os.path.join(filepath, f"{data_type}_{month:02d}.tif")

    with rasterio.open(filepath) as src:
        array = src.read(1).astype(float)

        array[array == 254] = np.nan  # NoData value
        array[array <= -9000] = np.nan  # Invalid values

        lon_array, lat_array = _process_coordinate_arrays(src.transform, src.width, src.height)

    return lon_array, lat_array, array
