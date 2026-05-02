#!/usr/bin/env python3
"""Generate static SEO/social preview images for each climate variable and month.

For each (variable, month) pair this script renders a single PNG/JPG showing the
climate data overlaid on a Natural Earth basemap, suitable for:
  - Google Images indexing (per-route landing-page <img>)
  - Open Graph / Twitter card previews
  - Crawlers that don't render JavaScript

Output goes to client/public/assets/previews/<variable-path>-<month-name>.jpg

Usage:
    python scripts/create_seo_previews.py
    python scripts/create_seo_previews.py --variable T_MAX --month 1
    python scripts/create_seo_previews.py --processes 4 --force-recreate
"""

from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.patheffects as PathEffects
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.ticker import LogFormatter, LogLocator, MaxNLocator

module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

from climatemaps.data import load_climate_data
from climatemaps.datasets import (
    ClimateDataConfig,
    ClimateVarKey,
    HISTORIC_DATA_SETS,
    SpatialResolution,
)
from climatemaps.logger import logger


REPO_ROOT = Path(module_dir)
OUTPUT_DIR = REPO_ROOT / "client" / "public" / "assets" / "previews"

DEFAULT_WIDTH_PX = 2400
DEFAULT_HEIGHT_PX = 1260
DEFAULT_DPI = 100

MONTH_NAMES: dict[int, str] = {
    1: "january",
    2: "february",
    3: "march",
    4: "april",
    5: "may",
    6: "june",
    7: "july",
    8: "august",
    9: "september",
    10: "october",
    11: "november",
    12: "december",
}

# Mirrors CLIMATE_VARIABLE_ROUTES in client/src/app/app.routes.ts so generated
# filenames line up with the Angular routes that will reference them.
VARIABLE_PATHS: dict[ClimateVarKey, str] = {
    ClimateVarKey.T_MAX: "temperature",
    ClimateVarKey.T_MIN: "temperature-min",
    ClimateVarKey.PRECIPITATION: "precipitation",
    ClimateVarKey.CLOUD_COVER: "cloud-cover",
    ClimateVarKey.RADIATION: "radiation",
    ClimateVarKey.DIURNAL_TEMP_RANGE: "diurnal-temperature-range",
    ClimateVarKey.VAPOUR_PRESSURE: "vapour-pressure",
    ClimateVarKey.WIND_SPEED: "wind-speed",
    ClimateVarKey.RELATIVE_HUMIDITY: "relative-humidity",
    ClimateVarKey.POTENTIAL_EVAPOTRANSPIRATION: "potential-evapotranspiration",
    ClimateVarKey.MOISTURE_INDEX: "moisture-index",
    ClimateVarKey.VAPOUR_PRESSURE_DEFICIT: "vapour-pressure-deficit",
}

# Human-readable variable names used in the generated <h1>/title overlay.
VARIABLE_TITLES: dict[ClimateVarKey, str] = {
    ClimateVarKey.T_MAX: "Average Temperature (Day)",
    ClimateVarKey.T_MIN: "Average Temperature (Night)",
    ClimateVarKey.PRECIPITATION: "Average Precipitation",
    ClimateVarKey.CLOUD_COVER: "Average Cloud Cover",
    ClimateVarKey.RADIATION: "Average Solar Radiation",
    ClimateVarKey.DIURNAL_TEMP_RANGE: "Diurnal Temperature Range",
    ClimateVarKey.VAPOUR_PRESSURE: "Vapour Pressure",
    ClimateVarKey.WIND_SPEED: "Average Wind Speed",
    ClimateVarKey.RELATIVE_HUMIDITY: "Relative Humidity",
    ClimateVarKey.POTENTIAL_EVAPOTRANSPIRATION: "Potential Evapotranspiration",
    ClimateVarKey.MOISTURE_INDEX: "Moisture Index",
    ClimateVarKey.VAPOUR_PRESSURE_DEFICIT: "Vapour Pressure Deficit",
}


def _resolution_minutes(resolution: SpatialResolution) -> float:
    return float(resolution.value.rstrip("m"))


def _select_lowest_resolution_dataset(
    variable: ClimateVarKey,
) -> ClimateDataConfig | None:
    """Pick the coarsest historic dataset for a variable (fast to render)."""
    candidates = [
        cfg for cfg in HISTORIC_DATA_SETS if cfg.variable_type == variable
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda cfg: _resolution_minutes(cfg.resolution_input))


