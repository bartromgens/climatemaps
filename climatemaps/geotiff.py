import os
from typing import Tuple

import numpy as np
import rasterio
from climatemaps.logger import logger


def _process_coordinate_arrays(transform, width: int, height: int) -> Tuple[np.ndarray, np.ndarray]:
    # Create coordinate arrays using rasterio's transform
    # The transform gives us the coordinates of the pixel centers
    lon_array = np.linspace(transform.c, transform.c + width * transform.a, width, endpoint=False)
    lat_array = np.linspace(transform.f, transform.f + height * transform.e, height, endpoint=False)

    # For regular grids, we can use the transform parameters directly
    # transform.a is the pixel width in longitude, transform.e is the pixel height in latitude
    lon_array += transform.a / 2  # Shift to pixel center
    lat_array += transform.e / 2  # Shift to pixel center

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


def read_geotiff_chelsa(filepath: str, month: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Read CHELSA data. CHELSA files are named with different months (01, 02, 03, etc.).
    """
    assert month > 0 and month <= 12, f"Month must be between 1 and 12, got {month}"

    # Format the filepath template with the month parameter
    data_type = filepath.split("/")[-1]
    formatted_filepath = os.path.join(filepath, f"{data_type}_{month:02d}.tif")

    logger.info(f"Loading CHELSA data from {formatted_filepath}, month {month}")

    with rasterio.open(formatted_filepath) as src:
        array = src.read(1).astype(float)
        logger.debug(f"CHELSA data loaded: shape {array.shape}, bounds {src.bounds}")
        lon_array, lat_array = _process_coordinate_arrays(src.transform, src.width, src.height)

    return lon_array, lat_array, array
