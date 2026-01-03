import hashlib
import os
import tempfile

import pytest
import numpy as np
from PIL import Image

from climatemaps.contour import ContourTileBuilder
from climatemaps.contour_config import ContourPlotConfig
from climatemaps.geogrid import GeoGrid
from climatemaps.logger import logger


class TestContour:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.contour_plot_config = ContourPlotConfig()
        geo_grid = GeoGrid(
            lon_range=np.array([-135, -45, 45, 135]),
            lat_range=np.array([45, -45]),
            values=np.array([[0, 1, 2, 4], [5, 6, 7, 8]]),
        )
        self.contour = ContourTileBuilder(config=self.contour_plot_config, geo_grid=geo_grid)

    def test_create_tiles(self):
        month = 1
        name = "test"
        expected_files = {
            f"{month}_colorbar.png": "8be74a4d01e956dde45e64572ae46ac13751bb6e41cb8195c005cbe8980a03b0",
            f"{month}_raster.mbtiles": None,
            f"{month}_vector.mbtiles": None,  # This checksum changes each run, no idea why (timestamp?)
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            self.contour.create_tiles(data_dir_out=tmpdir, name=name, month=month)
            for filename, checksum_expected in expected_files.items():
                filepath = os.path.join(tmpdir, name, filename)
                assert os.path.exists(filepath), f"File {filepath} does not exist"
                checksum = self._compute_checksum(filepath)
                logger.info(f"checksum for {filepath}: {checksum}")
                if checksum_expected is not None:
                    assert (
                        checksum_expected == checksum
                    ), f"Checksum for {filepath} does not match expected {checksum_expected}"

            geojson_filepath = os.path.join(tmpdir, name, f"{month}.geojson")
            assert not os.path.exists(geojson_filepath)

    @classmethod
    def _compute_checksum(
        cls, filepath: str, algorithm: str = "sha256", chunk_size: int = 8192
    ) -> str:
        if filepath.endswith(".png"):
            return cls._compute_png_checksum(filepath, algorithm)

        hash_func = hashlib.new(algorithm)
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    @classmethod
    def _compute_png_checksum(cls, filepath: str, algorithm: str = "sha256") -> str:
        hash_func = hashlib.new(algorithm)
        with Image.open(filepath) as img:
            hash_func.update(np.array(img).tobytes())
        return hash_func.hexdigest()


class TestContourWebMercatorCropping:

    def test_crop_to_web_mercator_limits(self):
        """Test that data extending beyond Web Mercator limits is cropped"""
        config = ContourPlotConfig()
        lon_range = np.linspace(-180, 180, 20)
        lat_range = np.linspace(90, -90, 20)
        values = np.random.rand(20, 20)
        geo_grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)

        contour = ContourTileBuilder(config=config, geo_grid=geo_grid)

        assert contour.geo_grid.lat_max <= ContourTileBuilder.WEB_MERCATOR_MAX_LAT
        assert contour.geo_grid.lat_min >= -ContourTileBuilder.WEB_MERCATOR_MAX_LAT

    def test_no_cropping_when_within_web_mercator(self):
        """Test that data within Web Mercator limits is not cropped"""
        config = ContourPlotConfig()
        lon_range = np.linspace(-180, 180, 20)
        lat_range = np.linspace(80, -80, 20)
        values = np.random.rand(20, 20)
        geo_grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)

        contour = ContourTileBuilder(config=config, geo_grid=geo_grid)

        assert len(contour.geo_grid.lat_range) == len(lat_range)
        assert len(contour.geo_grid.lon_range) == len(lon_range)

    def test_coordinate_alignment_after_cropping(self):
        """Test that coordinates match data values after Web Mercator cropping"""
        config = ContourPlotConfig()
        lon_range = np.linspace(-180, 180, 36)
        lat_range = np.linspace(90, -90, 36)
        lon_grid, lat_grid = np.meshgrid(lon_range, lat_range)
        values = lon_grid + lat_grid

        geo_grid = GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)
        contour = ContourTileBuilder(config=config, geo_grid=geo_grid)

        test_lon = 0.0
        test_lat = 50.0
        expected_value = test_lon + test_lat
        actual_value = contour.geo_grid.get_value_at_coordinate(lon=test_lon, lat=test_lat)

        np.testing.assert_almost_equal(actual_value, expected_value, decimal=1)
