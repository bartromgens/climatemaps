from typing import Type

from climatemaps.datasets import ClimateDataConfig, DataFormat
from climatemaps.download.base import DataDownloader
from climatemaps.download.chelsa import CHELSADownloader
from climatemaps.download.cru_ts import CRUTSDownloader
from climatemaps.download.worldclim import (
    WorldClimFutureDownloader,
    WorldClimHistoricalDownloader,
)
from climatemaps.logger import logger


DOWNLOADER_REGISTRY: dict[DataFormat, Type[DataDownloader]] = {
    DataFormat.GEOTIFF_WORLDCLIM_HISTORY: WorldClimHistoricalDownloader,
    DataFormat.GEOTIFF_WORLDCLIM_CMIP6: WorldClimFutureDownloader,
    DataFormat.CRU_TS: CRUTSDownloader,
    DataFormat.CHELSA: CHELSADownloader,
}


def get_downloader(config: ClimateDataConfig) -> DataDownloader:
    downloader_class = DOWNLOADER_REGISTRY.get(config.format)

    if downloader_class is None:
        raise ValueError(f"No downloader registered for format: {config.format}")

    return downloader_class(config)


def ensure_data_available(
    config: ClimateDataConfig,
    force_redownload: bool = False,
    month_upper: int = 12,
    skip_verification: bool = False,
) -> None:
    try:
        downloader = get_downloader(config)
        downloader.ensure_available(
            force_redownload=force_redownload,
            month_upper=month_upper,
            skip_verification=skip_verification,
        )
    except ValueError as e:
        logger.warning(f"Cannot download data: {e}")
        raise


__all__ = [
    "DOWNLOADER_REGISTRY",
    "get_downloader",
    "ensure_data_available",
]
