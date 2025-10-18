#!/usr/bin/env python3

import argparse
from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import xarray as xr

from climatemaps.logger import logger


def plot_era5_cloud_cover(
    input_file: Path,
    output_file: Path,
) -> None:
    logger.info(f"Reading GRIB file: {input_file}")

    ds = xr.open_dataset(input_file, engine="cfgrib")

    logger.info(f"Dataset variables: {list(ds.data_vars)}")
    logger.info(f"Dataset dimensions: {dict(ds.dims)}")

    tcc = ds["tcc"]

    if "number" in tcc.dims:
        logger.info(f"Computing mean across {tcc.sizes['number']} ensemble members")
        tcc = tcc.mean(dim="number")

    logger.info(f"Cloud cover data shape: {tcc.shape}")
    logger.info(f"Cloud cover data range: [{float(tcc.min()):.4f}, {float(tcc.max()):.4f}]")

    fig = plt.figure(figsize=(14, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())

    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linewidth=0.3, alpha=0.5)
    ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.5)

    im = ax.contourf(
        tcc.longitude,
        tcc.latitude,
        tcc,
        levels=20,
        cmap="Blues",
        transform=ccrs.PlateCarree(),
    )

    cbar = plt.colorbar(im, ax=ax, orientation="horizontal", pad=0.05, shrink=0.8)
    cbar.set_label("Total Cloud Cover (fraction)", fontsize=10)

    time_str = ""
    if "time" in tcc.coords:
        time_str = f" - {tcc.time.dt.strftime('%Y-%m').values}"

    plt.title(f"ERA5 Total Cloud Cover{time_str}", fontsize=14, fontweight="bold")

    plt.tight_layout()

    output_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    logger.info(f"Plot saved to: {output_file}")

    ds.close()
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot ERA5 monthly mean total cloud cover data from GRIB file"
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        help="Input GRIB file path (e.g., data/raw/era5/era5_total_cloud_cover_2025_01.grib)",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2025,
        help="Year for the data (default: 2025)",
    )
    parser.add_argument(
        "--month",
        type=int,
        default=1,
        help="Month for the data (default: 1)",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        help="Output image file path",
    )

    args = parser.parse_args()

    if args.input_file:
        input_file = args.input_file
    else:
        input_file = Path(f"data/raw/era5/era5_total_cloud_cover_{args.year}_{args.month:02d}.grib")

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return

    if args.output_file:
        output_file = args.output_file
    else:
        output_file = Path(f"data/images/era5_cloud_cover_{args.year}_{args.month:02d}.png")

    plot_era5_cloud_cover(input_file=input_file, output_file=output_file)


if __name__ == "__main__":
    main()
