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


class TestGeoGridGetValueAtCoordinate:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.lon_range = np.array([-135, -45, 45, 135])
        self.lat_range = np.array([45, -45])
        self.values = np.array([[10.0, 20.0, 30.0, 40.0], [50.0, 60.0, 70.0, 80.0]])
        self.geo_grid = GeoGrid(
            lon_range=self.lon_range, lat_range=self.lat_range, values=self.values
        )

    def test_get_value_exact_coordinate(self):
        value = self.geo_grid.get_value_at_coordinate(lon=-135, lat=45)
        assert value == 10.0

    def test_get_value_bilinear_interpolation(self):
        value = self.geo_grid.get_value_at_coordinate(lon=-90, lat=0)
        expected = 35.0
        npt.assert_almost_equal(value, expected, decimal=6)

    def test_get_value_interpolation_between_points(self):
        value = self.geo_grid.get_value_at_coordinate(lon=-135, lat=0)
        expected = 30.0
        npt.assert_almost_equal(value, expected, decimal=6)

    def test_get_value_out_of_bounds_lon(self):
        with pytest.raises(ValueError, match="Longitude .* is out of range"):
            self.geo_grid.get_value_at_coordinate(lon=200, lat=0)

    def test_get_value_out_of_bounds_lat(self):
        with pytest.raises(ValueError, match="Latitude .* is out of range"):
            self.geo_grid.get_value_at_coordinate(lon=0, lat=100)

    def test_get_value_nan(self):
        values_with_nan = np.array([[10.0, 20.0, np.nan, 40.0], [50.0, 60.0, 70.0, 80.0]])
        geo_grid_nan = GeoGrid(
            lon_range=self.lon_range, lat_range=self.lat_range, values=values_with_nan
        )
        with pytest.raises(ValueError, match="No data available at coordinates"):
            geo_grid_nan.get_value_at_coordinate(lon=45, lat=45)


class TestGeoGridDownsample:

    @pytest.fixture(autouse=True)
    def setup(self):
        # Create a larger grid for testing downsampling
        self.lon_range = np.linspace(-180, 180, 20)
        self.lat_range = np.linspace(90, -90, 10)
        self.values = np.random.rand(10, 20)
        self.geo_grid = GeoGrid(
            lon_range=self.lon_range, lat_range=self.lat_range, values=self.values
        )

    def test_downsample_factor_2(self):
        """Test downsampling by factor of 2"""
        downsampled = self.geo_grid.downsample(factor=2)

        # Check that dimensions are halved
        assert downsampled.values.shape[0] == self.geo_grid.values.shape[0] // 2
        assert downsampled.values.shape[1] == self.geo_grid.values.shape[1] // 2
        assert len(downsampled.lat_range) == len(self.geo_grid.lat_range) // 2
        assert len(downsampled.lon_range) == len(self.geo_grid.lon_range) // 2

        # Check that geographic bounds are preserved
        assert downsampled.lat_min == self.geo_grid.lat_min
        assert downsampled.lat_max == self.geo_grid.lat_max
        assert downsampled.lon_min == self.geo_grid.lon_min
        assert downsampled.lon_max == self.geo_grid.lon_max

    def test_downsample_factor_4(self):
        """Test downsampling by factor of 4"""
        downsampled = self.geo_grid.downsample(factor=4)

        # Check that dimensions are quartered
        assert downsampled.values.shape[0] == self.geo_grid.values.shape[0] // 4
        assert downsampled.values.shape[1] == self.geo_grid.values.shape[1] // 4
        assert len(downsampled.lat_range) == len(self.geo_grid.lat_range) // 4
        assert len(downsampled.lon_range) == len(self.geo_grid.lon_range) // 4

    def test_downsample_factor_1(self):
        """Test that factor=1 returns original grid"""
        downsampled = self.geo_grid.downsample(factor=1)

        # Should be identical to original
        npt.assert_array_equal(downsampled.values, self.geo_grid.values)
        npt.assert_array_equal(downsampled.lat_range, self.geo_grid.lat_range)
        npt.assert_array_equal(downsampled.lon_range, self.geo_grid.lon_range)

    def test_downsample_invalid_factor(self):
        """Test that invalid factors raise ValueError"""
        with pytest.raises(ValueError, match="Downsampling factor must be >= 1"):
            self.geo_grid.downsample(factor=0)

        with pytest.raises(ValueError, match="Downsampling factor must be >= 1"):
            self.geo_grid.downsample(factor=-1)

    def test_downsample_large_factor(self):
        """Test downsampling with a large factor that results in minimum size"""
        # Use a factor that would result in 0 dimensions, should be clamped to 1
        downsampled = self.geo_grid.downsample(factor=100)

        # Should have minimum size of 1x1
        assert downsampled.values.shape[0] == 1
        assert downsampled.values.shape[1] == 1
        assert len(downsampled.lat_range) == 1
        assert len(downsampled.lon_range) == 1

    def test_downsample_preserves_geographic_bounds(self):
        """Test that downsampling preserves the geographic extent"""
        downsampled = self.geo_grid.downsample(factor=3)

        # Geographic bounds should be exactly the same
        assert downsampled.lat_min == self.geo_grid.lat_min
        assert downsampled.lat_max == self.geo_grid.lat_max
        assert downsampled.lon_min == self.geo_grid.lon_min
        assert downsampled.lon_max == self.geo_grid.lon_max
