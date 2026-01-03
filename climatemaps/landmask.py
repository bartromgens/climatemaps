import os

import numpy as np
import rasterio
import rasterio.windows
from scipy.interpolate import RegularGridInterpolator

from climatemaps.geogrid import GeoGrid
from climatemaps.logger import logger


def _calculate_bounded_bbox_with_margin(
    geo_grid: GeoGrid, margin: float = 1.0
) -> tuple[float, float, float, float]:
    return (
        max(-180, geo_grid.llcrnrlon - margin),
        max(-90, geo_grid.llcrnrlat - margin),
        min(180, geo_grid.urcrnrlon + margin),
        min(90, geo_grid.urcrnrlat + margin),
    )


def _calculate_safe_window(
    window: rasterio.windows.Window, mask_src: rasterio.DatasetReader
) -> rasterio.windows.Window:
    col_off = max(0, int(np.floor(window.col_off)))
    row_off = max(0, int(np.floor(window.row_off)))

    return rasterio.windows.Window(
        col_off=col_off,
        row_off=row_off,
        width=min(
            mask_src.width - col_off,
            int(np.ceil(window.width)),
        ),
        height=min(
            mask_src.height - row_off,
            int(np.ceil(window.height)),
        ),
    )


def _create_mask_coordinate_arrays(
    window: rasterio.windows.Window, transform: rasterio.Affine, is_point_registration: bool
) -> tuple[np.ndarray, np.ndarray]:
    pixel_width = transform.a
    pixel_height = abs(transform.e)

    if is_point_registration:
        mask_lon_array = np.linspace(
            transform.c,
            transform.c + (window.width - 1) * transform.a,
            window.width,
        )
        mask_lat_array = np.linspace(
            transform.f,
            transform.f + (window.height - 1) * transform.e,
            window.height,
        )
    else:
        mask_lon_array = np.linspace(
            transform.c,
            transform.c + window.width * transform.a,
            window.width,
            endpoint=False,
        )
        mask_lon_array += pixel_width / 2

        mask_lat_array = np.linspace(
            transform.f,
            transform.f + window.height * transform.e,
            window.height,
            endpoint=False,
        )
        mask_lat_array -= pixel_height / 2

    return mask_lon_array, mask_lat_array


def _interpolate_mask_to_grid(
    land_mask_data: np.ndarray,
    mask_lon_array: np.ndarray,
    mask_lat_array: np.ndarray,
    geo_grid: GeoGrid,
) -> np.ndarray:
    interpolator = RegularGridInterpolator(
        (mask_lat_array, mask_lon_array),
        land_mask_data,
        method="nearest",
        bounds_error=False,
        fill_value=0,
    )

    lon_grid, lat_grid = np.meshgrid(geo_grid.lon_range, geo_grid.lat_range)
    return interpolator((lat_grid, lon_grid)).astype(np.uint8)


def _apply_mask_and_log_stats(geo_grid: GeoGrid, interpolated_mask: np.ndarray) -> np.ndarray:
    land_pixels = np.sum(interpolated_mask == 1)
    sea_pixels = np.sum(interpolated_mask == 0)
    logger.info(f"Land-sea mask applied: {land_pixels} land pixels, {sea_pixels} sea pixels")

    new_values = geo_grid.values.copy()
    new_values[interpolated_mask == 0] = np.nan

    final_land_pixels = np.count_nonzero(~np.isnan(new_values))
    final_sea_pixels = np.count_nonzero(np.isnan(new_values))
    logger.info(
        f"After masking: {final_land_pixels} land pixels, {final_sea_pixels} sea pixels "
        f"({final_sea_pixels/new_values.size*100:.1f}% masked)"
    )

    return new_values


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
        data_bbox_with_margin = _calculate_bounded_bbox_with_margin(geo_grid)
        window = rasterio.windows.from_bounds(*data_bbox_with_margin, transform=mask_src.transform)
        window_int = _calculate_safe_window(window, mask_src)

        logger.info(
            f"Reading land mask window: col={window_int.col_off}, row={window_int.row_off}, "
            f"width={window_int.width}, height={window_int.height} "
            f"(data bounds: {geo_grid.llcrnrlon:.2f}, {geo_grid.llcrnrlat:.2f}, "
            f"{geo_grid.urcrnrlon:.2f}, {geo_grid.urcrnrlat:.2f})"
        )

        land_mask_data = mask_src.read(1, window=window_int)
        logger.debug(
            f"Land mask window shape: {land_mask_data.shape} "
            f"(full mask: {mask_src.width}x{mask_src.height})"
        )

        window_transform = rasterio.windows.transform(window_int, mask_src.transform)

        logger.info("Interpolating land mask to match data coordinates")
        area_or_point = mask_src.tags().get("AREA_OR_POINT")
        is_point_registration = area_or_point == "Point"

        mask_lon_array, mask_lat_array = _create_mask_coordinate_arrays(
            window_int, window_transform, is_point_registration
        )

        interpolated_mask = _interpolate_mask_to_grid(
            land_mask_data, mask_lon_array, mask_lat_array, geo_grid
        )

        new_values = _apply_mask_and_log_stats(geo_grid, interpolated_mask)

    return GeoGrid(lon_range=geo_grid.lon_range, lat_range=geo_grid.lat_range, values=new_values)
