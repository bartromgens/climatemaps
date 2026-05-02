import os
from pathlib import Path
from typing import Tuple

import numpy as np
import rasterio
import rasterio.errors
from rasterio.windows import Window, from_bounds
from climatemaps.bbox import BoundingBox
from climatemaps.logger import logger


def verify_geotiff_file(filepath: str | Path) -> bool:
    """
    Verify that a GeoTIFF file is valid and can be read.
    Returns True if the file is valid, False otherwise.
    Checks multiple locations to detect incomplete/corrupt downloads.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return False

    try:
        with rasterio.open(filepath) as src:
            # Try to read metadata
            _ = src.width
            _ = src.height
            _ = src.count
            _ = src.transform
            _ = src.bounds

            # Read a small sample window instead of the entire file for faster verification
            # This catches corruption issues without loading the full file
            sample_size = min(10, src.width, src.height)

            # Test reading from beginning
            window_start = Window(0, 0, sample_size, sample_size)
            array = src.read(1, window=window_start)
            if array.size == 0:
                return False

            # Test reading from middle (catches incomplete downloads)
            if src.width > sample_size * 2 and src.height > sample_size * 2:
                mid_col = (src.width - sample_size) // 2
                mid_row = (src.height - sample_size) // 2
                window_mid = Window(mid_col, mid_row, sample_size, sample_size)
                array = src.read(1, window=window_mid)
                if array.size == 0:
                    return False

            # Test reading from near end (catches truncated files)
            if src.width > sample_size and src.height > sample_size:
                end_col = max(0, src.width - sample_size)
                end_row = max(0, src.height - sample_size)
                window_end = Window(end_col, end_row, sample_size, sample_size)
                array = src.read(1, window=window_end)
                if array.size == 0:
                    return False

        return True
    except (rasterio.errors.RasterioIOError, OSError, Exception) as e:
        logger.warning(f"GeoTIFF file verification failed for {filepath}: {e}")
        return False


def _process_coordinate_arrays(
    transform, width: int, height: int, area_or_point: str | None = None
) -> Tuple[np.ndarray, np.ndarray]:
    # GeoTIFF pixel registration convention:
    # - "Area" (default): transform origin is upper-left CORNER of upper-left pixel
    # - "Point": transform origin is the CENTER of the upper-left pixel
    #
    # transform.c = x (longitude) origin
    # transform.f = y (latitude) origin
    # transform.a = pixel width (longitude)
    # transform.e = pixel height (latitude, typically negative for north-up images)

    is_point_registration = area_or_point == "Point"

    if is_point_registration:
        # Point registration: transform origin is already at pixel center
        lon_array = np.linspace(transform.c, transform.c + (width - 1) * transform.a, width)
        lat_array = np.linspace(transform.f, transform.f + (height - 1) * transform.e, height)
        logger.debug(f"Using Point pixel registration (origin at pixel center)")
    else:
        # Area registration (default): transform origin is at pixel corner
        lon_array = np.linspace(
            transform.c, transform.c + width * transform.a, width, endpoint=False
        )
        lat_array = np.linspace(
            transform.f, transform.f + height * transform.e, height, endpoint=False
        )
        # Shift from corner to pixel center
        lon_array += transform.a / 2
        lat_array += transform.e / 2
        logger.debug(f"Using Area pixel registration (origin at pixel corner)")

    logger.debug(
        f"GeoTIFF transform: origin=({transform.c:.6f}, {transform.f:.6f}), "
        f"pixel_size=({transform.a:.6f}, {transform.e:.6f})"
    )
    logger.debug(
        f"Pixel centers: lon=[{lon_array[0]:.6f}..{lon_array[-1]:.6f}], "
        f"lat=[{lat_array[0]:.6f}..{lat_array[-1]:.6f}]"
    )

    return lon_array, lat_array


def _get_area_or_point(src) -> str | None:
    tags = src.tags()
    return tags.get("AREA_OR_POINT")


def _read_with_bbox(
    src, band: int, bbox: BoundingBox | None = None
) -> Tuple[np.ndarray, int, int, int, int]:
    if bbox is None:
        array = src.read(band).astype(float)
        return array, 0, 0, src.width, src.height

    window = from_bounds(
        bbox.lon_min, bbox.lat_min, bbox.lon_max, bbox.lat_max, transform=src.transform
    )

    window_int = Window(
        col_off=max(0, int(np.floor(window.col_off))),
        row_off=max(0, int(np.floor(window.row_off))),
        width=min(src.width - max(0, int(np.floor(window.col_off))), int(np.ceil(window.width))),
        height=min(src.height - max(0, int(np.floor(window.row_off))), int(np.ceil(window.height))),
    )

    logger.info(
        f"Reading window: col={window_int.col_off}, row={window_int.row_off}, "
        f"width={window_int.width}, height={window_int.height} "
        f"(bbox: {bbox.lon_min:.2f}, {bbox.lat_min:.2f}, {bbox.lon_max:.2f}, {bbox.lat_max:.2f})"
    )

    array = src.read(band, window=window_int).astype(float)
    return array, window_int.col_off, window_int.row_off, window_int.width, window_int.height


def read_geotiff_future(
    filepath: str, month: int, bbox: BoundingBox | None = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    assert month > 0 and month <= 12, f"Month must be between 1 and 12, got {month}"

    with rasterio.open(filepath) as src:
        array, col_off, row_off, width, height = _read_with_bbox(src, month, bbox)
        area_or_point = _get_area_or_point(src)

        if bbox is not None:
            window_transform = rasterio.windows.transform(
                Window(col_off, row_off, width, height), src.transform
            )
            lon_array, lat_array = _process_coordinate_arrays(
                window_transform, width, height, area_or_point
            )
        else:
            lon_array, lat_array = _process_coordinate_arrays(
                src.transform, src.width, src.height, area_or_point
            )

    return lon_array, lat_array, array


def read_geotiff_history(
    filepath: str, month: int, bbox: BoundingBox | None = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    data_type = filepath.split("/")[-1]
    filepath = os.path.join(filepath, f"{data_type}_{month:02d}.tif")

    with rasterio.open(filepath) as src:
        array, col_off, row_off, width, height = _read_with_bbox(src, 1, bbox)

        array[array == -32768] = np.nan  # Sea
        array[array <= -300] = np.nan  # Sea

        area_or_point = _get_area_or_point(src)

        if bbox is not None:
            window_transform = rasterio.windows.transform(
                Window(col_off, row_off, width, height), src.transform
            )
            lon_array, lat_array = _process_coordinate_arrays(
                window_transform, width, height, area_or_point
            )
        else:
            lon_array, lat_array = _process_coordinate_arrays(
                src.transform, src.width, src.height, area_or_point
            )

    return lon_array, lat_array, array


def read_geotiff_cru_ts(
    filepath: str, month: int, bbox: BoundingBox | None = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    data_type = filepath.split("/")[-1]
    filepath = os.path.join(filepath, f"{data_type}_{month:02d}.tif")

    with rasterio.open(filepath) as src:
        array, col_off, row_off, width, height = _read_with_bbox(src, 1, bbox)

        array[array == 254] = np.nan  # NoData value
        array[array <= -9000] = np.nan  # Invalid values

        area_or_point = _get_area_or_point(src)

        if bbox is not None:
            window_transform = rasterio.windows.transform(
                Window(col_off, row_off, width, height), src.transform
            )
            lon_array, lat_array = _process_coordinate_arrays(
                window_transform, width, height, area_or_point
            )
        else:
            lon_array, lat_array = _process_coordinate_arrays(
                src.transform, src.width, src.height, area_or_point
            )

    return lon_array, lat_array, array


def read_geotiff_chelsa(
    filepath: str, month: int, bbox: BoundingBox | None = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    assert month > 0 and month <= 12, f"Month must be between 1 and 12, got {month}"

    data_type = filepath.split("/")[-1]
    formatted_filepath = os.path.join(filepath, f"{data_type}_{month:02d}.tif")

    logger.info(f"Loading CHELSA data from {formatted_filepath}, month {month}")

    with rasterio.open(formatted_filepath) as src:
        array, col_off, row_off, width, height = _read_with_bbox(src, 1, bbox)
        logger.debug(f"CHELSA data loaded: shape {array.shape}, bounds {src.bounds}")
        area_or_point = _get_area_or_point(src)

        if bbox is not None:
            window_transform = rasterio.windows.transform(
                Window(col_off, row_off, width, height), src.transform
            )
            lon_array, lat_array = _process_coordinate_arrays(
                window_transform, width, height, area_or_point
            )
        else:
            lon_array, lat_array = _process_coordinate_arrays(
                src.transform, src.width, src.height, area_or_point
            )

    return lon_array, lat_array, array


def read_geotiff_chelsa_point(filepath: str, month: int, lon: float, lat: float) -> float:
    assert month > 0 and month <= 12, f"Month must be between 1 and 12, got {month}"

    data_type = filepath.split("/")[-1]
    formatted_filepath = os.path.join(filepath, f"{data_type}_{month:02d}.tif")

    with rasterio.open(formatted_filepath) as src:
        row, col = src.index(lon, lat)

        if row < 0 or row >= src.height or col < 0 or col >= src.width:
            raise ValueError(f"Coordinates ({lon}, {lat}) are outside the raster bounds")

        window = Window(col, row, 3, 3)

        col_start = max(0, col - 1)
        row_start = max(0, row - 1)
        col_end = min(src.width, col + 2)
        row_end = min(src.height, row + 2)

        window = Window(col_start, row_start, col_end - col_start, row_end - row_start)
        data = src.read(1, window=window).astype(float)

        local_col = col - col_start
        local_row = row - row_start

        value = float(data[local_row, local_col])

    return value
