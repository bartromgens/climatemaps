import hashlib
import logging
import os
import tempfile

import pytest
import numpy as np

from climatemaps.contour import Contour
from climatemaps.contour_config import ContourPlotConfig
from climatemaps.geogrid import GeoGrid

logger = logging.getLogger(__name__)


class TestContour:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.contour_plot_config = ContourPlotConfig()
        geo_grid = GeoGrid(
            lon_range=np.array([-135, -45, 45, 135]),
            lat_range=np.array([45, -45]),
            values=np.array([[0, 1, 2, 4], [5, 6, 7, 8]]),
        )
        self.contour = Contour(config=self.contour_plot_config, geo_grid=geo_grid)

    def test_create_tiles(self):
        month = 1
        name = "test"
        expected_colorbar_file = f"{month}_colorbar.png"
        expected_image_file = f"{month}.png"
        expected_geojson_file = f"{month}.geojson"
        expected_raster_tiles_file = f"{month}_raster.mbtiles"
        expected_vector_tiles_file = f"{month}_vector.mbtiles"
        expected_files = {
            expected_colorbar_file: "f8ae25cd2b9a0a7014a0fe48aca14f467856c6228a118ba03759d23466c15616",
            expected_image_file: "021935e7d2d63a568f0b4805e2e117ed442e16af9918723b3eea65f0da0c45c4",
            expected_geojson_file: "b164315696323348d514e34b76999e9a83c9bbc217821687bcfaf2fbde4d9b13",
            expected_raster_tiles_file: "a8a09c479e036df0c1ef61ae6b927f79b626a8322041b2851af8dc90a00667f3",
            expected_vector_tiles_file: None,  # This checksum changes each run, no idea why (timestamp?)
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            self.contour.create_tiles(data_dir_out=tmpdir, name=name, month=month)
            for filename, checksum_expected in expected_files.items():
                filepath = os.path.join(tmpdir, name, filename)
                assert os.path.exists(filepath)
                checksum = self._compute_checksum(filepath)
                logger.warning(f"checksum for {filepath}: {checksum}")
                if checksum_expected is not None:
                    assert checksum_expected == checksum

    @classmethod
    def _compute_checksum(cls, filepath, algorithm="sha256", chunk_size=8192):
        hash_func = hashlib.new(algorithm)
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                hash_func.update(chunk)
        return hash_func.hexdigest()
