import numpy as np
import numpy.testing as npt
import pytest
import tempfile
import os

import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds

from climatemaps.geogrid import GeoGrid
from climatemaps.landmask import apply_land_mask


class TestLandMask:

    @pytest.fixture
    def create_test_mask(self):
        """Create a temporary test land mask file"""
        temp_dir = tempfile.mkdtemp()
        mask_path = os.path.join(temp_dir, "test_mask.tif")

        width, height = 360, 180
        mask_data = np.ones((height, width), dtype=np.uint8)
        mask_data[:, :90] = 0

        transform = from_bounds(-180, -90, 180, 90, width, height)

        crs_wgs84 = CRS.from_proj4("+proj=longlat +datum=WGS84 +no_defs")
        
        with rasterio.open(
            mask_path,
            "w",
            driver="GTiff",
            height=height,
            width=width,
            count=1,
            dtype=np.uint8,
            crs=crs_wgs84,
            transform=transform,
        ) as dst:
            dst.write(mask_data, 1)

        yield mask_path

        if os.path.exists(mask_path):
            os.remove(mask_path)
        os.rmdir(temp_dir)

    def test_apply_land_mask_basic(self, create_test_mask):
        lon_range = np.array([-180, -90, 0, 90])
        lat_range = np.array([45, -45])
        values = np.array([[10, 20, 30, 40], [50, 60, 70, 80]], dtype=float)

        geo_grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)

        masked_grid = apply_land_mask(geo_grid, create_test_mask)

        assert isinstance(masked_grid, GeoGrid)
        assert masked_grid.values.shape == geo_grid.values.shape
        npt.assert_array_equal(masked_grid.lon_range, geo_grid.lon_range)
        npt.assert_array_equal(masked_grid.lat_range, geo_grid.lat_range)

        assert np.isnan(masked_grid.values[0, 0])
        assert np.isnan(masked_grid.values[0, 1])
        assert not np.isnan(masked_grid.values[0, 2])
        assert not np.isnan(masked_grid.values[0, 3])

    def test_apply_land_mask_preserves_land_values(self, create_test_mask):
        lon_range = np.array([0, 90])
        lat_range = np.array([45, -45])
        values = np.array([[30, 40], [70, 80]], dtype=float)

        geo_grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)

        masked_grid = apply_land_mask(geo_grid, create_test_mask)

        npt.assert_array_equal(masked_grid.values[~np.isnan(masked_grid.values)], values.flatten())

    def test_apply_land_mask_regional(self, create_test_mask):
        lon_range = np.linspace(10, 50, 20)
        lat_range = np.linspace(60, 30, 15)
        values = np.random.rand(15, 20) * 100

        geo_grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)

        masked_grid = apply_land_mask(geo_grid, create_test_mask)

        assert isinstance(masked_grid, GeoGrid)
        assert masked_grid.values.shape == geo_grid.values.shape

    def test_apply_land_mask_missing_file(self):
        lon_range = np.array([0, 90])
        lat_range = np.array([45, -45])
        values = np.array([[30, 40], [70, 80]], dtype=float)

        geo_grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)

        result = apply_land_mask(geo_grid, "nonexistent_mask.tif")

        assert result is geo_grid
        npt.assert_array_equal(result.values, values)

    def test_apply_land_mask_all_land(self, create_test_mask):
        lon_range = np.array([10, 20, 30, 40])
        lat_range = np.array([45, -45])
        values = np.array([[10, 20, 30, 40], [50, 60, 70, 80]], dtype=float)

        geo_grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)

        masked_grid = apply_land_mask(geo_grid, create_test_mask)

        assert not np.any(np.isnan(masked_grid.values))

    def test_apply_land_mask_small_region(self, create_test_mask):
        lon_range = np.linspace(5, 15, 5)
        lat_range = np.linspace(48, 44, 3)
        values = np.ones((3, 5)) * 25.0

        geo_grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)

        masked_grid = apply_land_mask(geo_grid, create_test_mask)

        assert masked_grid.values.shape == (3, 5)
        npt.assert_array_equal(masked_grid.lon_range, geo_grid.lon_range)
        npt.assert_array_equal(masked_grid.lat_range, geo_grid.lat_range)


class TestLandMaskWindowedReading:

    @pytest.fixture
    def create_large_test_mask(self):
        """Create a larger test mask to verify windowed reading optimization"""
        temp_dir = tempfile.mkdtemp()
        mask_path = os.path.join(temp_dir, "large_test_mask.tif")

        width, height = 3600, 1800
        mask_data = np.ones((height, width), dtype=np.uint8)
        mask_data[:, : width // 4] = 0

        transform = from_bounds(-180, -90, 180, 90, width, height)

        crs_wgs84 = CRS.from_proj4("+proj=longlat +datum=WGS84 +no_defs")
        
        with rasterio.open(
            mask_path,
            "w",
            driver="GTiff",
            height=height,
            width=width,
            count=1,
            dtype=np.uint8,
            crs=crs_wgs84,
            transform=transform,
        ) as dst:
            dst.write(mask_data, 1)

        yield mask_path

        if os.path.exists(mask_path):
            os.remove(mask_path)
        os.rmdir(temp_dir)

    def test_windowed_reading_small_region(self, create_large_test_mask):
        lon_range = np.linspace(5, 15, 50)
        lat_range = np.linspace(48, 44, 30)
        values = np.random.rand(30, 50) * 100

        geo_grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)

        masked_grid = apply_land_mask(geo_grid, create_large_test_mask)

        assert masked_grid.values.shape == geo_grid.values.shape
        npt.assert_array_equal(masked_grid.lon_range, geo_grid.lon_range)
        npt.assert_array_equal(masked_grid.lat_range, geo_grid.lat_range)

    def test_windowed_reading_respects_bbox(self, create_large_test_mask):
        lon_range = np.linspace(-150, -100, 20)
        lat_range = np.linspace(50, 20, 15)
        values = np.random.rand(15, 20) * 100

        geo_grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)

        masked_grid = apply_land_mask(geo_grid, create_large_test_mask)

        assert np.all(np.isnan(masked_grid.values))

