import pytest
import numpy as np

from climatemaps.contour import Contour
from climatemaps.contour import ContourPlotConfig


class TestContour:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.contour_plot_config = ContourPlotConfig()
        self.contour = Contour(
            config=self.contour_plot_config,
            lon_range=np.array([-180, 0, 180]),
            lat_range=np.array([-90, 0, 90]),
            values=np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]]),
        )

    def test_lon_min(self):
        assert self.contour.lon_min == -180

    def test_lon_max(self):
        assert self.contour.lon_max == 180

    def test_lat_min(self):
        assert self.contour.lat_min == -90

    def test_lat_max(self):
        assert self.contour.lat_max == 90