def _output_path(variable: ClimateVarKey, month: int) -> Path:
    return OUTPUT_DIR / f"{VARIABLE_PATHS[variable]}-{MONTH_NAMES[month]}.jpg"


def _render_preview(
    variable: ClimateVarKey,
    month: int,
    width_px: int,
    height_px: int,
    dpi: int,
    output_path: Path,
) -> None:
    config = _select_lowest_resolution_dataset(variable)
    if config is None:
        raise RuntimeError(f"No historic dataset found for {variable.value}")

    logger.info(
        f"Loading data for {variable.value} month {month} "
        f"(resolution={config.resolution_input.value})"
    )
    geo_grid = load_climate_data(config, month)

    contour_config = config.contour_config
    values = geo_grid.clipped_values(contour_config.level_lower, contour_config.level_upper)

    fig_w = width_px / dpi
    fig_h = height_px / dpi
    figure = Figure(figsize=(fig_w, fig_h), dpi=dpi)

    ax = figure.add_axes(
        [0.0, 0.0, 1.0, 1.0],
        projection=ccrs.PlateCarree(),
    )
    ax.set_global()
    ax.set_extent([-180, 180, -60, 85], crs=ccrs.PlateCarree())

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.add_feature(cfeature.OCEAN, facecolor="#cfe5ee", zorder=0)
    ax.add_feature(cfeature.LAND, facecolor="#f1ece1", zorder=0)

    extent = [
        geo_grid.llcrnrlon,
        geo_grid.urcrnrlon,
        geo_grid.llcrnrlat,
        geo_grid.urcrnrlat,
    ]
    ax.imshow(
        values,
        extent=extent,
        transform=ccrs.PlateCarree(),
        cmap=contour_config.colormap,
        norm=contour_config.norm,
        origin="upper",
        interpolation="nearest",
        alpha=0.85,
        zorder=1,
    )

    ax.add_feature(
        cfeature.COASTLINE.with_scale("110m"),
        edgecolor="#3c3c3c",
        linewidth=0.5,
        zorder=2,
    )
    ax.add_feature(
        cfeature.BORDERS.with_scale("110m"),
        edgecolor="#5a5a5a",
        linewidth=0.3,
        zorder=2,
    )

    _add_overlay_text(figure, variable, month, config)
    _add_colorbar(figure, contour_config)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        output_path,
        dpi=dpi,
        format="jpg",
        pil_kwargs={"quality": 85, "optimize": True, "progressive": True},
    )
    plt.close(figure)
    logger.info(f"Wrote {output_path.relative_to(REPO_ROOT)}")


_SOURCE_LABELS: dict[str, str] = {
    "worldclim.org": "WorldClim v2.1",
    "chelsa-climate.org": "CHELSA",
}


def _source_label(source_url: str) -> str:
    for domain, label in _SOURCE_LABELS.items():
        if domain in source_url:
            return label
    return source_url


def _add_overlay_text(
    figure: Figure,
    variable: ClimateVarKey,
    month: int,
    config: ClimateDataConfig,
) -> None:
    title = VARIABLE_TITLES[variable]
    month_name = MONTH_NAMES[month].capitalize()
    year_range = f"{config.year_range[0]}\u2013{config.year_range[1]}"
    source = _source_label(config.source)

    figure.text(
        0.02,
        0.95,
        f"{title} – {month_name}",
        fontsize=22,
        fontweight="bold",
        color="white",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#1976d2", edgecolor="none"),
    )
    figure.text(
        0.02,
        0.88,
        f"World map · {year_range} climatology",
        fontsize=12,
        color="white",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#1976d2", edgecolor="none"),
    )
    figure.text(
        0.98,
        0.025,
        "openclimatemap.org",
        fontsize=11,
        color="white",
        fontweight="bold",
        ha="right",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#222", edgecolor="none"),
    )
    figure.text(
        0.98,
        0.075,
        f"Data: {source}",
        fontsize=9,
        color="#222",
        ha="right",
        va="bottom",
    )


