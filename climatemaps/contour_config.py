from typing import Any
import numpy as np
from pydantic import BaseModel
from pydantic import Field
from pydantic import computed_field
from pydantic import model_validator
from pydantic import ConfigDict
from matplotlib import pyplot as plt
from matplotlib.colors import BoundaryNorm, SymLogNorm


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
            lt = self.linthresh
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
        n_colors = self.colormap.N
        levels = np.linspace(self.level_lower, self.level_upper, num=n_colors)
        norm = BoundaryNorm(levels, n_colors)
        return norm

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
