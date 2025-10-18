from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List

import cdsapi

from climatemaps.logger import logger


class ERA5DailyStatistic(str, Enum):
    DAILY_MEAN = "daily_mean"
    DAILY_MINIMUM = "daily_minimum"
    DAILY_MAXIMUM = "daily_maximum"
    DAILY_SUM = "daily_sum"


class ERA5Frequency(str, Enum):
    HOURLY_1 = "1_hourly"
    HOURLY_6 = "6_hourly"


class ERA5Variable(str, Enum):
    TEMPERATURE_2M = "2m_temperature"
    TEMPERATURE_2M_MAX = "2m_temperature_max"
    TEMPERATURE_2M_MIN = "2m_temperature_min"
    TOTAL_PRECIPITATION = "total_precipitation"
    SURFACE_PRESSURE = "surface_pressure"
    DEWPOINT_2M = "2m_dewpoint_temperature"


class ERA5MonthlyVariable(str, Enum):
    TOTAL_CLOUD_COVER = "total_cloud_cover"
    TEMPERATURE_2M = "2m_temperature"
    TOTAL_PRECIPITATION = "total_precipitation"
    SURFACE_PRESSURE = "surface_pressure"
    DEWPOINT_2M = "2m_dewpoint_temperature"


class ERA5Client:
    def __init__(self) -> None:
        self.client = cdsapi.Client()

    def download_daily_statistics(
        self,
        output_dir: Path,
        variable: ERA5Variable,
        start_year: int,
        end_year: int,
        daily_statistic: ERA5DailyStatistic,
        frequency: ERA5Frequency,
    ) -> None:
        months: List[str] = [f"{m:02d}" for m in range(1, 13)]
        days: List[str] = [f"{d:02d}" for d in range(1, 32)]
        variable_name = variable.value.replace("_", "-")

        def build_request(year: int) -> Dict:
            return {
                "product_type": "reanalysis",
                "variable": [variable.value],
                "year": str(year),
                "month": months,
                "day": days,
                "daily_statistic": daily_statistic.value,
                "time_zone": "utc+00:00",
                "frequency": frequency.value,
            }

        def build_filename(year: int) -> str:
            return f"era5_{variable_name}_{daily_statistic.value}_{frequency.value}_{year}.nc"

        self._download_by_year(
            output_dir=output_dir,
            dataset="derived-era5-single-levels-daily-statistics",
            variable_value=variable.value,
            start_year=start_year,
            end_year=end_year,
            build_request=build_request,
            build_filename=build_filename,
        )

    def download_monthly_means(
        self,
        output_dir: Path,
        variable: ERA5MonthlyVariable,
        start_year: int,
        end_year: int,
    ) -> None:
        months: List[str] = [f"{m:02d}" for m in range(1, 13)]
        variable_name = variable.value.replace("_", "-")

        def build_request(year: int) -> Dict:
            return {
                "product_type": ["monthly_averaged_reanalysis"],
                "variable": [variable.value],
                "year": [str(year)],
                "month": months,
                "time": ["00:00"],
                "data_format": "grib",
                "download_format": "unarchived",
            }

        def build_filename(year: int) -> str:
            return f"era5_{variable_name}_{year}.grib"

        self._download_by_year(
            output_dir=output_dir,
            dataset="reanalysis-era5-single-levels-monthly-means",
            variable_value=variable.value,
            start_year=start_year,
            end_year=end_year,
            build_request=build_request,
            build_filename=build_filename,
        )

    def _download_by_year(
        self,
        output_dir: Path,
        dataset: str,
        variable_value: str,
        start_year: int,
        end_year: int,
        build_request: Callable[[int], Dict],
        build_filename: Callable[[int], str],
    ) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)

        years: List[int] = list(range(start_year, end_year + 1))
        total_downloads = len(years)
        current = 0

        for year in years:
            current += 1
            output_file = output_dir / build_filename(year)

            if output_file.exists():
                logger.info(f"[{current}/{total_downloads}] File already exists: {output_file}")
                continue

            logger.info(
                f"[{current}/{total_downloads}] Downloading {variable_value} for {year} (all months)"
            )

            request = build_request(year)

            try:
                self.client.retrieve(dataset, request).download(str(output_file))
                logger.info(f"Successfully downloaded: {output_file}")
            except Exception as e:
                logger.error(f"Failed to download {year}: {e}")
                continue

        logger.info(f"\nCompleted download process. Files saved to {output_dir}")