def _add_colorbar(figure: Figure, contour_config) -> None:
    # Horizontal colorbar at bottom-left: [left, bottom, width, height] in figure fraction
    bg_ax = figure.add_axes([0.02, 0.04, 0.30, 0.065])
    bg_ax.set_facecolor("none")
    bg_ax.set_xticks([])
    bg_ax.set_yticks([])
    for spine in bg_ax.spines.values():
        spine.set_visible(False)

    cbar_ax = figure.add_axes([0.04, 0.055, 0.26, 0.022])
    cbar_ax.set_facecolor("none")
    sm = plt.cm.ScalarMappable(cmap=contour_config.colormap, norm=contour_config.norm)
    sm.set_array(np.array([]))
    cbar = figure.colorbar(sm, cax=cbar_ax, orientation="horizontal")

    if contour_config.log_scale:
        cbar.locator = LogLocator(subs="all", numticks=20)
        cbar.formatter = LogFormatter(base=10, labelOnlyBase=False, minor_thresholds=(2, 0.4))
    else:
        cbar.locator = MaxNLocator(nbins=12)
    cbar.update_ticks()

    cbar.ax.tick_params(labelsize=10, colors="#222")
    cbar.outline.set_edgecolor("#222")
    cbar.set_label(contour_config.unit, color="#222", fontsize=11, labelpad=3)
    cbar.ax.set_title(contour_config.title, fontsize=11, fontweight="bold", color="#222", pad=4)


def _process_task(
    variable_value: str,
    month: int,
    width_px: int,
    height_px: int,
    dpi: int,
    force_recreate: bool,
) -> str:
    variable = ClimateVarKey(variable_value)
    output_path = _output_path(variable, month)

    if output_path.exists() and not force_recreate:
        logger.info(f"Skip (exists): {output_path.relative_to(REPO_ROOT)}")
        return f"skip:{variable.value}-{month}"

    try:
        _render_preview(variable, month, width_px, height_px, dpi, output_path)
        return f"ok:{variable.value}-{month}"
    except Exception as exc:
        logger.exception(
            f"Failed to render preview for {variable.value} month {month}: {exc}"
        )
        return f"fail:{variable.value}-{month}"


def main(
    variables: list[ClimateVarKey],
    months: list[int],
    width_px: int,
    height_px: int,
    dpi: int,
    processes: int,
    force_recreate: bool,
) -> None:
    tasks = [(v.value, m) for v in variables for m in months]
    logger.info(
        f"Generating {len(tasks)} preview(s) -> {OUTPUT_DIR.relative_to(REPO_ROOT)}"
    )

    if processes <= 1:
        for variable_value, month in tasks:
            _process_task(variable_value, month, width_px, height_px, dpi, force_recreate)
        return

    with ProcessPoolExecutor(max_workers=processes) as executor:
        futures = [
            executor.submit(
                _process_task,
                variable_value,
                month,
                width_px,
                height_px,
                dpi,
                force_recreate,
            )
            for variable_value, month in tasks
        ]
        for future in as_completed(futures):
            future.result()


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate per-variable, per-month SEO preview images."
    )
    parser.add_argument(
        "--variable",
        type=str,
        choices=[v.value for v in VARIABLE_PATHS],
        action="append",
        help="Variable to render. May be passed multiple times. Defaults to all.",
    )
    parser.add_argument(
        "--month",
        type=int,
        choices=range(1, 13),
        action="append",
        metavar="1-12",
        help="Month to render (1-12). May be passed multiple times. Defaults to all.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=DEFAULT_WIDTH_PX,
        help=f"Output width in pixels (default: {DEFAULT_WIDTH_PX}, Open Graph spec).",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=DEFAULT_HEIGHT_PX,
        help=f"Output height in pixels (default: {DEFAULT_HEIGHT_PX}, Open Graph spec).",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=DEFAULT_DPI,
        help=f"Render DPI (default: {DEFAULT_DPI}).",
    )
    parser.add_argument(
        "--processes",
        type=int,
        default=1,
        help="Number of parallel processes (default: 1).",
    )
    parser.add_argument(
        "--force-recreate",
        action="store_true",
        help="Re-render images even if they already exist.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_arguments()

    selected_variables = (
        [ClimateVarKey(v) for v in args.variable]
        if args.variable
        else list(VARIABLE_PATHS.keys())
    )
    selected_months = sorted(set(args.month)) if args.month else list(range(1, 13))

    main(
        variables=selected_variables,
        months=selected_months,
        width_px=args.width,
        height_px=args.height,
        dpi=args.dpi,
        processes=args.processes,
        force_recreate=args.force_recreate,
    )
