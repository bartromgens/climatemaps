from typing import Any
from typing import Dict
import numpy as np
from pydantic import BaseModel
from pydantic import Field
from pydantic import computed_field
from pydantic import model_validator
from pydantic import ConfigDict
from matplotlib import pyplot as plt
from matplotlib.colors import SymLogNorm
from matplotlib.colors import Normalize


class ContourPlotConfig(BaseModel):
    level_lower: float = Field(0.0, description="Minimum contour level")
    level_upper: float = Field(100.0, description="Maximum contour level")
    colormap: Any = Field(default_factory=lambda: plt.cm.jet, description="Matplotlib colormap")
    title: str = Field("", description="Plot title")
    unit: str = Field("", description="Unit label for colorbar")
    log_scale: bool = Field(False, description="Use symmetric log scale?")
    n_contours: int = Field(21, description="Number of contour intervals")
    linthresh: float = Field(1.0, description="Linear threshold for SymLogNorm")

    # allow matplotlib & numpy types
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def _check_ranges(self) -> "ContourPlotConfig":
        if self.level_upper <= self.level_lower:
            raise ValueError("level_upper must exceed level_lower")
        if self.log_scale:
            if self.level_lower <= 0:
                raise ValueError("level_lower must be > 0 for log scale")
            if self.linthresh <= 0:
                raise ValueError("linthresh must be > 0 for log scale")
            if self.level_upper <= -self.linthresh:
                raise ValueError(
                    "Data range cannot lie entirely below -linthresh when using log_scale"
                )
        return self

    @computed_field
    @property
    def norm(self) -> SymLogNorm | None:
        if self.log_scale:
            return SymLogNorm(
                linthresh=self.linthresh, vmin=self.level_lower, vmax=self.level_upper
            )
        return Normalize(vmin=self.level_lower, vmax=self.level_upper)

    @computed_field
    @property
    def levels(self) -> np.ndarray:
        if self.log_scale:
            return np.geomspace(self.level_lower, self.level_upper, num=self.n_contours)
        return np.linspace(self.level_lower, self.level_upper, num=self.n_contours)

    @computed_field
    @property
    def levels_image(self) -> np.ndarray:
        if self.log_scale:
            return np.geomspace(self.level_lower, self.level_upper, num=self.n_contours * 20)
        return np.linspace(self.level_lower, self.level_upper, num=self.n_contours * 20)

    @computed_field
    @property
    def colorbar_ticks(self) -> list[float]:
        return self.levels[::2].tolist()

    def get_colorbar_data(self) -> Dict[str, Any]:
        num_levels = 100
        if self.log_scale:
            levels_array = np.geomspace(self.level_lower, self.level_upper, num=num_levels)
        else:
            levels_array = np.linspace(self.level_lower, self.level_upper, num=num_levels)
        levels_list = levels_array.tolist()

        norm = self.norm

        colors = []
        for level in levels_list:
            normalized_value = norm(level)
            normalized_value = max(0.0, min(1.0, normalized_value))
            rgba = self.colormap(normalized_value)
            colors.append([float(rgba[0]), float(rgba[1]), float(rgba[2]), float(rgba[3])])

        return {
            "title": self.title,
            "unit": self.unit,
            "levels": levels_list,
            "colors": colors,
            "level_lower": float(self.level_lower),
            "level_upper": float(self.level_upper),
            "log_scale": self.log_scale,
        }
