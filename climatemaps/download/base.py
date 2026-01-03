from abc import ABC, abstractmethod
from pathlib import Path

from climatemaps.datasets import ClimateDataConfig


class DataDownloader(ABC):
    def __init__(self, config: ClimateDataConfig):
        self.config = config

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def download(self, force_redownload: bool = False, **kwargs: dict) -> None:
        pass

    @abstractmethod
    def verify(self) -> bool:
        pass

    def ensure_available(self, force_redownload: bool = False, **kwargs: dict) -> None:
        if not force_redownload and self.is_available() and self.verify():
            return
        self.download(force_redownload=force_redownload, **kwargs)
