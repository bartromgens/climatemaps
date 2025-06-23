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


class Contour:
    world_bounding_box_filepath = "data/world_bounding_box.geojson"

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
        data_dir = self.create_output_dir(data_dir_out, name)
        filepath = os.path.join(str(data_dir), str(month))
        if zoom_factor:
            self.geo_grid = self.geo_grid_orig.zoom(zoom_factor)
        else:
            self.geo_grid = self.geo_grid_orig
        ax, contourf, figure = self._create_contourf()
        self._save_contour_image(figure, filepath, figure_dpi)
        self._create_raster_mbtiles(filepath)
        self._create_colorbar_image(ax, contourf, figure, filepath)
        self._create_contour_vector_mbtiles(filepath, zoomfactor=zoom_factor)
        logger.info(f"DONE: contour for {name} and month {month} and zoomfactor {zoom_factor}")

    @classmethod
    def create_output_dir(cls, data_dir_out, name):
        data_dir = os.path.join(data_dir_out, name)
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)
        return data_dir

    @property
    def values(self):
        return self.geo_grid.clipped_values(self.config.level_lower, self.config.level_upper)

    def _create_contourf(self):
        logger.info(f"BEGIN: create matplotlib contourf")
        figure = Figure(frameon=False)
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

    def _create_colorbar_image(self, ax, contour, figure, filepath):
        logger.info(f"saving colorbar to image")
        cbar = figure.colorbar(contour, format="%.1f")
        cbar.set_label(self.config.title + " [" + self.config.unit + "]")
        cbar.set_ticks(self.config.colorbar_ticks)
        ax.set_visible(False)
        figure.savefig(
            filepath + "_colorbar.png", dpi=150, bbox_inches="tight", pad_inches=0, transparent=True
        )

    @classmethod
    def _create_raster_mbtiles(cls, filepath):
        contour_image_path = f"{filepath}.png"
        mbtiles_path = f"{filepath}_raster.mbtiles"
        logger.info(f"BEGIN: creating raster mbtiles:{mbtiles_path}")
        args = [
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
            mbtiles_path,
        ]
        output = subprocess.check_output(args)
        logger.info(output.decode("utf8"))
        args = ["gdaladdo", "-r", "nearest", mbtiles_path, "2", "4", "8", "16"]
        output = subprocess.check_output(args)
        logger.info(output.decode("utf8"))
        logger.info(f"END: creating raster mbtiles:{mbtiles_path}")

    @classmethod
    def _save_contour_image(cls, figure, filepath, figure_dpi):
        logger.info(f"saving contour to image")
        figure.savefig(
            filepath + ".png", dpi=figure_dpi, bbox_inches="tight", pad_inches=0, transparent=True
        )

    def _create_contour_vector_mbtiles(self, filepath, zoomfactor: float = None):
        logger.info("BEGIN: create contour mbtiles")

        figure = Figure(frameon=False)
        ax = figure.add_subplot(111)
        logger.info(f"creating matplotlib contour")
        contours = ax.contour(
            self.geo_grid.lon_range,
            self.geo_grid.lat_range,
            self.values,
            levels=self.config.levels,
            cmap=self.config.colormap,
            norm=self.config.norm,
        )

        logger.info("converting matplotlib contour to geojson")
        geojsoncontour.contour_to_geojson(
            contour=contours,
            geojson_filepath=filepath + ".geojson",
            unit=self.config.unit,
        )

        assert os.path.exists(self.world_bounding_box_filepath)

        mbtiles_filepath = f"{filepath}_vector.mbtiles"
        logger.info(f"converting geojson_to_mbtiles at {mbtiles_filepath}")
        togeojsontiles.geojson_to_mbtiles(
            filepaths=[filepath + ".geojson", self.world_bounding_box_filepath],
            tippecanoe_dir=settings.TIPPECANOE_DIR,
            mbtiles_file=mbtiles_filepath,
            minzoom=self.zoom_min,
            maxzoom=self.zoom_max,
            full_detail=10,
            lower_detail=9,
            min_detail=7,
            extra_args=["--layer", "contours"],
        )
        logger.info("DONE: create contour mbtiles")
