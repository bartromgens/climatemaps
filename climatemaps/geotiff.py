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
    Read CHELSA data. CHELSA files contain monthly data in separate bands.
    """
    assert month > 0 and month <= 12, f"Month must be between 1 and 12, got {month}"

    logger.info(f"Loading CHELSA data from {filepath}, month {month}")

    with rasterio.open(filepath) as src:
        # CHELSA files have monthly data in separate bands
        array = src.read(month).astype(float)

        # Handle NoData values (typically -9999 or similar)
        array[array <= -9999] = np.nan
        array[array == -32768] = np.nan  # Common NoData value

        logger.debug(f"CHELSA data loaded: shape {array.shape}, bounds {src.bounds}")

        lon_array, lat_array = _process_coordinate_arrays(src.transform, src.width, src.height)

        # Apply high-resolution land-sea mask to remove sea areas
        land_mask_path = "data/raw/land_masks/gshhs_land_water_mask_3km_i.tif"
        if os.path.exists(land_mask_path):
            logger.info(f"Applying land-sea mask from {land_mask_path}")
            with rasterio.open(land_mask_path) as mask_src:
                # Read the land mask
                land_mask_data = mask_src.read(1)
                logger.debug(f"Land mask shape: {land_mask_data.shape}, bounds: {mask_src.bounds}")

                # Interpolate the land mask to match CHELSA coordinates using efficient method
                logger.info("Interpolating land mask to match CHELSA coordinates")

                # Use efficient coordinate-based interpolation
                from scipy.interpolate import RegularGridInterpolator

                # Create coordinate arrays for the land mask
                mask_lon_array = np.linspace(
                    mask_src.bounds.left, mask_src.bounds.right, mask_src.width, endpoint=False
                )
                # mask_lon_array = mask_lon_array + 360

                mask_lat_array = np.linspace(
                    mask_src.bounds.top, mask_src.bounds.bottom, mask_src.height, endpoint=False
                )

                # Create interpolator for the land mask
                interpolator = RegularGridInterpolator(
                    (mask_lat_array, mask_lon_array),
                    land_mask_data,
                    method="nearest",
                    bounds_error=False,
                    fill_value=0,
                )

                # Create coordinate grids for CHELSA data
                lon_grid, lat_grid = np.meshgrid(lon_array, lat_array)

                # Interpolate using the efficient RegularGridInterpolator
                interpolated_mask = interpolator((lat_grid, lon_grid)).astype(np.uint8)

                # Apply the land mask (1 = land, 0 = sea)
                land_pixels = np.sum(interpolated_mask == 1)
                sea_pixels = np.sum(interpolated_mask == 0)
                logger.info(
                    f"Land-sea mask applied: {land_pixels} land pixels, {sea_pixels} sea pixels"
                )

                array[interpolated_mask == 0] = np.nan

                # Log final statistics
                final_land_pixels = np.count_nonzero(~np.isnan(array))
                final_sea_pixels = np.count_nonzero(np.isnan(array))
                logger.info(
                    f"After masking: {final_land_pixels} land pixels, {final_sea_pixels} sea pixels ({final_sea_pixels/array.size*100:.1f}% masked)"
                )
        else:
            logger.error(f"Land mask file not found at {land_mask_path}, skipping sea masking")

    return lon_array, lat_array, array
