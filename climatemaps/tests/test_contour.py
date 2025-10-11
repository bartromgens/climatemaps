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
        expected_colorbar_file = f"{month}_colorbar.png"
        expected_image_file = f"{month}.png"
        expected_raster_tiles_file = f"{month}_raster.mbtiles"
        expected_vector_tiles_file = f"{month}_vector.mbtiles"
        expected_files = {
            expected_colorbar_file: "c1c96094eb0fabb6d38dd1e4adff2379351d1d80376dbd5e6fc19c61cc5d4e04",
            expected_image_file: "194e17635d738c43171039ee2389201fb8dbddf35d2ab8b45e0f3f09652669b4",
            expected_raster_tiles_file: "219a04d48f88699d04e0c838a683a3e913a7933c06d617984064c5b2056983da",
            expected_vector_tiles_file: None,  # This checksum changes each run, no idea why (timestamp?)
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            self.contour.create_tiles(data_dir_out=tmpdir, name=name, month=month)
            for filename, checksum_expected in expected_files.items():
                filepath = os.path.join(tmpdir, name, filename)
                assert os.path.exists(filepath)
                checksum = self._compute_checksum(filepath)
                logger.info(f"checksum for {filepath}: {checksum}")
                if checksum_expected is not None:
                    assert checksum_expected == checksum

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
