#!/usr/bin/env python3

import argparse
from pathlib import Path
from typing import List

import cdsapi

from climatemaps.logger import logger


def download_era5_monthly_cloud_cover(
    output_dir: Path,
    start_year: int = 1996,
    end_year: int = 2025,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = "reanalysis-era5-single-levels-monthly-means"

    client = cdsapi.Client()

    years: List[int] = list(range(start_year, end_year + 1))
    months: List[str] = [f"{m:02d}" for m in range(1, 13)]

    total_downloads = len(years) * len(months)
    current = 0

    for year in years:
        for month in months:
            current += 1

            output_file = output_dir / f"era5_total_cloud_cover_{year}_{month}.grib"

            if output_file.exists():
                logger.info(f"[{current}/{total_downloads}] File already exists: {output_file}")
                continue

            logger.info(f"[{current}/{total_downloads}] Downloading data for {year}-{month}")

            request = {
                "product_type": ["monthly_averaged_reanalysis"],
                "variable": ["total_cloud_cover"],
                "year": [str(year)],
                "month": [month],
                "time": ["00:00"],
                "data_format": "grib",
                "download_format": "unarchived",
            }

            try:
                client.retrieve(dataset, request).download(str(output_file))
                logger.info(f"Successfully downloaded: {output_file}")
            except Exception as e:
                logger.error(f"Failed to download {year}-{month}: {e}")
                continue

    logger.info(f"\nCompleted download process. Files saved to {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download ERA5 monthly mean total cloud cover data"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw/era5"),
        help="Output directory for ERA5 GRIB files",
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=1996,
        help="Start year for download (default: 1996)",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=2025,
        help="End year for download (default: 2025)",
    )

    args = parser.parse_args()

    download_era5_monthly_cloud_cover(
        output_dir=args.output_dir,
        start_year=args.start_year,
        end_year=args.end_year,
    )


if __name__ == "__main__":
    main()
