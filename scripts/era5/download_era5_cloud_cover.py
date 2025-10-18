#!/usr/bin/env python3

import argparse
from pathlib import Path

from climatemaps.era5 import ERA5Client, ERA5MonthlyVariable


def download_era5_monthly_cloud_cover(
    output_dir: Path,
    start_year: int = 1996,
    end_year: int = 2025,
) -> None:
    client = ERA5Client()
    client.download_monthly_means(
        output_dir=output_dir,
        variable=ERA5MonthlyVariable.TOTAL_CLOUD_COVER,
        start_year=start_year,
        end_year=end_year,
    )


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
