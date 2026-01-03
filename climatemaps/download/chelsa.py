from pathlib import Path

from climatemaps.datasets import ClimateDataConfig, ClimateVarKey, CHELSA_FILE_ABBREVIATIONS
from climatemaps.download.base import DataDownloader
from climatemaps.download.utils import download_file
from climatemaps.geotiff import verify_geotiff_file
from climatemaps.logger import logger


class CHELSADownloader(DataDownloader):
    def __init__(self, config: ClimateDataConfig):
        super().__init__(config)
        self.var_str = CHELSA_FILE_ABBREVIATIONS.get(config.variable_type)
        if not self.var_str:
            raise ValueError(f"Unsupported CHELSA variable: {config.variable_type}")

        self.base_dir = Path(config.filepath)

    def is_available(self) -> bool:
        first_month_file = self._get_month_filepath(1)
        return first_month_file.exists()

    def verify(self) -> bool:
        first_month_file = self._get_month_filepath(1)
        if not first_month_file.exists():
            return False
        return verify_geotiff_file(first_month_file)

    def _get_month_filepath(self, month: int) -> Path:
        filename = f"CHELSA_{self.var_str}_{self.config.year_range[0]}-{self.config.year_range[1]}_{month:02d}.tif"
        return self.base_dir / filename

    def _get_url(self, month: int) -> str:
        base_url = "https://os.unil.cloud.switch.ch/chelsa02/chelsa/global/climatologies"
        filename = f"CHELSA_{self.var_str}_{month:02d}_{self.config.year_range[0]}-{self.config.year_range[1]}_V.2.1.tif"
        year_range_str = f"{self.config.year_range[0]}-{self.config.year_range[1]}"
        return f"{base_url}/{self.var_str}/{year_range_str}/{filename}"

    def _cleanup_corrupted_data(self) -> None:
        for month in range(1, 13):
            month_file = self._get_month_filepath(month)
            month_file.unlink(missing_ok=True)

    def _do_download(self, skip_verification: bool = False, month_upper: int = 12) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)

        for month in range(1, month_upper + 1):
            destination = self._get_month_filepath(month)
            logger.info(f"Downloading CHELSA data for month {month:02d}...")

            try:
                url = self._get_url(month)
                download_file(url, destination)
            except ValueError as e:
                logger.error(f"Cannot download data for month {month:02d}: {e}")
                raise
