#!/usr/bin/env python3

import argparse
from pathlib import Path

from climatemaps.era5 import ERA5Client, ERA5DailyStatistic, ERA5Frequency, ERA5Variable


def download_era5_daily_2m_temperature(
    output_dir: Path,
    start_year: int = 2024,
    end_year: int = 2024,
    daily_statistic: ERA5DailyStatistic = ERA5DailyStatistic.DAILY_MINIMUM,
    frequency: ERA5Frequency = ERA5Frequency.HOURLY_6,
) -> None:
    client = ERA5Client()
    client.download_daily_statistics(
        output_dir=output_dir,
        variable=ERA5Variable.TEMPERATURE_2M,
        start_year=start_year,
        end_year=end_year,
        daily_statistic=daily_statistic,
        frequency=frequency,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Download ERA5 daily 2m temperature statistics")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw/era5"),
        help="Output directory for ERA5 NetCDF files",
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=2024,
        help="Start year for download (default: 2024)",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=2024,
        help="End year for download (default: 2024)",
    )
    parser.add_argument(
        "--daily-statistic",
        type=str,
        default="daily_minimum",
        choices=["daily_mean", "daily_minimum", "daily_maximum", "daily_sum"],
        help="Daily statistic to download (default: daily_minimum)",
    )
    parser.add_argument(
        "--frequency",
        type=str,
        default="6_hourly",
        choices=["1_hourly", "6_hourly"],
        help="Frequency for the data (default: 6_hourly)",
    )

    args = parser.parse_args()

    statistic_map = {
        "daily_mean": ERA5DailyStatistic.DAILY_MEAN,
        "daily_minimum": ERA5DailyStatistic.DAILY_MINIMUM,
        "daily_maximum": ERA5DailyStatistic.DAILY_MAXIMUM,
        "daily_sum": ERA5DailyStatistic.DAILY_SUM,
    }

    frequency_map = {
        "1_hourly": ERA5Frequency.HOURLY_1,
        "6_hourly": ERA5Frequency.HOURLY_6,
    }

    download_era5_daily_2m_temperature(
        output_dir=args.output_dir,
        start_year=args.start_year,
        end_year=args.end_year,
        daily_statistic=statistic_map[args.daily_statistic],
        frequency=frequency_map[args.frequency],
    )


if __name__ == "__main__":
    main()
