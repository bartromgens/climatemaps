import numpy as np

from climatemaps.datasets import SpatialResolution


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

        Returns:
            Maximum zoom level (0 = entire image as 1 tile, higher = more subdivisions)
        """
        width_pixels = int(fig_width * dpi)
        height_pixels = int(fig_height * dpi)
        return GdalCalculator.calculate_max_zoom_level_from_pixels(
            width_pixels, height_pixels, tile_size
        )

    @staticmethod
    def calculate_max_zoom_level_from_pixels(
        width_pixels: int, height_pixels: int, tile_size: int = 256
    ) -> int:
        """Calculate the maximum MBTiles zoom level based on pixel dimensions.

        The maximum zoom level is determined by how many times the image can be
        subdivided into tiles of the specified size (default 256×256 pixels).
        This is different from overview levels - zoom levels represent how the
        image is tiled, not just downsampled.

        Returns:
            Maximum zoom level (0 = entire image as 1 tile, higher = more subdivisions)
        """
        max_dimension = max(width_pixels, height_pixels)

        if max_dimension <= tile_size:
            return 0

        # Calculate max zoom where max_dimension / (2^zoom) >= tile_size
        # So: 2^zoom <= max_dimension / tile_size
        # Therefore: zoom <= log2(max_dimension / tile_size)
        max_zoom = int(np.floor(np.log2(max_dimension / tile_size)))
        return max_zoom

    @staticmethod
    def calculate_min_resolution_for_zoom_level(
        zoom_level: int,
        aspect_ratio_width: float = 1.0,
        aspect_ratio_height: float = 1.0,
        tile_size: int = 256,
    ) -> tuple[int, int]:
        """Calculate the minimum required resolution (width, height in pixels) to achieve a given zoom level.

        The zoom level determines how many times the image can be subdivided into tiles.
        This function calculates the minimum pixel dimensions needed to support the specified zoom level
        while maintaining the given aspect ratio.

        Returns:
            Tuple of (width_pixels, height_pixels) representing minimum required resolution
        """
        if zoom_level < 0:
            raise ValueError("Zoom level must be non-negative")

        # Calculate the minimum max dimension needed for this zoom level
        # max_dimension = tile_size * 2^zoom_level
        min_max_dimension = tile_size * (2**zoom_level)

        # Calculate aspect ratio
        aspect = aspect_ratio_width / aspect_ratio_height

        # Determine which dimension is larger based on aspect ratio
        if aspect >= 1.0:
            # Width is larger or equal
            width = min_max_dimension
            height = int(min_max_dimension / aspect)
        else:
            # Height is larger
            height = min_max_dimension
            width = int(min_max_dimension * aspect)

        return width, height

    @staticmethod
    def get_overview_levels_list(max_levels: int) -> list[str]:
        """Generate list of overview level factors for gdaladdo.

        Returns:
            List of level factors as strings (e.g., ["2", "4", "8", ...])
        """
        levels = []
        for i in range(1, max_levels + 1):
            factor = 2**i
            levels.append(str(factor))
        return levels

    @staticmethod
    def calculate_max_zoom_raster(resolution: SpatialResolution) -> int:
        """Calculate the maximum zoom level for raster tiles based on spatial resolution."""
        return 6 if resolution == SpatialResolution.MIN0_5 else 5
