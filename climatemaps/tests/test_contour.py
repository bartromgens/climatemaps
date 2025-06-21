import tempfile

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
            lon_range=np.array([-135, -45, 45, 135]),
            lat_range=np.array([45, -45]),
            values=np.array([[0, 1, 2, 4], [5, 6, 7, 8]]),
        )

    def test_lon_min(self):
        assert self.contour.lon_min == -135

    def test_lon_max(self):
        assert self.contour.lon_max == 135

    def test_lat_min(self):
        assert self.contour.lat_min == -45

    def test_lat_max(self):
        assert self.contour.lat_max == 45

    def test_bin_width(self):
        assert self.contour.bin_width_lon == 90

    def test_llcrnrlon(self):
        assert self.contour.llcrnrlon == -180

    def test_llcrnrlat(self):
        assert self.contour.llcrnrlat == -90

    def test_urcrnrlon(self):
        assert self.contour.urcrnrlon == 180

    def test_urcrnrlat(self):
        assert self.contour.urcrnrlat == 90

    def test_create_tiles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.contour.create_tiles(data_dir_out=tmpdir, name="test", month=1)
