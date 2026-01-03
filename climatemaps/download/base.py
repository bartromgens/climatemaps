from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from climatemaps.datasets import ClimateDataConfig
from climatemaps.geotiff import verify_geotiff_file
from climatemaps.logger import logger


class DataDownloader(ABC):
    def __init__(self, config: ClimateDataConfig):
        self.config = config

    def _get_month_filepath(self, month: int) -> Optional[Path]:
        return None

    def is_available(self, month_upper: int = 12) -> bool:
        if self._get_month_filepath(1) is None:
            return self._is_available_single_file()

        for month in range(1, month_upper + 1):
            month_file = self._get_month_filepath(month)
            if month_file is None or not month_file.exists():
                return False
        return True

    def verify(self, month_upper: int = 12) -> bool:
        if self._get_month_filepath(1) is None:
            return self._verify_single_file()

        for month in range(1, month_upper + 1):
            month_file = self._get_month_filepath(month)
            if month_file is None or not month_file.exists():
                return False
            if not verify_geotiff_file(month_file):
                return False
        return True

    @abstractmethod
    def _is_available_single_file(self) -> bool:
        pass

    @abstractmethod
    def _verify_single_file(self) -> bool:
        pass

    @abstractmethod
    def _do_download(self, skip_verification: bool = False, month_upper: int = 12) -> None:
        pass

    @abstractmethod
    def _cleanup_corrupted_data(self) -> None:
        pass

    def download(
        self, force_redownload: bool = False, skip_verification: bool = False, month_upper: int = 12
    ) -> None:
        if self.is_available(month_upper=month_upper) and not force_redownload:
            if skip_verification or self.verify(month_upper=month_upper):
                logger.info(f"Data already exists and is valid at {self.config.filepath}")
                return
            else:
                logger.warning("Data exists but is corrupted, will re-download")
                self._cleanup_corrupted_data()

        logger.info(f"Data not found or invalid at {self.config.filepath}, downloading...")
        self._do_download(skip_verification=skip_verification, month_upper=month_upper)

    def ensure_available(
        self, force_redownload: bool = False, skip_verification: bool = False, month_upper: int = 12
    ) -> None:
        if (
            not force_redownload
            and self.is_available(month_upper=month_upper)
            and (skip_verification or self.verify(month_upper=month_upper))
        ):
            return
        self.download(
            force_redownload=force_redownload,
            skip_verification=skip_verification,
            month_upper=month_upper,
        )
