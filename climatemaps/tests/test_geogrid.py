import numpy as np
import numpy.testing as npt
import pytest

from climatemaps.geogrid import GeoGrid


class TestGeoGridProperties:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.geo_grid = GeoGrid(
            lon_range=np.array([-135, -45, 45, 135]),
            lat_range=np.array([45, -45]),
            values=np.array([[0, 1, 2, 4], [5, 6, 7, 8]]),
        )

    def test_lon_min(self):
        assert self.geo_grid.lon_min == -135

    def test_lon_max(self):
        assert self.geo_grid.lon_max == 135

    def test_lat_min(self):
        assert self.geo_grid.lat_min == -45

    def test_lat_max(self):
        assert self.geo_grid.lat_max == 45

    def test_bin_width(self):
        assert self.geo_grid.bin_width_lon == 90

    def test_llcrnrlon(self):
        assert self.geo_grid.llcrnrlon == -180

    def test_llcrnrlat(self):
        assert self.geo_grid.llcrnrlat == -90

    def test_urcrnrlon(self):
        assert self.geo_grid.urcrnrlon == 180

    def test_urcrnrlat(self):
        assert self.geo_grid.urcrnrlat == 90


class TestGeoGridValidation:

    def test_validation_true(self):
        lon_range = np.array([-135, -45, 45, 135])
        lat_range = np.array([45, -45])
        values = np.array([[0, 1, 2, 4], [5, 6, 7, 8]])
        grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)

    def test_validation_lat_false(self):
        lon_range = np.array([-135, -45, 45, 135])
        lat_range = np.array([-45, 45])
        values = np.array([[0, 1, 2, 4], [5, 6, 7, 8]])
        with pytest.raises(ValueError):
            grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)

    def test_validation_lon_false(self):
        lon_range = np.array([135, 45, -45, -135])
        lat_range = np.array([45, -45])
        values = np.array([[0, 1, 2, 4], [5, 6, 7, 8]])
        with pytest.raises(ValueError):
            grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)

    def test_validation_shapes_false(self):
        lon_range = np.array([-135, -45, 45, 135])
        lat_range = np.array([45, -45])
        values = np.array([[0, 1], [5, 6], [0, 1], [5, 6]])
        with pytest.raises(ValueError):
            grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)


class TestGeoGridDifference:

    @pytest.fixture(autouse=True)
    def setup(self):
        lon_range = np.array([-135, -45, 45, 135])
        lat_range = np.array([45, -45])
        values = np.array([[0, 1, 2, 4], [5, 6, 7, 8]])
        self.geo_grid_a = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)
        self.geo_grid_b = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)

    def test_difference(self):
        geo_grid_diff = self.geo_grid_a.difference(self.geo_grid_b)
        npt.assert_array_almost_equal(geo_grid_diff.values, 0, decimal=6)
