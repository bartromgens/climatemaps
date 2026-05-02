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

        # Check that the bounding box (outer edges) is preserved, not the pixel centers
        npt.assert_almost_equal(downsampled.llcrnrlon, self.geo_grid.llcrnrlon, decimal=10)
        npt.assert_almost_equal(downsampled.urcrnrlon, self.geo_grid.urcrnrlon, decimal=10)
        npt.assert_almost_equal(downsampled.llcrnrlat, self.geo_grid.llcrnrlat, decimal=10)
        npt.assert_almost_equal(downsampled.urcrnrlat, self.geo_grid.urcrnrlat, decimal=10)

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
        """Test that downsampling preserves the geographic bounding box (outer edges)"""
        downsampled = self.geo_grid.downsample(factor=3)

        # The bounding box (outer edges of pixels) should be preserved
        npt.assert_almost_equal(downsampled.llcrnrlon, self.geo_grid.llcrnrlon, decimal=10)
        npt.assert_almost_equal(downsampled.urcrnrlon, self.geo_grid.urcrnrlon, decimal=10)
        npt.assert_almost_equal(downsampled.llcrnrlat, self.geo_grid.llcrnrlat, decimal=10)
        npt.assert_almost_equal(downsampled.urcrnrlat, self.geo_grid.urcrnrlat, decimal=10)

    def test_downsample_preserves_bounding_box(self):
        """Test that downsampled grid properly tiles the same bounding box"""
        # Create a grid with known coordinates
        # Original: 5 pixels at centers [-180, -90, 0, 90, 180] with bin_width=90
        # Longitude: bounding box extends to [-225, 225]
        # Latitude: bounding box extends to [-112.5, 112.5]
        lon_range = np.array([-180.0, -90.0, 0.0, 90.0, 180.0])
        lat_range = np.array([90.0, 45.0, 0.0, -45.0, -90.0])
        values = np.random.rand(5, 5)
        geo_grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)

        # Downsample by factor 2 -> 2 pixels
        downsampled = geo_grid.downsample(factor=2)

        # The bounding box should be preserved exactly
        npt.assert_almost_equal(downsampled.llcrnrlon, geo_grid.llcrnrlon, decimal=10)
        npt.assert_almost_equal(downsampled.urcrnrlon, geo_grid.urcrnrlon, decimal=10)
        npt.assert_almost_equal(downsampled.llcrnrlat, geo_grid.llcrnrlat, decimal=10)
        npt.assert_almost_equal(downsampled.urcrnrlat, geo_grid.urcrnrlat, decimal=10)

        # Verify bounding box values (no clamping applied)
        assert geo_grid.llcrnrlon == -225.0
        assert geo_grid.urcrnrlon == 225.0
        assert geo_grid.llcrnrlat == -112.5
        assert geo_grid.urcrnrlat == 112.5
        assert downsampled.llcrnrlon == -225.0
        assert downsampled.urcrnrlon == 225.0
        assert downsampled.llcrnrlat == -112.5
        assert downsampled.urcrnrlat == 112.5

        # For downsampled grid: 2 pixels spanning the original bounding box
        # Original bbox: lon [-225, 225], lat [-112.5, 112.5]
        # With 2 pixels: centers at -112.5 and 112.5 for lon, 56.25 and -56.25 for lat
        expected_lon_centers = np.array([-112.5, 112.5])
        expected_lat_centers = np.array([56.25, -56.25])

        npt.assert_almost_equal(downsampled.lon_range, expected_lon_centers, decimal=10)
        npt.assert_almost_equal(downsampled.lat_range, expected_lat_centers, decimal=10)


class TestGeoGridCropToLatRange:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.lon_range = np.linspace(-180, 180, 20)
        self.lat_range = np.linspace(90, -90, 10)
        self.values = np.arange(200).reshape(10, 20)
        self.geo_grid = GeoGrid(
            lon_range=self.lon_range, lat_range=self.lat_range, values=self.values
        )

    def test_crop_to_lat_range_basic(self):
        """Test basic cropping functionality"""
        original_lon_len = len(self.geo_grid.lon_range)
        original_values_width = self.geo_grid.values.shape[1]

        self.geo_grid.crop_to_lat_range(-45, 45)

        assert self.geo_grid.lat_min >= -45
        assert self.geo_grid.lat_max <= 45
        assert len(self.geo_grid.lon_range) == original_lon_len
        assert self.geo_grid.values.shape[1] == original_values_width

    def test_crop_to_lat_range_web_mercator(self):
        """Test cropping to Web Mercator limits"""
        WEB_MERCATOR_MAX_LAT = 85.05112878
        self.geo_grid.crop_to_lat_range(-WEB_MERCATOR_MAX_LAT, WEB_MERCATOR_MAX_LAT)

        assert self.geo_grid.lat_min >= -WEB_MERCATOR_MAX_LAT
        assert self.geo_grid.lat_max <= WEB_MERCATOR_MAX_LAT

    def test_crop_to_lat_range_no_cropping_needed(self):
        """Test that no cropping occurs when range contains entire grid"""
        original_lat_range = self.geo_grid.lat_range.copy()
        original_lon_range = self.geo_grid.lon_range.copy()
        original_values = self.geo_grid.values.copy()

        self.geo_grid.crop_to_lat_range(-100, 100)

        npt.assert_array_equal(self.geo_grid.lat_range, original_lat_range)
        npt.assert_array_equal(self.geo_grid.lon_range, original_lon_range)
        npt.assert_array_equal(self.geo_grid.values, original_values)

    def test_crop_to_lat_range_invalid_range(self):
        """Test that invalid ranges raise ValueError"""
        with pytest.raises(ValueError, match="lat_min .* must be less than lat_max"):
            self.geo_grid.crop_to_lat_range(45, -45)

    def test_crop_to_lat_range_no_overlap(self):
        """Test that non-overlapping ranges raise ValueError"""
        with pytest.raises(ValueError, match="does not overlap"):
            self.geo_grid.crop_to_lat_range(95, 100)

    def test_crop_preserves_longitude(self):
        """Test that cropping preserves longitude range and data"""
        original_lon_range = self.geo_grid.lon_range.copy()

        self.geo_grid.crop_to_lat_range(-45, 45)

        npt.assert_array_equal(self.geo_grid.lon_range, original_lon_range)

    def test_crop_maintains_coordinate_data_alignment(self):
        """Test that after cropping, coordinates still match data values"""
        original_lat_60 = self.lat_range[1]
        original_lon_0 = self.lon_range[10]
        original_value = self.values[1, 10]

        self.geo_grid.crop_to_lat_range(-45, 80)

        cropped_value = self.geo_grid.get_value_at_coordinate(
            lon=original_lon_0, lat=original_lat_60
        )
        npt.assert_almost_equal(cropped_value, original_value, decimal=6)


