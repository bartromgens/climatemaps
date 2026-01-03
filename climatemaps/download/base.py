from abc import ABC, abstractmethod

from climatemaps.datasets import ClimateDataConfig
from climatemaps.logger import logger


class DataDownloader(ABC):
    def __init__(self, config: ClimateDataConfig):
        self.config = config

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def verify(self) -> bool:
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
        if self.is_available() and not force_redownload:
            if skip_verification or self.verify():
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
        if not force_redownload and self.is_available() and (skip_verification or self.verify()):
            return
        self.download(
            force_redownload=force_redownload,
            skip_verification=skip_verification,
            month_upper=month_upper,
        )
