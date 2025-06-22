import hashlib
import logging
import os
import tempfile

import pytest
import numpy as np

from climatemaps.contour import Contour
from climatemaps.contour import ContourPlotConfig

logger = logging.getLogger(__name__)


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
        month = 1
        name = "test"
        expected_colorbar_file = f"{month}_colorbar.png"
        expected_image_file = f"{month}.png"
        expected_geojson_file = f"{month}.geojson"
        expected_raster_tiles_file = f"{month}_raster.mbtiles"
        expected_vector_tiles_file = f"{month}_vector.mbtiles"
        expected_files = {
            expected_colorbar_file: "f8ae25cd2b9a0a7014a0fe48aca14f467856c6228a118ba03759d23466c15616",
            expected_image_file: "272d837f0a3050274b40497d5fa7638a87da65a47e5ee58fc7f474e50d9b053a",
            expected_geojson_file: "b164315696323348d514e34b76999e9a83c9bbc217821687bcfaf2fbde4d9b13",
            expected_raster_tiles_file: "1956d30f3509dd095deb0f19702963b416fb4d2fd01ed94efa30ab85eca266b9",
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

    @classmethod
    def _compute_checksum(cls, filepath, algorithm="sha256", chunk_size=8192):
        hash_func = hashlib.new(algorithm)
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                hash_func.update(chunk)
        return hash_func.hexdigest()
