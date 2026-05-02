from pathlib import Path

from climatemaps.datasets import (
    ClimateDataConfig,
    ClimateModel,
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

    def _get_month_filepath(self, month: int) -> Path:
        return self.data_dir / f"{self.data_type}_{month:02d}.tif"

    def _is_available_single_file(self) -> bool:
        return False

    def _verify_single_file(self) -> bool:
        return False

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

    def _cleanup_corrupted_data(self) -> None:
        for month in range(1, 13):
            month_file = self.data_dir / f"{self.data_type}_{month:02d}.tif"
            month_file.unlink(missing_ok=True)

    def _do_download(self, skip_verification: bool = False, month_upper: int = 12) -> None:
        try:
            url = self._get_url()
        except ValueError as e:
            logger.error(f"Cannot download data: {e}")
            raise

        temp_zip = self.data_dir.parent / f"{self.data_dir.name}.zip"
        download_file(url, temp_zip, verify=False)
        extract_zip(temp_zip, self.data_dir)

        if not skip_verification:
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

    def _is_available_single_file(self) -> bool:
        return self.destination.exists()

    def _verify_single_file(self) -> bool:
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

    def _cleanup_corrupted_data(self) -> None:
        self.destination.unlink(missing_ok=True)

    def _do_download(self, skip_verification: bool = False, month_upper: int = 12) -> None:
        if self.config.climate_model == ClimateModel.ENSEMBLE_MEAN:
            logger.info("Ensemble mean requested, creating from available models...")
            self._create_ensemble_mean()
            return

        if self.config.climate_model == ClimateModel.ENSEMBLE_STD_DEV:
            logger.info("Ensemble standard deviation requested, creating from available models...")
            self._create_ensemble_std_dev()
            return

        try:
            url = self._get_url()
        except ValueError as e:
            logger.error(f"Cannot download data: {e}")
            raise

        download_file(url, self.destination)
