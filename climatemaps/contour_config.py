import logging

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import SymLogNorm

logger = logging.getLogger(__name__)


class ContourPlotConfig:
    def __init__(
        self,
        level_lower: float = 0.0,
        level_upper: float = 100.0,
        colormap=plt.cm.jet,  # jet, jet_r, YlOrRd, gist_rainbow
        title: str = "",
        unit: str = "",
        log_scale: bool = False,
        n_contours: int = 21,
        linthresh: float = 1.0,
    ):
        self.n_contours = n_contours
        self.level_lower = level_lower
        self.level_upper = level_upper
        self.colormap = colormap
        self.title = title
        self.unit = unit

        # Basic validation
        assert level_upper > level_lower, "level_upper must exceed level_lower"
        if log_scale:
            assert level_lower > 0, "level_lower must be > 0 for log scale"
            assert linthresh > 0, "linthresh must be > 0 for log scale"
            assert (
                level_upper > -linthresh
            ), "Data range cannot lie entirely below -linthresh when using log_scale"

        self.norm = (
            SymLogNorm(linthresh=linthresh, vmin=level_lower, vmax=level_upper)
            if log_scale
            else None
        )

        # Build the contour levels
        if log_scale:
            # Use a tiny epsilon to avoid hitting exactly linthresh
            eps = linthresh * 1e-6
            # Start above the linear region
            start = max(level_lower, linthresh + eps)
            self.levels = np.geomspace(start, level_upper, num=n_contours)
            self.levels_image = np.geomspace(start, level_upper, num=n_contours * 20)
        else:
            self.levels = np.linspace(level_lower, level_upper, num=n_contours)
            self.levels_image = np.linspace(level_lower, level_upper, num=n_contours * 20)

        # Compute colorbar ticks at every other level
        self.colorbar_ticks = self.levels[::2].tolist()
