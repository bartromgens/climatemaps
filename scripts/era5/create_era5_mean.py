#!/usr/bin/env python3

import argparse
from pathlib import Path
from typing import List

import numpy as np
import rasterio
from rasterio.transform import from_bounds
import xarray as xr

from climatemaps.logger import logger


def calculate_monthly_mean_cloud_cover(
    input_dir: Path,
    output_dir: Path,
    month: int,
    start_year: int,
    end_year: int,
) -> None:
    if month < 1 or month > 12:
        raise ValueError(f"Month must be between 1 and 12, got {month}")

    logger.info(f"Calculating mean cloud cover for month {month} from {start_year} to {end_year}")

    grib_files: List[Path] = []
    for year in range(start_year, end_year + 1):
        grib_file = input_dir / f"era5_total_cloud_cover_{year}_{month:02d}.grib"
        if grib_file.exists():
            grib_files.append(grib_file)
            logger.info(f"Found: {grib_file.name}")
        else:
            logger.warning(f"Missing file: {grib_file.name}")

    if not grib_files:
        raise FileNotFoundError(
            f"No GRIB files found for month {month} between {start_year} and {end_year}"
        )

    logger.info(f"Processing {len(grib_files)} files")

    cloud_cover_data: List[np.ndarray] = []
    reference_ds = None
    latitude = None
    longitude = None

    for grib_file in grib_files:
        logger.info(f"Reading: {grib_file.name}")
        ds = xr.open_dataset(grib_file, engine="cfgrib")

        tcc = ds["tcc"]

        if "number" in tcc.dims:
            logger.info(f"Computing mean across {tcc.sizes['number']} ensemble members")
            tcc = tcc.mean(dim="number")

        if reference_ds is None:
            reference_ds = ds
            latitude = tcc.latitude.values
            longitude = tcc.longitude.values

            longitude_adjusted = longitude.copy()
            longitude_adjusted[longitude_adjusted > 180] -= 360
            longitude = longitude_adjusted

        cloud_cover_data.append(tcc.values)
        ds.close()

    logger.info("Calculating mean across all years")
    cloud_cover_stack = np.stack(cloud_cover_data, axis=0)
    mean_cloud_cover = np.nanmean(cloud_cover_stack, axis=0)

    lon_indices = np.argsort(longitude)
    longitude = longitude[lon_indices]
    mean_cloud_cover = mean_cloud_cover[:, lon_indices]

    logger.info(
        f"Mean cloud cover range: [{np.nanmin(mean_cloud_cover):.4f}, {np.nanmax(mean_cloud_cover):.4f}]"
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    variable_name = f"era5_2.5m_tcc"
    output_filename = f"{variable_name}_{month:02d}.tif"
    output_path = output_dir / variable_name / output_filename

    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing geotiff to: {output_path}")

    lat_min = float(latitude.min())
    lat_max = float(latitude.max())
    lon_min = float(longitude.min())
    lon_max = float(longitude.max())

    height, width = mean_cloud_cover.shape

    transform = from_bounds(lon_min, lat_min, lon_max, lat_max, width, height)

    # Using WKT instead of EPSG:4326 due to PROJ database version mismatch
    # TODO: Fix PROJ installation (conda update proj)
    wgs84_wkt = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AXIS["Latitude",NORTH],AXIS["Longitude",EAST],AUTHORITY["EPSG","4326"]]'
    try:
        crs = rasterio.crs.CRS.from_epsg(4326)
    except Exception:
        crs = rasterio.crs.CRS.from_wkt(wgs84_wkt)

    metadata = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "float32",
        "crs": crs,
        "transform": transform,
        "compress": "lzw",
        "nodata": np.nan,
    }

    with rasterio.open(output_path, "w", **metadata) as dst:
        dst.write(mean_cloud_cover.astype(np.float32), 1)

    logger.info(f"Successfully created: {output_path}")
    logger.info(
        f"Year range: {start_year}-{end_year}, Month: {month}, Files processed: {len(grib_files)}"
    )


def calculate_all_months_mean(
    input_dir: Path,
    output_dir: Path,
    start_year: int,
    end_year: int,
) -> None:
    logger.info(f"Calculating mean cloud cover for all 12 months")

    for month in range(1, 13):
        try:
            calculate_monthly_mean_cloud_cover(
                input_dir=input_dir,
                output_dir=output_dir,
                month=month,
                start_year=start_year,
                end_year=end_year,
            )
        except FileNotFoundError as e:
            logger.error(f"Skipping month {month}: {e}")
            continue
        except Exception as e:
            logger.error(f"Error processing month {month}: {e}")
            continue

    logger.info("Completed processing all months")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate mean cloud cover for a given month across a year range from ERA5 data"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/raw/era5"),
        help="Input directory containing ERA5 GRIB files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw/era5"),
        help="Output directory for geotiff files (will create subdirectory for variable)",
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=2024,
        help="Start year for averaging (default: 2024)",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=2025,
        help="End year for averaging (default: 2025)",
    )

    args = parser.parse_args()

    calculate_all_months_mean(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        start_year=args.start_year,
        end_year=args.end_year,
    )


if __name__ == "__main__":
    main()
