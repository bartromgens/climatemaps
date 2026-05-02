from pathlib import Path

from climatemaps.datasets import ClimateDataConfig, ClimateVarKey, CRU_TS_FILE_ABBREVIATIONS
from climatemaps.download.base import DataDownloader
from climatemaps.download.utils import download_file, extract_zip
from climatemaps.geotiff import verify_geotiff_file
from climatemaps.logger import logger


class CRUTSDownloader(DataDownloader):
    def __init__(self, config: ClimateDataConfig):
        super().__init__(config)
        self.abbr = CRU_TS_FILE_ABBREVIATIONS.get(config.variable_type)
        if not self.abbr:
            raise ValueError(f"Unsupported CRU-TS variable: {config.variable_type}")

        self.data_dir = Path(config.filepath)
        self.year_str = f"{config.year_range[0]}-{config.year_range[1]}"
        self.file_pattern = f"cru_{self.abbr}_clim_{self.year_str}_{{:02d}}.tif"

    def _get_month_filepath(self, month: int) -> Path:
        return self.data_dir / self.file_pattern.format(month)

    def _is_available_single_file(self) -> bool:
        return False

    def _verify_single_file(self) -> bool:
        return False

    def _get_url(self) -> str:
        base_url = "https://dap.ceda.ac.uk/badc/ipcc-ddc/data/obs/cru_ts2_1/clim_30"
        filename = f"cru_{self.abbr}_clim_{self.year_str}.zip"
        return f"{base_url}/{self.abbr}/{filename}"

    def _cleanup_corrupted_data(self) -> None:
        for month in range(1, 13):
            (self.data_dir / self.file_pattern.format(month)).unlink(missing_ok=True)

    def _do_download(self, skip_verification: bool = False, month_upper: int = 12) -> None:
        try:
            url = self._get_url()
        except ValueError as e:
            logger.error(f"Cannot download data: {e}")
            raise

        self.data_dir.mkdir(parents=True, exist_ok=True)
        temp_zip = self.data_dir / f"cru_{self.abbr}_clim_{self.year_str}.zip"

        download_file(url, temp_zip, verify=False)
        extract_zip(temp_zip, self.data_dir)

        if not skip_verification:
            for month in range(1, 13):
                month_file = self.data_dir / self.file_pattern.format(month)
                if month_file.exists() and not verify_geotiff_file(month_file):
                    logger.warning(
                        f"Extracted CRU-TS file for month {month:02d} failed verification"
                    )
                    raise ValueError(
                        f"Extracted CRU-TS file for month {month:02d} failed verification"
                    )
