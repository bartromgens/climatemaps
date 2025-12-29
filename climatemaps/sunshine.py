import gc
import os

import numpy as np
import numpy.typing as npt
from scipy.interpolate import RegularGridInterpolator

from climatemaps.logger import logger


DEM_PATH = "data/raw/elevation/etopo2022_30s.tif"
_terrain_grids_cache: dict[
    str,
    tuple[
        npt.NDArray[np.floating],
        npt.NDArray[np.floating],
        npt.NDArray[np.floating],
        npt.NDArray[np.floating],
    ],
] = {}


def calculate_daylight_hours(
    latitudes: npt.NDArray[np.floating], month: int
) -> npt.NDArray[np.floating]:
    days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    day_of_year = sum(days_per_month[: month - 1]) + 15

    declination = 23.45 * np.sin(np.radians(360 / 365 * (day_of_year - 81)))
    declination_rad = np.radians(declination)

    lat_rad = np.radians(latitudes)

    cos_hour_angle = -np.tan(lat_rad) * np.tan(declination_rad)
    cos_hour_angle = np.clip(cos_hour_angle, -1, 1)

    hour_angle = np.arccos(cos_hour_angle)
    daylight_hours = 2 * np.degrees(hour_angle) / 15

    return daylight_hours


def calculate_extraterrestrial_radiation(
    latitudes: npt.NDArray[np.floating], month: int
) -> npt.NDArray[np.floating]:
    """
    Calculate extraterrestrial radiation (Ra) using FAO-56 method.
    Returns Ra in W/m² (daily mean).
    """
    days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    day_of_year = sum(days_per_month[: month - 1]) + 15

    lat_rad = np.radians(latitudes)

    dr = 1 + 0.033 * np.cos(2 * np.pi * day_of_year / 365)
    declination = 0.409 * np.sin(2 * np.pi * day_of_year / 365 - 1.39)

    cos_hour_angle = -np.tan(lat_rad) * np.tan(declination)
    cos_hour_angle = np.clip(cos_hour_angle, -1, 1)
    sunset_hour_angle = np.arccos(cos_hour_angle)

    # Solar constant in MJ/m²/min (FAO-56 standard)
    Gsc = 0.0820

    # Ra in MJ/m²/day (FAO-56 formula)
    Ra_MJ = (
        (24 * 60 / np.pi)
        * Gsc
        * dr
        * (
            sunset_hour_angle * np.sin(lat_rad) * np.sin(declination)
            + np.cos(lat_rad) * np.cos(declination) * np.sin(sunset_hour_angle)
        )
    )

    # Convert MJ/m²/day to W/m² (daily mean): 1 MJ/m²/day = 11.574 W/m²
    Ra = Ra_MJ * 1_000_000 / 86400

    return np.maximum(Ra, 0)


def calculate_slope_correction_factor(
    latitudes: npt.NDArray[np.floating],
    slope: npt.NDArray[np.floating],
    aspect: npt.NDArray[np.floating],
    month: int,
) -> npt.NDArray[np.floating]:
    """
    Calculate correction factor for extraterrestrial radiation on tilted surfaces.

    For a tilted surface, Ra_slope = Ra_horizontal × correction_factor

    The correction accounts for the effective tilt toward the sun based on:
    - Latitude
    - Slope angle
    - Aspect (orientation)
    - Solar declination (varies by month)
    """
    days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    day_of_year = sum(days_per_month[: month - 1]) + 15
    declination = np.radians(23.45 * np.sin(np.radians(360 / 365 * (day_of_year - 81))))

    lat_rad = np.radians(latitudes)
    slope_rad = np.radians(slope)
    aspect_rad = np.radians(aspect)

    # For south-facing slopes in Northern Hemisphere (aspect ~ 180°),
    # the effective latitude is reduced (more perpendicular to sun)
    # For north-facing slopes, effective latitude is increased

    # Component facing the equator (south in NH, north in SH)
    # aspect=180° means south-facing, cos(180°-180°)=1
    # aspect=0° means north-facing, cos(0°-180°)=-1
    equator_facing = np.cos(aspect_rad - np.pi)

    # Effective tilt toward equator
    effective_tilt = slope_rad * equator_facing

    # Adjust for hemisphere: in SH, south-facing should decrease effective latitude
    hemisphere_sign = np.sign(latitudes)
    effective_tilt = effective_tilt * hemisphere_sign

    # Effective latitude after slope adjustment
    effective_lat = lat_rad - effective_tilt

    # Correction factor based on cosine of solar zenith angle ratio
    # At solar noon: cos(zenith) = sin(lat)*sin(decl) + cos(lat)*cos(decl)
    cos_zenith_horizontal = np.sin(lat_rad) * np.sin(declination) + np.cos(lat_rad) * np.cos(
        declination
    )
    cos_zenith_tilted = np.sin(effective_lat) * np.sin(declination) + np.cos(
        effective_lat
    ) * np.cos(declination)

    # Avoid division issues
    cos_zenith_horizontal = np.clip(cos_zenith_horizontal, 0.01, 1.0)
    cos_zenith_tilted = np.clip(cos_zenith_tilted, 0.01, 1.0)

    correction = cos_zenith_tilted / cos_zenith_horizontal

    # Limit correction to reasonable range
    return np.clip(correction, 0.2, 3.0)