class TestGeoGridBinWidth:
    """Test bin_width calculation to prevent regression of coordinate shift bug"""

    def test_bin_width_uses_actual_coordinate_spacing(self):
        """Test that bin_width is calculated from actual coordinate spacing, not full world assumption"""
        # Simulate CHELSA-like data with non-full-world bounds
        lon_min = -180.00013888885002
        lon_max = 179.99985967115003
        lat_min = -90.00013888884999
        lat_max = 83.99986041515001

        # Create coordinate arrays with actual spacing
        n_lon = 100
        n_lat = 50
        lon_range = np.linspace(lon_min, lon_max, n_lon)
        lat_range = np.linspace(lat_max, lat_min, n_lat)
        values = np.random.rand(n_lat, n_lon)

        geo_grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)

        # Calculate expected bin_width from actual spacing
        expected_bin_width_lon = np.mean(np.diff(lon_range))
        expected_bin_width_lat = np.mean(np.abs(np.diff(lat_range)))

        # Verify bin_width uses actual spacing, not full world assumption
        npt.assert_almost_equal(geo_grid.bin_width_lon, expected_bin_width_lon, decimal=10)
        npt.assert_almost_equal(geo_grid.bin_width_lat, expected_bin_width_lat, decimal=10)

        # Verify it's NOT using the old hardcoded calculation
        wrong_bin_width_lon = 360.0 / len(lon_range)
        wrong_bin_width_lat = 180.0 / len(lat_range)
        assert abs(geo_grid.bin_width_lon - wrong_bin_width_lon) > 1e-6
        assert abs(geo_grid.bin_width_lat - wrong_bin_width_lat) > 1e-6

    def test_corner_coordinates_match_geotiff_bounds(self):
        """Test that corner coordinates are calculated correctly from actual spacing"""
        # Simulate CHELSA data bounds
        lon_min = -180.00013888885002
        lon_max = 179.99985967115003
        lat_min = -90.00013888884999
        lat_max = 83.99986041515001

        n_lon = 4320
        n_lat = 2088
        lon_range = np.linspace(lon_min, lon_max, n_lon)
        lat_range = np.linspace(lat_max, lat_min, n_lat)
        values = np.random.rand(n_lat, n_lon)

        geo_grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)

        # Calculate expected corner coordinates from actual bin_width
        expected_bin_width_lon = np.mean(np.diff(lon_range))
        expected_bin_width_lat = np.mean(np.abs(np.diff(lat_range)))

        # No clamping is applied in the new implementation
        expected_llcrnrlon = lon_min - expected_bin_width_lon / 2
        expected_urcrnrlon = lon_max + expected_bin_width_lon / 2
        expected_llcrnrlat = lat_min - expected_bin_width_lat / 2
        expected_urcrnrlat = lat_max + expected_bin_width_lat / 2

        # Verify corner coordinates match expected values
        npt.assert_almost_equal(geo_grid.llcrnrlon, expected_llcrnrlon, decimal=10)
        npt.assert_almost_equal(geo_grid.llcrnrlat, expected_llcrnrlat, decimal=10)
        npt.assert_almost_equal(geo_grid.urcrnrlon, expected_urcrnrlon, decimal=10)
        npt.assert_almost_equal(geo_grid.urcrnrlat, expected_urcrnrlat, decimal=10)

    def test_bin_width_after_downsampling(self):
        """Test that bin_width calculation works correctly after downsampling"""
        # Create grid with non-full-world bounds
        lon_min = -180.00013888885002
        lon_max = 179.99985967115003
        lat_min = -90.00013888884999
        lat_max = 83.99986041515001

        n_lon = 1000
        n_lat = 500
        lon_range = np.linspace(lon_min, lon_max, n_lon)
        lat_range = np.linspace(lat_max, lat_min, n_lat)
        values = np.random.rand(n_lat, n_lon)

        geo_grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)
        original_bin_width_lon = geo_grid.bin_width_lon
        original_bin_width_lat = geo_grid.bin_width_lat

        # Downsample
        downsampled = geo_grid.downsample(factor=2.5)

        # After downsampling, bin_width should be larger (fewer pixels, larger spacing)
        assert downsampled.bin_width_lon > original_bin_width_lon
        assert downsampled.bin_width_lat > original_bin_width_lat

        # Verify bin_width is still calculated from actual spacing
        expected_bin_width_lon = np.mean(np.diff(downsampled.lon_range))
        expected_bin_width_lat = np.mean(np.abs(np.diff(downsampled.lat_range)))

        npt.assert_almost_equal(downsampled.bin_width_lon, expected_bin_width_lon, decimal=10)
        npt.assert_almost_equal(downsampled.bin_width_lat, expected_bin_width_lat, decimal=10)
