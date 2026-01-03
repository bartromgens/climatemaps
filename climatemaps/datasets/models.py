import logging
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

import numpy as np
import numpy.typing as npt

from climatemaps.bbox import BoundingBox
from climatemaps.contour_config import ContourPlotConfig
from climatemaps.datasets.config import (
    CHELSA_FILE_ABBREVIATIONS,
    CLIMATE_CONTOUR_CONFIGS,
    CLIMATE_DIFFERENCE_CONTOUR_CONFIGS,
    CLIMATE_DIFFERENCE_CONTOUR_CONFIGS_STD_DEV,
    CLIMATE_VARIABLES,
    CRU_TS_FILE_ABBREVIATIONS,
    ClimateVariable,
)
from climatemaps.datasets.conversions import chelsa_temperature_conversion
from climatemaps.datasets.enums import (
    ClimateModel,
    ClimateScenario,
    ClimateVarKey,
    DataFormat,
    SpatialResolution,
)

logger = logging.getLogger(__name__)

ReaderFunction = Callable[[str, int, BoundingBox | None], Tuple[np.ndarray, np.ndarray, np.ndarray]]


@dataclass
class ClimateDataConfig:
    variable_type: ClimateVarKey
    filepath: str
    format: DataFormat
    resolution_input: SpatialResolution
    year_range: Tuple[int, int]
    reader_function: ReaderFunction
    conversion_function: Optional[
        Callable[[npt.NDArray[np.floating], int], npt.NDArray[np.floating]]
    ] = None
    conversion_factor: float = 1
    source: Optional[str] = None
    apply_land_mask: bool = False

    @property
    def variable(self) -> ClimateVariable:
        return CLIMATE_VARIABLES[self.variable_type]

    @property
    def data_type_slug(self) -> str:
        return f"{self.variable.name}_{self.year_range[0]}_{self.year_range[1]}_{self.resolution_input.value}".lower().replace(
            ".", "_"
        )

    @property
    def contour_config(self) -> ContourPlotConfig:
        return CLIMATE_CONTOUR_CONFIGS[self.variable_type]

    @property
    def target_max_zoom_raster(self) -> int:
        from climatemaps.gdal import GdalCalculator

        current_max_zoom = GdalCalculator.calculate_max_zoom_raster(self.resolution_input)
        max_target_zoom = 6

        if current_max_zoom >= max_target_zoom:
            return max_target_zoom

        return current_max_zoom + 1

    @property
    def target_resolution_raster(self) -> int | None:
        from climatemaps.gdal import GdalCalculator

        world_width_minutes = 360 * 60
        world_height_minutes = 180 * 60
        width, height = GdalCalculator.calculate_min_resolution_for_zoom_level(
            self.target_max_zoom_raster,
            aspect_ratio_width=world_width_minutes,
            aspect_ratio_height=world_height_minutes,
        )
        return width * height

    @property
    def target_resolution_vector(self) -> int:
        return 25_000_000

    @property
    def resolution_effective(self) -> float:
        resolution_minutes = float(self.resolution_input.value.rstrip("m"))
        world_width_minutes = 360 * 60
        world_height_minutes = 180 * 60
        width_pixels = int(world_width_minutes / resolution_minutes)
        height_pixels = int(world_height_minutes / resolution_minutes)
        original_size = width_pixels * height_pixels

        if self.target_resolution_raster is None or original_size <= self.target_resolution_raster:
            return resolution_minutes

        downsample_factor = float(np.sqrt(original_size / self.target_resolution_raster))

        return resolution_minutes * downsample_factor

    @property
    def zoom_factor(self) -> Optional[float]:
        from climatemaps.gdal import GdalCalculator

        current_max_zoom = GdalCalculator.calculate_max_zoom_raster(self.resolution_input)

        if current_max_zoom >= self.target_max_zoom_raster:
            return None

        target_max_zoom = self.target_max_zoom_raster
        resolution_minutes = float(self.resolution_input.value.rstrip("m"))
        target_resolution_minutes = GdalCalculator.calculate_spatial_resolution_for_zoom_level(
            target_max_zoom
        )
        zoom_factor = resolution_minutes / target_resolution_minutes

        zoom_factor *= 1.015

        logger.info(
            f"Resolution {self.resolution_input.value} supports zoom level {current_max_zoom}, "
            f"applying zoom factor {zoom_factor:.3f} to reach zoom level {target_max_zoom}"
        )
        return zoom_factor

    def get_climate_model(self) -> Optional[ClimateModel]:
        return None

    def get_variable_type(self) -> ClimateVarKey:
        return self.variable_type

    def get_climate_scenario(self) -> Optional[ClimateScenario]:
        return None

    def get_year_range(self) -> Tuple[int, int]:
        return self.year_range


