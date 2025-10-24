import os
import subprocess

import numpy as np
from matplotlib.figure import Figure
import cartopy.crs as ccrs

import geojsoncontour
import togeojsontiles

from climatemaps.contour_config import ContourPlotConfig
from climatemaps.geogrid import GeoGrid
from climatemaps.settings import settings
from climatemaps.logger import logger
from climatemaps.config import get_config


class ContourTileBuilder:
    world_bounding_box_filepath = "data/raw/world_bounding_box.geojson"

    def __init__(
        self,
        config: ContourPlotConfig,
        geo_grid: GeoGrid,
        zoom_min: int = 0,
        zoom_max: int = 5,
    ):
        logger.info(f"Contour zoom {zoom_min}-{zoom_max}")
        self.zoom_min = zoom_min
        self.zoom_max = zoom_max
        self.config = config
        self.geo_grid_orig = geo_grid
        self.geo_grid = geo_grid
        logger.info(f"lon min, max: {self.geo_grid.lon_min}, {self.geo_grid.lon_max}")
        logger.info(f"lat min, max: {self.geo_grid.lat_min}, {self.geo_grid.lat_max}")

    def create_tiles(
        self,
        data_dir_out: str,
        name: str,
        month: int,
        figure_dpi: int = 700,
        zoom_factor: float = 2.0,
    ):
        logger.info(f"BEGIN: contour for {name} and month {month} and zoomfactor {zoom_factor}")
        data_dir = self._create_output_dir(data_dir_out, name)
        filepath = os.path.join(str(data_dir), str(month))
        if zoom_factor and not self._is_high_resolution():
            self.geo_grid = self.geo_grid_orig.zoom(zoom_factor)
        else:
            self.geo_grid = self.geo_grid_orig

        # Adjust DPI for high-resolution data to maintain grid resolution
        adjusted_dpi, fig_width, fig_height = self._calculate_appropriate_dpi(figure_dpi)
        logger.info(f"Using DPI: {adjusted_dpi} (original: {figure_dpi})")
        logger.info(f'Figure size: {fig_width:.1f}" x {fig_height:.1f}"')

        ax, contourf, figure = self._create_contourf(fig_width, fig_height)
        self._save_contour_image(figure, filepath, adjusted_dpi)
        self._create_raster_mbtiles(filepath)
        self._create_colorbar_image(ax, contourf, figure, filepath)
        self._create_contour_vector_mbtiles(filepath, zoom_factor=zoom_factor)
        logger.info(f"DONE: contour for {name} and month {month} and zoomfactor {zoom_factor}")

    @classmethod
    def _create_output_dir(cls, data_dir_out, name):
        data_dir = os.path.join(data_dir_out, name)
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)
        return data_dir

    @property
    def values(self):
        return self.geo_grid.clipped_values(self.config.level_lower, self.config.level_upper)

    def _create_contourf(self, fig_width: float = 10.0, fig_height: float = None):
        # Check if this is high-resolution data that should use 2D histogram
        if self._is_high_resolution():
            return self._create_2d_histogram(fig_width, fig_height)
        else:
            return self._create_contour_plot(fig_width, fig_height)

    def _is_high_resolution(self):
        """Check if the data is high-resolution and should use 2D histogram instead of contours"""
        # Consider high-resolution if we have more than 10 million pixels
        total_pixels = len(self.geo_grid.lon_range) * len(self.geo_grid.lat_range)
        return total_pixels > 10_000_000

    def _calculate_appropriate_dpi(
        self, base_dpi: int, standard_fig_width: float = 10.0
    ) -> tuple[int, float, float]:
        """Calculate appropriate DPI to maintain grid resolution in the output image"""
        # Calculate the aspect ratio of the geographic extent
        lon_extent = self.geo_grid.urcrnrlon - self.geo_grid.llcrnrlon
        lat_extent = self.geo_grid.urcrnrlat - self.geo_grid.llcrnrlat
        aspect_ratio = lon_extent / lat_extent

        # Calculate figure height based on aspect ratio
        standard_fig_height = standard_fig_width / aspect_ratio

        if not self._is_high_resolution():
            return base_dpi, standard_fig_width, standard_fig_height

        # For high-resolution data, calculate DPI needed to maintain grid resolution
        grid_width = len(self.geo_grid.lon_range)
        grid_height = len(self.geo_grid.lat_range)

        # Calculate DPI needed to maintain grid resolution
        required_dpi_width = grid_width / standard_fig_width
        required_dpi_height = grid_height / standard_fig_height
        required_dpi = max(required_dpi_width, required_dpi_height)

        # Use the higher of the required DPI or base DPI
        adjusted_dpi = max(int(required_dpi), base_dpi)

        logger.info(f"Grid resolution: {grid_width} x {grid_height}")
        logger.info(f'Figure size: {standard_fig_width:.1f}" x {standard_fig_height:.1f}"')
        logger.info(f"Required DPI: {required_dpi:.1f}, using: {adjusted_dpi}")

        return adjusted_dpi, standard_fig_width, standard_fig_height

    def _calculate_fig_height(self, fig_width: float) -> float:
        """Calculate figure height based on geographic extent aspect ratio"""
        lon_extent = self.geo_grid.urcrnrlon - self.geo_grid.llcrnrlon
        lat_extent = self.geo_grid.urcrnrlat - self.geo_grid.llcrnrlat
        aspect_ratio = lon_extent / lat_extent
        return fig_width / aspect_ratio

    def _create_figure_and_axes(self, fig_width: float, fig_height: float):
        """Create figure and axes with proper geographic extent"""
        figure = Figure(frameon=False, figsize=(fig_width, fig_height))
        # Remove padding to use full figure area
        figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
        ax = figure.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        ax.set_extent(
            [
                self.geo_grid.llcrnrlon,
                self.geo_grid.urcrnrlon,
                self.geo_grid.llcrnrlat,
                self.geo_grid.urcrnrlat,
            ],
            crs=ccrs.PlateCarree(),
        )
        logger.info(
            f"create base map [{self.geo_grid.lon_min}, {self.geo_grid.lon_max}], [{self.geo_grid.lat_min}, {self.geo_grid.lat_max}]"
        )
        logger.info(
            f"llcrnrlat: {self.geo_grid.llcrnrlat}, llcrnrlon: {self.geo_grid.llcrnrlon}, urcrnrlat: {self.geo_grid.urcrnrlat}, urcrnrlon: {self.geo_grid.urcrnrlon}"
        )
        return figure, ax

    def _create_2d_histogram(self, fig_width: float = 10.0, fig_height: float = None):
        """Create a 2D histogram plot for high-resolution data (much faster than contours)"""
        logger.info(f"BEGIN: create 2D histogram for high-resolution data")
        if fig_height is None:
            fig_height = self._calculate_fig_height(fig_width)

        figure, ax = self._create_figure_and_axes(fig_width, fig_height)
        logger.info(f"Using 2D histogram for high-resolution data")

        # Use pcolormesh for high-resolution data (much faster than contourf)
        lon_grid, lat_grid = np.meshgrid(self.geo_grid.lon_range, self.geo_grid.lat_range)
        im = ax.pcolormesh(
            lon_grid,
            lat_grid,
            self.values,
            transform=ccrs.PlateCarree(),
            cmap=self.config.colormap,
            norm=self.config.norm,
            shading="auto",
        )
        ax.axis("off")
        logger.info(f"DONE: create 2D histogram")
        return ax, im, figure

    def _create_contour_plot(self, fig_width: float = 10.0, fig_height: float = None):
        """Create traditional contour plot for lower-resolution data"""
        logger.info(f"BEGIN: create matplotlib contourf")
        if fig_height is None:
            fig_height = self._calculate_fig_height(fig_width)

        figure, ax = self._create_figure_and_axes(fig_width, fig_height)
        logger.info(f"levels image: {self.config.levels_image}")
        lon_grid, lat_grid = np.meshgrid(self.geo_grid.lon_range, self.geo_grid.lat_range)
        contourf = ax.contourf(
            lon_grid,
            lat_grid,
            self.values,
            transform=ccrs.PlateCarree(),
            cmap=self.config.colormap,
            levels=self.config.levels_image,
            norm=self.config.norm,
        )
        ax.axis("off")
        logger.info(f"DONE: create matplotlib contourf")
        return ax, contourf, figure

    @classmethod
    def _create_raster_mbtiles(cls, filepath):
        contour_image_path = f"{filepath}.png"
        mbtiles_path = f"{filepath}_raster.mbtiles"
        mbtiles_temp_path = f"{mbtiles_path}.tmp"
        logger.info(f"BEGIN: creating raster mbtiles: {mbtiles_path}")

        translate_cmd = [
            "gdal_translate",
            "-of",
            "MBTILES",
            "-a_ullr",
            "-180.0",
            "90.0",
            "180.0",
            "-90.0",
            "-a_srs",
            "EPSG:4326",
            contour_image_path,
            mbtiles_temp_path,
        ]

        addo_cmd = [
            "gdaladdo",
            "-r",
            "lanczos",
            mbtiles_temp_path,
            "2",
            "4",
            "8",
            "16",
            "32",
            "64",
            "128",
        ]

        try:
            logger.debug(f"Running: {' '.join(translate_cmd)}")
            out = subprocess.check_output(translate_cmd, stderr=subprocess.STDOUT)
            logger.info(out.decode("utf-8"))

            logger.debug(f"Running: {' '.join(addo_cmd)}")
            out = subprocess.check_output(addo_cmd, stderr=subprocess.STDOUT)
            logger.info(out.decode("utf-8"))

            logger.info(f"Atomically moving {mbtiles_temp_path} to {mbtiles_path}")
            os.replace(mbtiles_temp_path, mbtiles_path)
        except subprocess.CalledProcessError as e:
            logger.error(
                f"GDAL command failed (exit {e.returncode}): {e.cmd}\n"
                f"Output: {e.output.decode('utf-8', errors='replace')}"
            )
            if os.path.exists(mbtiles_temp_path):
                logger.info(f"Removing incomplete temp file: {mbtiles_temp_path}")
                os.remove(mbtiles_temp_path)
            raise
        finally:
            if os.path.exists(contour_image_path):
                config = get_config()
                if not config.dev_mode:
                    logger.info(f"Removing temporary PNG file: {contour_image_path}")
                    os.remove(contour_image_path)
                else:
                    logger.info(f"Keeping temporary PNG file in dev mode: {contour_image_path}")
        logger.info(f"END: creating raster mbtiles:{mbtiles_path}")

    @classmethod
    def _save_contour_image(cls, figure, filepath, figure_dpi):
        logger.info(f"BEGIN: save contour to image")
        # For high-resolution data, don't use bbox_inches="tight" as it crops the image
        # and can result in different dimensions than expected
        figure.savefig(filepath + ".png", dpi=figure_dpi, pad_inches=0, transparent=True)
        logger.info(f"END: save contour to image")

    def _create_contour_vector_mbtiles(self, filepath, zoom_factor: float = None):
        logger.info("BEGIN: create contour mbtiles")

        # For very high-resolution data, downsample before creating contours
        if self._is_high_resolution():
            logger.info("Downsampling high-resolution data for vector contours")
            # Calculate appropriate downsampling factor to get under 10M pixels
            total_pixels = len(self.geo_grid.lon_range) * len(self.geo_grid.lat_range)
            target_pixels = 10_000_000  # Target 10M pixels for good balance
            downsample_factor = int(np.ceil(np.sqrt(total_pixels / target_pixels)))
            logger.info(f"Downsampling by factor of {downsample_factor}")

            # Create downsampled grid for contours
            downsampled_grid = self.geo_grid.downsample(factor=downsample_factor)
            contour_lon_range = downsampled_grid.lon_range
            contour_lat_range = downsampled_grid.lat_range
            contour_values = downsampled_grid.values
        else:
            contour_lon_range = self.geo_grid.lon_range
            contour_lat_range = self.geo_grid.lat_range
            contour_values = self.values

        figure = Figure(frameon=False)
        ax = figure.add_subplot(1, 1, 1)
        logger.info(f"creating matplotlib contour")
        contours = ax.contour(
            contour_lon_range,
            contour_lat_range,
            contour_values,
            levels=self.config.levels,
            cmap=self.config.colormap,
            norm=self.config.norm,
        )

        geojson_filepath = filepath + ".geojson"
        logger.info("converting matplotlib contour to geojson")
        geojsoncontour.contour_to_geojson(
            contour=contours,
            geojson_filepath=geojson_filepath,
            unit=self.config.unit,
        )

        assert os.path.exists(self.world_bounding_box_filepath)

        mbtiles_filepath = f"{filepath}_vector.mbtiles"
        mbtiles_temp_filepath = f"{mbtiles_filepath}.tmp"
        logger.info(f"converting geojson_to_mbtiles at {mbtiles_filepath}")

        try:
            togeojsontiles.geojson_to_mbtiles(
                filepaths=[geojson_filepath, self.world_bounding_box_filepath],
                tippecanoe_dir=settings.TIPPECANOE_DIR,
                mbtiles_file=mbtiles_temp_filepath,
                minzoom=self.zoom_min,
                maxzoom=self.zoom_max,
                full_detail=10,
                lower_detail=9,
                min_detail=7,
                extra_args=["--layer", "contours"],
            )

            logger.info(f"Atomically moving {mbtiles_temp_filepath} to {mbtiles_filepath}")
            os.replace(mbtiles_temp_filepath, mbtiles_filepath)
        except Exception as e:
            logger.error(f"Failed to create vector mbtiles: {e}")
            if os.path.exists(mbtiles_temp_filepath):
                logger.info(f"Removing incomplete temp file: {mbtiles_temp_filepath}")
                os.remove(mbtiles_temp_filepath)
            raise
        finally:
            logger.info(f"removing temporary geojson file: {geojson_filepath}")
            if os.path.exists(geojson_filepath):
                os.remove(geojson_filepath)

        logger.info("DONE: create contour mbtiles")

    def _create_colorbar_image(self, ax, contour_or_im, figure, filepath):
        logger.info(f"saving colorbar to image")
        cbar = figure.colorbar(contour_or_im, format="%.1f")
        cbar.set_label(self.config.title + " [" + self.config.unit + "]")
        cbar.set_ticks(self.config.colorbar_ticks)
        ax.set_visible(False)
        figure.savefig(
            filepath + "_colorbar.png", dpi=150, bbox_inches="tight", pad_inches=0, transparent=True
        )
