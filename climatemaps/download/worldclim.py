from pathlib import Path

from climatemaps.datasets import (
    ClimateDataConfig,
    ClimateModel,
    ClimateScenario,
    ClimateVarKey,
    FutureClimateDataConfig,
    SpatialResolution,
)
from climatemaps.download.base import DataDownloader
from climatemaps.download.utils import download_file, extract_zip
from climatemaps.ensemble import compute_ensemble_mean, compute_ensemble_std_dev
from climatemaps.geotiff import verify_geotiff_file
from climatemaps.logger import logger


class WorldClimHistoricalDownloader(DataDownloader):
    def __init__(self, config: ClimateDataConfig):
        super().__init__(config)
        self.data_dir = Path(config.filepath)
        self.data_type = config.filepath.split("/")[-1]

    def is_available(self) -> bool:
        first_month_file = self.data_dir / f"{self.data_type}_01.tif"
        return first_month_file.exists()

    def verify(self) -> bool:
        first_month_file = self.data_dir / f"{self.data_type}_01.tif"
        if not first_month_file.exists():
            return False
        return verify_geotiff_file(first_month_file)

    def _get_url(self) -> str:
        base_url = "https://geodata.ucdavis.edu/climate/worldclim/2_1/base"

        resolution_map = {
            SpatialResolution.MIN10: "10m",
            SpatialResolution.MIN5: "5m",
            SpatialResolution.MIN2_5: "2.5m",
        }

        variable_map = {
            ClimateVarKey.T_MIN: "tmin",
            ClimateVarKey.T_MAX: "tmax",
            ClimateVarKey.PRECIPITATION: "prec",
        }

        res_str = resolution_map.get(self.config.resolution_input)
        var_str = variable_map.get(self.config.variable_type)

        if not res_str or not var_str:
            raise ValueError(
                f"Unsupported resolution {self.config.resolution_input} or variable {self.config.variable_type}"
            )

        return f"{base_url}/wc2.1_{res_str}_{var_str}.zip"

    def download(self, force_redownload: bool = False, **kwargs: dict) -> None:
        if self.is_available() and not force_redownload:
            if self.verify():
                logger.info(
                    f"Historical data already exists and is valid at {self.config.filepath}"
                )
                return
            else:
                logger.warning("Historical data exists but is corrupted, will re-download")
                for month in range(1, 13):
                    month_file = self.data_dir / f"{self.data_type}_{month:02d}.tif"
                    month_file.unlink(missing_ok=True)

        logger.info(
            f"Historical data not found or invalid at {self.config.filepath}, downloading..."
        )

        try:
            url = self._get_url()
        except ValueError as e:
            logger.error(f"Cannot download data: {e}")
            raise

        temp_zip = self.data_dir.parent / f"{self.data_dir.name}.zip"
        download_file(url, temp_zip, verify=False)
        extract_zip(temp_zip, self.data_dir)

        for month in range(1, 13):
            month_file = self.data_dir / f"{self.data_type}_{month:02d}.tif"
            if month_file.exists() and not verify_geotiff_file(month_file):
                logger.warning(
                    f"Extracted historical file for month {month:02d} failed verification"
                )
                raise ValueError(
                    f"Extracted historical file for month {month:02d} failed verification"
                )


class WorldClimFutureDownloader(DataDownloader):
    def __init__(self, config: FutureClimateDataConfig):
        super().__init__(config)
        self.config: FutureClimateDataConfig = config
        self.destination = Path(config.filepath)

    def is_available(self) -> bool:
        return self.destination.exists()

    def verify(self) -> bool:
        if not self.destination.exists():
            return False
        return verify_geotiff_file(self.destination)

    def _get_url(self) -> str:
        base_url = "https://geodata.ucdavis.edu/cmip6"

        resolution_map = {
            SpatialResolution.MIN10: "10m",
            SpatialResolution.MIN5: "5m",
            SpatialResolution.MIN2_5: "2.5m",
        }

        variable_map = {
            ClimateVarKey.T_MIN: "tmin",
            ClimateVarKey.T_MAX: "tmax",
            ClimateVarKey.PRECIPITATION: "prec",
        }

        res_str = resolution_map.get(self.config.resolution_input)
        var_str = variable_map.get(self.config.variable_type)
        model_str = self.config.climate_model.filename
        scenario_str = self.config.climate_scenario.name.lower()
        year_str = f"{self.config.year_range[0]}-{self.config.year_range[1]}"

        if not res_str or not var_str:
            raise ValueError(
                f"Unsupported resolution {self.config.resolution_input} or variable {self.config.variable_type}"
            )

        return f"{base_url}/{res_str}/{model_str}/{scenario_str}/wc2.1_{res_str}_{var_str}_{model_str}_{scenario_str}_{year_str}.tif"

    def _create_ensemble_mean(self) -> None:
        logger.info(f"Creating ensemble mean for {self.config.data_type_slug}")

        base_dir = Path(self.config.filepath).parent
        output_dir = base_dir

        compute_ensemble_mean(
            base_dir=base_dir,
            resolution=self.config.resolution_input,
            variable=self.config.variable_type,
            scenario=self.config.climate_scenario,
            year_range=self.config.year_range,
            output_dir=output_dir,
        )

    def _create_ensemble_std_dev(self) -> None:
        logger.info(f"Creating ensemble standard deviation for {self.config.data_type_slug}")

        base_dir = Path(self.config.filepath).parent
        output_dir = base_dir

        compute_ensemble_std_dev(
            base_dir=base_dir,
            resolution=self.config.resolution_input,
            variable=self.config.variable_type,
            scenario=self.config.climate_scenario,
            year_range=self.config.year_range,
            output_dir=output_dir,
        )

    def download(self, force_redownload: bool = False, **kwargs: dict) -> None:
        if self.is_available() and not force_redownload:
            if self.verify():
                logger.info(f"Future data already exists and is valid at {self.config.filepath}")
                return
            else:
                logger.warning("Future data exists but is corrupted, will re-download")
                self.destination.unlink()

        if self.config.climate_model == ClimateModel.ENSEMBLE_MEAN:
            logger.info("Ensemble mean requested, creating from available models...")
            self._create_ensemble_mean()
            return

        if self.config.climate_model == ClimateModel.ENSEMBLE_STD_DEV:
            logger.info("Ensemble standard deviation requested, creating from available models...")
            self._create_ensemble_std_dev()
            return

        logger.info(f"Future data not found or invalid at {self.config.filepath}, downloading...")

        try:
            url = self._get_url()
        except ValueError as e:
            logger.error(f"Cannot download data: {e}")
            raise

        download_file(url, self.destination)
