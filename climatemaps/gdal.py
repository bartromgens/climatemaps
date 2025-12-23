import numpy as np


class GdalCalculator:
    """Calculate GDAL overview levels for raster tiles based on image resolution."""

    @staticmethod
    def calculate_max_overview_levels(
        dpi: int, fig_width: float, fig_height: float, minsize: int = 256
    ) -> int:
        """Calculate the maximum number of overview levels that can be created based on image resolution.

        GDAL overview levels are powers of 2 (2, 4, 8, 16, 32, 64, 128, 256, ...).
        The maximum level depends on the image dimensions - gdaladdo stops when the
        smallest overview would be smaller than the minsize threshold (default 256 pixels).

        Args:
            dpi: DPI used to render the image
            fig_width: Figure width in inches
            fig_height: Figure height in inches
            minsize: Minimum size for the smallest overview (default: 256, matching gdaladdo default)

        Returns:
            Maximum number of overview levels (where level 0 is the original, level 1 is 2x downsampled, etc.)
        """
        width_pixels = int(fig_width * dpi)
        height_pixels = int(fig_height * dpi)
        min_dimension = min(width_pixels, height_pixels)

        if min_dimension <= minsize:
            return 0

        # Calculate max level where dimension / (2^level) >= minsize
        # So: 2^level <= dimension / minsize
        # Therefore: level <= log2(dimension / minsize)
        max_level = int(np.floor(np.log2(min_dimension / minsize)))
        return max_level

    @staticmethod
    def calculate_max_zoom_level(
        dpi: int, fig_width: float, fig_height: float, tile_size: int = 256
    ) -> int:
        """Calculate the maximum MBTiles zoom level based on image resolution.

        The maximum zoom level is determined by how many times the image can be
        subdivided into tiles of the specified size (default 256×256 pixels).
        This is different from overview levels - zoom levels represent how the
        image is tiled, not just downsampled.

        Args:
            dpi: DPI used to render the image
            fig_width: Figure width in inches
            fig_height: Figure height in inches
            tile_size: Size of each tile in pixels (default: 256)

        Returns:
            Maximum zoom level (0 = entire image as 1 tile, higher = more subdivisions)
        """
        width_pixels = int(fig_width * dpi)
        height_pixels = int(fig_height * dpi)
        max_dimension = max(width_pixels, height_pixels)

        if max_dimension <= tile_size:
            return 0

        # Calculate max zoom where max_dimension / (2^zoom) >= tile_size
        # So: 2^zoom <= max_dimension / tile_size
        # Therefore: zoom <= log2(max_dimension / tile_size)
        max_zoom = int(np.floor(np.log2(max_dimension / tile_size)))
        return max_zoom

    @staticmethod
    def get_overview_levels_list(max_levels: int) -> list[str]:
        """Generate list of overview level factors for gdaladdo.

        Args:
            max_levels: Maximum number of levels to create

        Returns:
            List of level factors as strings (e.g., ["2", "4", "8", ...])
        """
        levels = []
        for i in range(1, max_levels + 1):
            factor = 2**i
            levels.append(str(factor))
        return levels