@dataclass
class FutureClimateDataConfig(ClimateDataConfig):
    climate_scenario: Optional[ClimateScenario] = field(default=None)
    climate_model: Optional[ClimateModel] = field(default=None)

    @property
    def data_type_slug(self) -> str:
        base_slug = super().data_type_slug
        return f"{base_slug}_{self.climate_scenario.name}_{self.climate_model.name}".lower()

    def get_climate_model(self) -> Optional[ClimateModel]:
        return self.climate_model

    def get_climate_scenario(self) -> Optional[ClimateScenario]:
        return self.climate_scenario


@dataclass
class ClimateDifferenceDataConfig(ClimateDataConfig):
    historical_config: Optional[ClimateDataConfig] = field(default=None)
    future_config: Optional[FutureClimateDataConfig] = field(default=None)

    @property
    def data_type_slug(self) -> str:
        if self.future_config and self.historical_config:
            return f"difference_{self.variable.name}_{self.historical_config.year_range[0]}_{self.historical_config.year_range[1]}_to_{self.future_config.year_range[0]}_{self.future_config.year_range[1]}_{self.resolution_input.value}_{self.future_config.climate_scenario.name}_{self.future_config.climate_model.name}".lower().replace(
                ".", "_"
            )
        return super().data_type_slug

    @property
    def contour_config(self) -> ContourPlotConfig:
        if self.future_config and self.future_config.climate_model == ClimateModel.ENSEMBLE_STD_DEV:
            return CLIMATE_DIFFERENCE_CONTOUR_CONFIGS_STD_DEV[self.variable_type]
        return CLIMATE_DIFFERENCE_CONTOUR_CONFIGS[self.variable_type]

    def get_climate_model(self) -> Optional[ClimateModel]:
        if self.future_config:
            return self.future_config.climate_model
        return None

    def get_variable_type(self) -> ClimateVarKey:
        if self.future_config:
            return self.future_config.variable_type
        return self.variable_type

    def get_climate_scenario(self) -> Optional[ClimateScenario]:
        if self.future_config:
            return self.future_config.climate_scenario
        return None

    def get_year_range(self) -> Tuple[int, int]:
        if self.future_config:
            return self.future_config.year_range
        return self.year_range


@dataclass
class ClimateDataConfigGroup:
    variable_types: List[ClimateVarKey]
    format: DataFormat
    resolutions: List[SpatialResolution]
    year_ranges: List[Tuple[int, int]]
    reader_function: ReaderFunction
    conversion_function: Optional[
        Callable[[npt.NDArray[np.floating], int], npt.NDArray[np.floating]]
    ] = None
    conversion_factor: float = 1
    source: Optional[str] = None
    configs: List[ClimateDataConfig] = field(default_factory=list)
    filepath_template: Optional[str] = None

    def __post_init__(self) -> None:
        for cfg in self.configs:
            cfg.group = self

    def create_configs(self) -> List[ClimateDataConfig]:
        configs: List[ClimateDataConfig] = []
        for variable_type in self.variable_types:
            for year_range in self.year_ranges:
                for resolution in self.resolutions:
                    variable = CLIMATE_VARIABLES[variable_type]
                    config = ClimateDataConfig(
                        variable_type=variable_type,
                        format=self.format,
                        resolution_input=resolution,
                        year_range=year_range,
                        filepath=self.filepath_template.format(
                            resolution=resolution.value,
                            year_range=year_range,
                            variable_name=variable.filename.lower(),
                        ),
                        reader_function=self.reader_function,
                        conversion_function=self.conversion_function,
                        conversion_factor=self.conversion_factor,
                    )
                    configs.append(config)
        return configs


