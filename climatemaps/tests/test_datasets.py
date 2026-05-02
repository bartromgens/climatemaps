import pytest
from climatemaps.datasets import ClimateDataConfig, ClimateVarKey, SpatialResolution, DataFormat
from climatemaps.gdal import GdalCalculator
from climatemaps.geotiff import read_geotiff_future


class TestClimateDataConfig:
    def test_zoom_factor_min1_5_resolution(self):
        """Test zoom_factor property for MIN1_5 resolution (1.5m)"""
        config = ClimateDataConfig(
            variable_type=ClimateVarKey.T_MAX,
            filepath="test.nc",
            format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
            resolution_input=SpatialResolution.MIN1_5,
            year_range=(2021, 2040),
            reader_function=read_geotiff_future,
        )

        current_max_zoom = GdalCalculator.calculate_max_zoom_raster(SpatialResolution.MIN1_5)
        target_max_zoom = config.target_max_zoom_raster
        zoom_factor = config.zoom_factor

        assert (
            current_max_zoom == 5
        ), f"MIN1_5 resolution should support zoom level 5, got {current_max_zoom}"
        assert target_max_zoom == 6, f"Target zoom should be 6 for MIN1_5, got {target_max_zoom}"
        assert (
            zoom_factor is not None
        ), f"Zoom factor should not be None for MIN1_5 (needs to reach zoom level 6), got {zoom_factor}"
        expected_zoom_factor = 1.1548444444444443
        assert zoom_factor == pytest.approx(
            expected_zoom_factor, rel=1e-5
        ), f"Zoom factor should be approximately {expected_zoom_factor:.6f} to increase from zoom 5 to 6, got {zoom_factor}"