def calculate_sunshine_hours(
    radiation: npt.NDArray[np.floating],
    latitudes_grid: npt.NDArray[np.floating],
    month: int,
    slope: npt.NDArray[np.floating] | None = None,
    aspect: npt.NDArray[np.floating] | None = None,
) -> npt.NDArray[np.floating]:
    """
    Calculate sunshine hours using the Ångström-Prescott formula.

    Rs/Ra = a + b × (n/N)  →  n = N × (Rs/Ra - a) / b

    Where:
    - Rs = surface solar radiation (input, W/m²)
    - Ra = extraterrestrial radiation (calculated, optionally slope-corrected)
    - n = actual sunshine hours (output)
    - N = daylight hours
    - a, b = empirical coefficients (FAO recommended: a=0.25, b=0.50)

    If slope and aspect grids are provided, Ra is corrected for tilted surfaces.
    """
    a, b = 0.25, 0.50

    daylight_hours = calculate_daylight_hours(latitudes_grid, month)
    Ra = calculate_extraterrestrial_radiation(latitudes_grid, month)

    # Apply slope correction if terrain data provided
    if slope is not None and aspect is not None:
        correction = calculate_slope_correction_factor(latitudes_grid, slope, aspect, month)
        Ra = Ra * correction

    # Avoid division by zero
    Ra_safe = np.where(Ra > 0, Ra, np.nan)

    # Calculate relative sunshine duration (n/N)
    relative_sunshine = (radiation / Ra_safe - a) / b

    # Clip to valid range [0, 1]
    relative_sunshine = np.clip(relative_sunshine, 0, 1)

    sunshine_hours = daylight_hours * relative_sunshine

    # Handle polar regions (Ra=0) by falling back to 0 sunshine
    sunshine_hours = np.where(np.isnan(sunshine_hours), 0, sunshine_hours)

    return sunshine_hours


def load_terrain_grids() -> (
    tuple[
        npt.NDArray[np.floating],
        npt.NDArray[np.floating],
        npt.NDArray[np.floating],
        npt.NDArray[np.floating],
    ]
    | None
):
    """Load DEM and compute slope/aspect grids. Returns (slope, aspect, lon_range, lat_range) or None."""
    if not os.path.exists(DEM_PATH):
        logger.warning(f"DEM file not found at {DEM_PATH}, slope correction disabled")
        return None

    cache_key = DEM_PATH
    if cache_key in _terrain_grids_cache:
        return _terrain_grids_cache[cache_key]

    import rasterio
    from scipy.ndimage import sobel

    logger.info(f"Loading DEM from {DEM_PATH} for slope/aspect calculation...")

    with rasterio.open(DEM_PATH) as src:
        dem = src.read(1).astype(np.float32)
        transform = src.transform
        bounds = src.bounds

    pixel_size_x = abs(transform[0])
    pixel_size_y = abs(transform[4])

    # Create coordinate arrays
    lon_range = np.linspace(
        bounds.left + pixel_size_x / 2, bounds.right - pixel_size_x / 2, dem.shape[1]
    )
    lat_range = np.linspace(
        bounds.top - pixel_size_y / 2, bounds.bottom + pixel_size_y / 2, dem.shape[0]
    )

    # Convert pixel size from degrees to meters (approximate at equator)
    meters_per_degree = 111320
    cell_size_x = pixel_size_x * meters_per_degree
    cell_size_y = pixel_size_y * meters_per_degree

    # Calculate gradients using Sobel filter
    dz_dx = sobel(dem, axis=1) / (8 * cell_size_x)
    dz_dy = sobel(dem, axis=0) / (8 * cell_size_y)

    # Slope in degrees
    slope = np.degrees(np.arctan(np.sqrt(dz_dx**2 + dz_dy**2)))

    # Aspect in degrees from north (0=N, 90=E, 180=S, 270=W)
    aspect = np.degrees(np.arctan2(-dz_dx, dz_dy))
    aspect = np.where(aspect < 0, aspect + 360, aspect)

    # Clean up intermediate arrays
    del dem, dz_dx, dz_dy
    gc.collect()

    logger.info(f"Terrain grids computed: slope range {slope.min():.1f}-{slope.max():.1f}°")

    _terrain_grids_cache[cache_key] = (slope, aspect, lon_range, lat_range)
    return slope, aspect, lon_range, lat_range


def interpolate_terrain_to_grid(
    target_lon: npt.NDArray[np.floating],
    target_lat: npt.NDArray[np.floating],
) -> tuple[npt.NDArray[np.floating], npt.NDArray[np.floating]] | None:
    """Interpolate terrain grids to match target coordinates."""
    terrain_data = load_terrain_grids()
    if terrain_data is None:
        return None

    slope, aspect, dem_lon, dem_lat = terrain_data

    # Create interpolators
    slope_interp = RegularGridInterpolator(
        (dem_lat, dem_lon), slope, method="linear", bounds_error=False, fill_value=0
    )
    aspect_interp = RegularGridInterpolator(
        (dem_lat, dem_lon), aspect, method="nearest", bounds_error=False, fill_value=180
    )

    # Create target coordinate grid
    lon_grid, lat_grid = np.meshgrid(target_lon, target_lat)
    coords = np.stack([lat_grid.ravel(), lon_grid.ravel()], axis=-1)

    # Interpolate
    slope_interp_values = slope_interp(coords).reshape(lat_grid.shape)
    aspect_interp_values = aspect_interp(coords).reshape(lat_grid.shape)

    return slope_interp_values, aspect_interp_values
