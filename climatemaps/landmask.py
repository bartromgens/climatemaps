import os

import numpy as np
import rasterio
import rasterio.windows
from scipy.interpolate import RegularGridInterpolator

from climatemaps.geogrid import GeoGrid
from climatemaps.logger import logger


def apply_land_mask(
    geo_grid: GeoGrid, land_mask_path: str = "data/raw/land_mask_osm.tif"
) -> GeoGrid:
    """
    Apply land-sea mask to remove sea areas from the data array.

    The default land mask is derived from OpenStreetMap coastlines at ~1km resolution.
    See: https://osmdata.openstreetmap.de/data/land-polygons.html

    Args:
        geo_grid: The GeoGrid to apply the mask to
        land_mask_path: Path to the land mask file

    Returns:
        A new GeoGrid with sea areas set to NaN
    """
    if not os.path.exists(land_mask_path):
        logger.error(f"Land mask file not found at {land_mask_path}, skipping sea masking")
        return geo_grid

    logger.info(f"Applying land-sea mask from {land_mask_path}")

    with rasterio.open(land_mask_path) as mask_src:
        # Calculate window to read only the portion of the mask we need
        data_bbox_with_margin = (
            max(-180, geo_grid.llcrnrlon - 1),
            max(-90, geo_grid.llcrnrlat - 1),
            min(180, geo_grid.urcrnrlon + 1),
            min(90, geo_grid.urcrnrlat + 1),
        )

        window = rasterio.windows.from_bounds(*data_bbox_with_margin, transform=mask_src.transform)

        window_int = rasterio.windows.Window(
            col_off=max(0, int(np.floor(window.col_off))),
            row_off=max(0, int(np.floor(window.row_off))),
            width=min(
                mask_src.width - max(0, int(np.floor(window.col_off))),
                int(np.ceil(window.width)),
            ),
            height=min(
                mask_src.height - max(0, int(np.floor(window.row_off))),
                int(np.ceil(window.height)),
            ),
        )

        logger.info(
            f"Reading land mask window: col={window_int.col_off}, row={window_int.row_off}, "
            f"width={window_int.width}, height={window_int.height} "
            f"(data bounds: {geo_grid.llcrnrlon:.2f}, {geo_grid.llcrnrlat:.2f}, "
            f"{geo_grid.urcrnrlon:.2f}, {geo_grid.urcrnrlat:.2f})"
        )

        # Read only the relevant portion of the land mask
        land_mask_data = mask_src.read(1, window=window_int)
        logger.debug(
            f"Land mask window shape: {land_mask_data.shape} "
            f"(full mask: {mask_src.width}x{mask_src.height})"
        )

        # Get the transform for the windowed region
        window_transform = rasterio.windows.transform(window_int, mask_src.transform)

        # Interpolate the land mask to match data coordinates using efficient method
        logger.info("Interpolating land mask to match data coordinates")

        # Check pixel registration convention
        area_or_point = mask_src.tags().get("AREA_OR_POINT")
        is_point_registration = area_or_point == "Point"

        pixel_width = window_transform.a
        pixel_height = abs(window_transform.e)

        if is_point_registration:
            mask_lon_array = np.linspace(
                window_transform.c,
                window_transform.c + (window_int.width - 1) * window_transform.a,
                window_int.width,
            )
            mask_lat_array = np.linspace(
                window_transform.f,
                window_transform.f + (window_int.height - 1) * window_transform.e,
                window_int.height,
            )
        else:
            mask_lon_array = np.linspace(
                window_transform.c,
                window_transform.c + window_int.width * window_transform.a,
                window_int.width,
                endpoint=False,
            )
            mask_lon_array += pixel_width / 2

            mask_lat_array = np.linspace(
                window_transform.f,
                window_transform.f + window_int.height * window_transform.e,
                window_int.height,
                endpoint=False,
            )
            mask_lat_array -= pixel_height / 2

        # Create interpolator for the land mask
        interpolator = RegularGridInterpolator(
            (mask_lat_array, mask_lon_array),
            land_mask_data,
            method="nearest",
            bounds_error=False,
            fill_value=0,
        )

        # Create coordinate grids for data
        lon_grid, lat_grid = np.meshgrid(geo_grid.lon_range, geo_grid.lat_range)

        # Interpolate using the efficient RegularGridInterpolator
        interpolated_mask = interpolator((lat_grid, lon_grid)).astype(np.uint8)

        # Apply the land mask (1 = land, 0 = sea)
        land_pixels = np.sum(interpolated_mask == 1)
        sea_pixels = np.sum(interpolated_mask == 0)
        logger.info(f"Land-sea mask applied: {land_pixels} land pixels, {sea_pixels} sea pixels")

        # Create new values array with masking applied
        new_values = geo_grid.values.copy()
        new_values[interpolated_mask == 0] = np.nan

        # Log final statistics
        final_land_pixels = np.count_nonzero(~np.isnan(new_values))
        final_sea_pixels = np.count_nonzero(np.isnan(new_values))
        logger.info(
            f"After masking: {final_land_pixels} land pixels, {final_sea_pixels} sea pixels "
            f"({final_sea_pixels/new_values.size*100:.1f}% masked)"
        )

    return GeoGrid(lon_range=geo_grid.lon_range, lat_range=geo_grid.lat_range, values=new_values)