@dataclass
class FutureClimateDataConfigGroup(ClimateDataConfigGroup):
    climate_scenarios: List[ClimateScenario] = field(default_factory=list)
    climate_models: List[ClimateModel] = field(default_factory=list)
    configs: List[FutureClimateDataConfig] = field(default_factory=list)

    def create_configs(self) -> List[FutureClimateDataConfig]:
        configs: List[FutureClimateDataConfig] = []
        for variable_type in self.variable_types:
            for year_range in self.year_ranges:
                for resolution in self.resolutions:
                    for climate_scenario in self.climate_scenarios:
                        for climate_model in self.climate_models:
                            config = FutureClimateDataConfig(
                                variable_type=variable_type,
                                format=self.format,
                                resolution_input=resolution,
                                year_range=year_range,
                                climate_scenario=climate_scenario,
                                climate_model=climate_model,
                                filepath=self.filepath_template.format(
                                    resolution=resolution.value,
                                    year_range=year_range,
                                    variable_name=CLIMATE_VARIABLES[variable_type].filename.lower(),
                                    climate_scenario=climate_scenario.name.lower(),
                                    climate_model=climate_model.filename,
                                ),
                                reader_function=self.reader_function,
                                conversion_function=self.conversion_function,
                                conversion_factor=self.conversion_factor,
                                source=self.source,
                            )
                            configs.append(config)
        return configs


@dataclass
class CRUTSClimateDataConfigGroup(ClimateDataConfigGroup):
    def create_configs(self) -> List[ClimateDataConfig]:
        configs: List[ClimateDataConfig] = []
        for variable_type in self.variable_types:
            for year_range in self.year_ranges:
                for resolution in self.resolutions:
                    abbr = CRU_TS_FILE_ABBREVIATIONS[variable_type]
                    config = ClimateDataConfig(
                        variable_type=variable_type,
                        format=self.format,
                        resolution_input=resolution,
                        year_range=year_range,
                        filepath=f"data/raw/cruts/cru_{abbr}_clim_{year_range[0]}-{year_range[1]}",
                        reader_function=self.reader_function,
                        conversion_function=self.conversion_function,
                        conversion_factor=self.conversion_factor,
                        source=self.source,
                    )
                    configs.append(config)
        return configs


@dataclass
class CHELSAClimateDataConfigGroup(ClimateDataConfigGroup):
    def create_configs(self) -> List[ClimateDataConfig]:
        configs: List[ClimateDataConfig] = []
        for variable_type in self.variable_types:
            for year_range in self.year_ranges:
                for resolution in self.resolutions:
                    var_str = CHELSA_FILE_ABBREVIATIONS.get(variable_type)
                    if not var_str:
                        raise ValueError(f"Unsupported CHELSA variable: {variable_type}")

                    filepath = f"data/raw/chelsa/CHELSA_{var_str}_{year_range[0]}-{year_range[1]}"

                    conversion_factors = {
                        ClimateVarKey.CLOUD_COVER: 0.01,
                        ClimateVarKey.T_MAX: 0.1,
                        ClimateVarKey.T_MIN: 0.1,
                        ClimateVarKey.PRECIPITATION: 0.1,
                        ClimateVarKey.WIND_SPEED: 0.001,
                        ClimateVarKey.RELATIVE_HUMIDITY: 0.01,
                        ClimateVarKey.RADIATION: 1.0,
                        ClimateVarKey.MOISTURE_INDEX: 0.1,
                        ClimateVarKey.POTENTIAL_EVAPOTRANSPIRATION: 0.01,
                        ClimateVarKey.VAPOUR_PRESSURE_DEFICIT: 0.1,
                    }

                    conversion_factor = conversion_factors.get(
                        variable_type, self.conversion_factor
                    )

                    conversion_function = self.conversion_function
                    if variable_type in [ClimateVarKey.T_MAX, ClimateVarKey.T_MIN]:
                        conversion_function = chelsa_temperature_conversion

                    config = ClimateDataConfig(
                        variable_type=variable_type,
                        format=self.format,
                        resolution_input=resolution,
                        year_range=year_range,
                        filepath=filepath,
                        reader_function=self.reader_function,
                        conversion_function=conversion_function,
                        conversion_factor=conversion_factor,
                        source=self.source,
                        apply_land_mask=True,
                    )
                    configs.append(config)
        return configs
