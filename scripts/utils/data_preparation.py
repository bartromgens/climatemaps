from datetime import datetime
import os
from typing import List, Union

from climatemaps.config import ClimateMapsConfig
from climatemaps.datasets import ClimateDataConfig, ClimateDifferenceDataConfig
from climatemaps.download import ensure_data_available
from climatemaps.logger import logger


def pre_download_all_data(
    datasets: List[Union[ClimateDataConfig, ClimateDifferenceDataConfig]],
    month_upper: int = 12,
) -> None:
    unique_configs = set()

    for config in datasets:
        if isinstance(config, ClimateDifferenceDataConfig):
            unique_configs.add(id(config.historical_config))
            unique_configs.add(id(config.future_config))
        else:
            unique_configs.add(id(config))

    logger.info(f"Pre-downloading/generating data for {len(unique_configs)} unique configurations")

    processed_configs = set()
    failed_downloads = []

    def try_download(cfg: ClimateDataConfig, description: str) -> None:
        if id(cfg) in processed_configs:
            return

        logger.info(f"Ensuring data available for {description}: {cfg.data_type_slug}")
        try:
            ensure_data_available(cfg, month_upper=month_upper)
            processed_configs.add(id(cfg))
        except Exception as e:
            failed_downloads.append((cfg.data_type_slug, str(e)))
            logger.warning(f"Failed to ensure data for {description} {cfg.data_type_slug}: {e}")

    for config in datasets:
        if isinstance(config, ClimateDifferenceDataConfig):
            try_download(config.historical_config, "historical")
            try_download(config.future_config, "future")
        else:
            try_download(config, "")

    if failed_downloads:
        logger.error(f"Failed to download/generate {len(failed_downloads)} dataset(s):")
        for data_slug, error in failed_downloads:
            logger.error(f"  - {data_slug}: {error}")

    logger.info(
        f"Data pre-download/generation completed "
        f"({len(processed_configs)} successful, {len(failed_downloads)} failed)"
    )


def check_if_mbtiles_older_than(
    config: ClimateDataConfig,
    month: int,
    threshold_date: datetime,
    maps_config: ClimateMapsConfig,
) -> bool:
    directory = os.path.join(maps_config.data_dir_out, config.data_type_slug)

    mbtiles_files = [
        os.path.join(directory, f"{month}_raster.mbtiles"),
        os.path.join(directory, f"{month}_vector.mbtiles"),
    ]

    for file_path in mbtiles_files:
        if not os.path.isfile(file_path):
            return True

        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        if file_mtime < threshold_date:
            return True

    return False
