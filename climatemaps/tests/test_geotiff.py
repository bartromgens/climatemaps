import numpy as np
import pytest
from unittest.mock import Mock

from climatemaps.geotiff import _process_coordinate_arrays


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
