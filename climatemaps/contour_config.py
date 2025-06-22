import math

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import SymLogNorm


class ContourPlotConfig:
    def __init__(
        self,
        level_lower=0,
        level_upper=100,
        colormap=plt.cm.jet,  # jet, jet_r, YlOrRd, gist_rainbow
        title="",
        unit="",
        log_scale=False,
        n_contours=21,
    ):
        self.n_contours = n_contours
        self.min_angle_between_segments = 5
        self.level_lower = level_lower
        self.level_upper = level_upper
        self.colormap = colormap
        self.title = title
        self.unit = unit
        self.norm = None

        if log_scale:
            assert self.level_lower > 0
            self.norm = SymLogNorm(linthresh=1.0, vmin=self.level_lower, vmax=self.level_upper)
            self.levels = np.logspace(
                start=self.level_lower,
                stop=math.log(self.level_upper + 2),
                num=self.n_contours,
                base=math.e,
            )
            # TODO: why is this needed?
            for i in range(0, len(self.levels)):
                self.levels[i] -= 1.0
        else:
            self.levels = np.linspace(
                start=self.level_lower, stop=self.level_upper, num=self.n_contours
            )

        if log_scale:
            assert self.level_lower > 0
            self.levels_image = np.logspace(
                start=math.log(self.level_lower) - 0.0001,  # TODO: why is this needed?
                stop=math.log(self.level_upper + 2),
                num=self.n_contours * 20,
                base=math.e,
            )
            # TODO: why is this needed?
            # for i in range(0, len(self.levels_image)):
            #     self.levels_image[i] -= 1.0
            # print(self.levels_image)
        else:
            self.levels_image = np.linspace(
                start=self.level_lower, stop=self.level_upper, num=self.n_contours * 20
            )

        # use half the number of levels for the colorbar ticks
        counter = 0
        self.colorbar_ticks = []
        for level in self.levels:
            if counter % 2 == 0:
                self.colorbar_ticks.append(level)
            counter += 1
