from climatemaps.gdal import GdalCalculator
from climatemaps.logger import logger


class TestGdalCalculator:
    def test_min_resolution_for_zoom_levels_1_2_aspect_ratio(self):
        """
        Zoom level | Width (px) | Height (px) | Total Pixels
        0     |      128 |       256 |        32,768
        1     |      256 |       512 |       131,072
        2     |      512 |      1024 |       524,288
        3     |     1024 |      2048 |     2,097,152
        4     |     2048 |      4096 |     8,388,608
        5     |     4096 |      8192 |    33,554,432
        6     |     8192 |     16384 |   134,217,728
        7     |    16384 |     32768 |   536,870,912
        8     |    32768 |     65536 | 2,147,483,648
        """
        logger.info("Minimum required resolution (1:2 aspect ratio) for zoom levels 0-8:")
        logger.info("Zoom Level | Width (px) | Height (px) | Total Pixels")
        logger.info("-" * 60)

        for zoom_level in range(0, 9):
            width, height = GdalCalculator.calculate_min_resolution_for_zoom_level(
                zoom_level, aspect_ratio_width=1.0, aspect_ratio_height=2.0
            )
            total_pixels = width * height
            logger.info(f"    {zoom_level:2d}     | {width:8d} | {height:9d} | {total_pixels:13,}")

            # Verify that this resolution actually achieves the target zoom level
            calculated_zoom = GdalCalculator.calculate_max_zoom_level_from_pixels(width, height)
            assert calculated_zoom == zoom_level, (
                f"Resolution {width}x{height} should achieve zoom level {zoom_level}, "
                f"but calculated zoom is {calculated_zoom}"
            )
