import pytest
from climatemaps.gdal import GdalCalculator
from climatemaps.logger import logger


class TestGdalCalculator:
    def test_min_resolution_for_zoom_levels_1_2_aspect_ratio(self):
        """
        Zoom Level | Width (px) | Height (px) | Total Pixels | Spatial Resolution
        --------------------------------------------------------------------------------
        0     |      128 |       256 |        32,768 |   84.4m
        1     |      256 |       512 |       131,072 |   42.2m
        2     |      512 |      1024 |       524,288 |   21.1m
        3     |     1024 |      2048 |     2,097,152 |   10.5m
        4     |     2048 |      4096 |     8,388,608 |    5.3m
        5     |     4096 |      8192 |    33,554,432 |    2.6m
        6     |     8192 |     16384 |   134,217,728 |    1.3m
        7     |    16384 |     32768 |   536,870,912 |    0.7m
        8     |    32768 |     65536 | 2,147,483,648 |    0.3m
        """
        logger.info("Minimum required resolution (1:2 aspect ratio) for zoom levels 0-8:")
        logger.info("Zoom Level | Width (px) | Height (px) | Total Pixels | Spatial Resolution")
        logger.info("-" * 80)

        for zoom_level in range(0, 9):
            width, height = GdalCalculator.calculate_min_resolution_for_zoom_level(
                zoom_level, aspect_ratio_width=1.0, aspect_ratio_height=2.0
            )
            total_pixels = width * height
            spatial_resolution = GdalCalculator.calculate_spatial_resolution_for_zoom_level(
                zoom_level
            )
            logger.info(
                f"    {zoom_level:2d}     | {width:8d} | {height:9d} | {total_pixels:13,} | {spatial_resolution:>6.1f}m"
            )

            # Verify that this resolution actually achieves the target zoom level
            calculated_zoom = GdalCalculator.calculate_max_zoom_level_from_pixels(width, height)
            assert calculated_zoom == zoom_level, (
                f"Resolution {width}x{height} should achieve zoom level {zoom_level}, "
                f"but calculated zoom is {calculated_zoom}"
            )

    def test_calculate_max_zoom_raster_from_minutes(self):
        resolution_minutes = 2.5
        max_zoom = GdalCalculator.calculate_max_zoom_raster_from_minutes(resolution_minutes)

        world_width_minutes = 360 * 60
        world_height_minutes = 180 * 60
        width_pixels = int(world_width_minutes / resolution_minutes)
        height_pixels = int(world_height_minutes / resolution_minutes)
        expected_zoom = GdalCalculator.calculate_max_zoom_level_from_pixels(
            width_pixels, height_pixels
        )

        assert max_zoom == expected_zoom
