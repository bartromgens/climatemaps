import numpy as np
import numpy.testing as npt
import pytest
import tempfile
import os
from unittest.mock import Mock

import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds

from climatemaps.bbox import BoundingBox
from climatemaps.geotiff import (
    _process_coordinate_arrays,
    read_geotiff_future,
)


class TestProcessCoordinateArrays:

    def test_global_grid_coordinates_within_valid_bounds(self) -> None:
        width = 4320
        height = 2160

        transform = Mock()
        transform.c = -180.0
        transform.a = 360.0 / width
        transform.f = 90.0
        transform.e = -180.0 / height

        lon_array, lat_array = _process_coordinate_arrays(transform, width, height)

        assert len(lon_array) == width
        assert len(lat_array) == height

        assert lon_array.min() >= -180.0, f"Longitude minimum {lon_array.min()} is below -180"
        assert lon_array.max() <= 180.0, f"Longitude maximum {lon_array.max()} exceeds 180"
        assert lat_array.min() >= -90.0, f"Latitude minimum {lat_array.min()} is below -90"
        assert lat_array.max() <= 90.0, f"Latitude maximum {lat_array.max()} exceeds 90"

    def test_coordinate_arrays_represent_cell_centers(self) -> None:
        width = 360
        height = 180

        transform = Mock()
        transform.c = -180.0
        transform.a = 1.0
        transform.f = 90.0
        transform.e = -1.0

        lon_array, lat_array = _process_coordinate_arrays(transform, width, height)

        expected_first_lon = -180.0 + 0.5
        expected_last_lon = 180.0 - 0.5
        expected_first_lat = 90.0 - 0.5
        expected_last_lat = -90.0 + 0.5

        np.testing.assert_almost_equal(lon_array[0], expected_first_lon, decimal=6)
        np.testing.assert_almost_equal(lon_array[-1], expected_last_lon, decimal=6)
        np.testing.assert_almost_equal(lat_array[0], expected_first_lat, decimal=6)
        np.testing.assert_almost_equal(lat_array[-1], expected_last_lat, decimal=6)

    def test_high_resolution_grid_stays_within_bounds(self) -> None:
        width = 8640
        height = 4320

        transform = Mock()
        transform.c = -180.0
        transform.a = 360.0 / width
        transform.f = 90.0
        transform.e = -180.0 / height

        lon_array, lat_array = _process_coordinate_arrays(transform, width, height)

        assert lon_array.min() >= -180.0
        assert lon_array.max() <= 180.0
        assert lat_array.min() >= -90.0
        assert lat_array.max() <= 90.0

    def test_coordinate_spacing_is_uniform(self) -> None:
        width = 360
        height = 180

        transform = Mock()
        transform.c = -180.0
        transform.a = 1.0
        transform.f = 90.0
        transform.e = -1.0

        lon_array, lat_array = _process_coordinate_arrays(transform, width, height)

        lon_diffs = np.diff(lon_array)
        lat_diffs = np.diff(lat_array)

        expected_lon_spacing = 1.0
        expected_lat_spacing = -1.0

        np.testing.assert_array_almost_equal(lon_diffs, expected_lon_spacing, decimal=6)
        np.testing.assert_array_almost_equal(lat_diffs, expected_lat_spacing, decimal=6)


class TestGeotiffWithBbox:

    @pytest.fixture
    def create_multi_band_geotiff(self):
        """Create a multi-band GeoTIFF for testing monthly data"""
        temp_dir = tempfile.mkdtemp()
        tiff_path = os.path.join(temp_dir, "test_monthly.tif")

        width, height = 360, 180
        transform = from_bounds(-180, -90, 180, 90, width, height)

        crs_wgs84 = CRS.from_proj4("+proj=longlat +datum=WGS84 +no_defs")

        with rasterio.open(
            tiff_path,
            "w",
            driver="GTiff",
            height=height,
            width=width,
            count=12,
            dtype=np.float32,
            crs=crs_wgs84,
            transform=transform,
        ) as dst:
            for month in range(1, 13):
                data = np.full((height, width), month * 10.0, dtype=np.float32)
                dst.write(data, month)

        yield tiff_path

        if os.path.exists(tiff_path):
            os.remove(tiff_path)
        os.rmdir(temp_dir)

    def test_read_geotiff_future_without_bbox(self, create_multi_band_geotiff):
        lon_array, lat_array, values = read_geotiff_future(create_multi_band_geotiff, month=1)

        assert len(lon_array) == 360
        assert len(lat_array) == 180
        assert values.shape == (180, 360)
        assert np.all(values == 10.0)

    def test_read_geotiff_future_with_bbox(self, create_multi_band_geotiff):
        bbox = BoundingBox(lon_min=0, lat_min=0, lon_max=45, lat_max=45)

        lon_array, lat_array, values = read_geotiff_future(
            create_multi_band_geotiff, month=1, bbox=bbox
        )

        assert len(lon_array) < 360
        assert len(lat_array) < 180
        assert values.shape == (len(lat_array), len(lon_array))
        assert np.all(values == 10.0)

    def test_read_geotiff_future_bbox_coordinates_correct(self, create_multi_band_geotiff):
        bbox = BoundingBox(lon_min=10, lat_min=20, lon_max=30, lat_max=40)

        lon_array, lat_array, values = read_geotiff_future(
            create_multi_band_geotiff, month=6, bbox=bbox
        )

        assert lon_array.min() >= bbox.lon_min - 1
        assert lon_array.max() <= bbox.lon_max + 1
        assert lat_array.min() >= bbox.lat_min - 1
        assert lat_array.max() <= bbox.lat_max + 1
        assert np.all(values == 60.0)

    def test_read_geotiff_future_different_months_with_bbox(self, create_multi_band_geotiff):
        bbox = BoundingBox(lon_min=-45, lat_min=-30, lon_max=45, lat_max=30)

        lon_array_1, lat_array_1, values_1 = read_geotiff_future(
            create_multi_band_geotiff, month=1, bbox=bbox
        )
        lon_array_12, lat_array_12, values_12 = read_geotiff_future(
            create_multi_band_geotiff, month=12, bbox=bbox
        )

        npt.assert_array_equal(lon_array_1, lon_array_12)
        npt.assert_array_equal(lat_array_1, lat_array_12)
        assert values_1.shape == values_12.shape

        assert np.all(values_1 == 10.0)
        assert np.all(values_12 == 120.0)
