import math
import os
import subprocess

from PIL import Image

from mpl_toolkits.basemap import Basemap
import numpy as np
import numpy.typing as npt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.colors import SymLogNorm
import scipy.ndimage

import geojsoncontour
import togeojsontiles

from climatemaps.logger import logger


TIPPECANOE_DIR = "/usr/local/bin/"


def dot_product(v1, v2):
    return sum((a * b) for a, b in zip(v1, v2))


def length(v):
    return math.sqrt(dot_product(v, v))


def angle(v1, v2):
    cos_angle = dot_product(v1, v2) / (length(v1) * length(v2))
    cos_angle = min(1.0, max(cos_angle, -1.0))
    assert cos_angle <= 1.0
    assert cos_angle >= -1.0
    return math.acos(cos_angle)


class ContourPlotConfig:
    def __init__(
        self,
        level_lower=0,
        level_upper=100,
        colormap=plt.cm.jet,
        title="",
        unit="",
        logscale=False,
        n_contours=21,
    ):  # jet, jet_r, YlOrRd, gist_rainbow
        self.n_contours = n_contours
        self.min_angle_between_segments = 5
        self.level_lower = level_lower
        self.level_upper = level_upper
        self.colormap = colormap
        self.title = title
        self.unit = unit
        self.norm = None

        if logscale:
            assert self.level_lower > 0
            self.norm = SymLogNorm(linthresh=1.0, vmin=self.level_lower, vmax=self.level_upper)
            self.levels = np.logspace(
                start=self.level_lower,
                stop=math.log(self.level_upper + 2),
                num=self.n_contours,
                base=math.e,
            )
            # TODO: why is this needed?
            for i in range(0, len(self.levels)):
                self.levels[i] -= 1.0
        else:
            self.levels = np.linspace(
                start=self.level_lower, stop=self.level_upper, num=self.n_contours
            )

        if logscale:
            assert self.level_lower > 0
            self.levels_image = np.logspace(
                start=math.log(self.level_lower) - 0.0001,  # TODO: why is this needed?
                stop=math.log(self.level_upper + 2),
                num=self.n_contours * 20,
                base=math.e,
            )
            # TODO: why is this needed?
            # for i in range(0, len(self.levels_image)):
            #     self.levels_image[i] -= 1.0
            # print(self.levels_image)
        else:
            self.levels_image = np.linspace(
                start=self.level_lower, stop=self.level_upper, num=self.n_contours * 20
            )

        # use half the number of levels for the colorbar ticks
        counter = 0
        self.colorbar_ticks = []
        for level in self.levels:
            if counter % 2 == 0:
                self.colorbar_ticks.append(level)
            counter += 1
        # print(self.levels)
        # print(self.levels_image)


class Contour:

    def __init__(
        self,
        config: ContourPlotConfig,
        lon_range: npt.NDArray[np.floating],
        lat_range: npt.NDArray[np.floating],
        values: npt.NDArray[np.floating],
        zoom_min: int = 0,
        zoom_max: int = 5,
    ):
        logger.info(f"Contour zoom {zoom_min}-{zoom_max}")
        self.zoom_min = zoom_min
        self.zoom_max = zoom_max
        self.config = config
        for i in range(0, values.shape[0]):
            for j in range(0, values.shape[1]):
                if values[i][j] >= config.level_upper:
                    values[i][j] = config.level_upper
                elif values[i][j] <= config.level_lower:
                    values[i][j] = config.level_lower

        self.values = values
        self.lon_range = lon_range
        self.lat_range = lat_range
        logger.info(f"lon min, max {self.lon_min}, {self.lon_max}")
        logger.info(f"lat min, max {self.lat_min}, {self.lat_max}")
        np.set_printoptions(3, threshold=100, suppress=True)  # .3f

    def create_tiles(
        self,
        data_dir_out: str,
        name: str,
        month: int,
        figure_dpi: int = 700,
        zoom_factor: float = 2.0,
    ):
        logger.info(f"BEGIN: contour for {name} and month {month} and zoomfactor {zoom_factor}")
        figure = Figure(frameon=False)
        FigureCanvas(figure)

        ax = figure.add_subplot(111)
        logger.info(
            f"BEGIN: create base map [{self.lon_min}, {self.lon_max}], [{self.lat_min}, {self.lat_max}]"
        )
        logger.info(f"bin_width {self.bin_width_lon}")
        logger.info(
            f"llcrnrlat: {self.llcrnrlat}, llcrnrlon: {self.llcrnrlon}, urcrnrlat: {self.urcrnrlat}, urcrnrlon: {self.urcrnrlon}"
        )
        m = Basemap(
            epsg="4326",
            # projection='cyl',
            # resolution='l',
            lon_0=0,
            ax=ax,
            llcrnrlon=self.llcrnrlon,
            llcrnrlat=self.llcrnrlat,
            urcrnrlon=self.urcrnrlon,
            urcrnrlat=self.urcrnrlat,
        )
        x, y = m(*np.meshgrid(self.lon_range, self.lat_range))
        logger.info(f"DONE: create base map")
        logger.info(f"BEGIN: create matplotlib contourf")
        logger.info(f"levels image: {self.config.levels_image}")

        data_dir = os.path.join(data_dir_out, name)
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)
        filepath = os.path.join(str(data_dir), str(month))

        contour = m.contourf(
            x,
            y,
            self.values,
            cmap=self.config.colormap,
            levels=self.config.levels_image,
            norm=self.config.norm,
        )
        ax.set_axis_off()
        logger.info(f"DONE: create matplotlib contourf")

        logger.info(f"BEGIN: create contourf image")
        self._save_contour_image(figure, filepath, figure_dpi)
        self._create_colorbar_image(ax, contour, figure, filepath)
        self._create_raster_mbtiles(filepath)
        logger.info(f"DONE: create contourf image")

        self._create_contour_mbtiles(filepath, zoomfactor=zoom_factor)
        logger.info(f"DONE: contour for {name} and month {month}")

    @property
    def lat_min(self):
        return self.lat_range[-1]

    @property
    def lat_max(self):
        return self.lat_range[0]

    @property
    def lon_min(self):
        return self.lon_range[0]

    @property
    def lon_max(self):
        return self.lon_range[-1]

    @property
    def bin_width(self):
        assert self.bin_width_lon == self.bin_width_lat
        return self.bin_width_lon

    @property
    def bin_width_lon(self):
        return 360.0 / len(self.lon_range)

    @property
    def bin_width_lat(self):
        return 180.0 / len(self.lat_range)

    @property
    def llcrnrlon(self):
        """lower left corner longitude"""
        return self.lon_min - self.bin_width / 2

    @property
    def llcrnrlat(self):
        """lower left corner latitude"""
        return self.lat_min - self.bin_width / 2

    @property
    def urcrnrlon(self):
        """upper right corner longitude"""
        return self.lon_max + self.bin_width / 2

    @property
    def urcrnrlat(self):
        """upper right corner latitude"""
        return self.lat_max + self.bin_width / 2

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
        print(output.decode("utf8"))
        args = ["gdaladdo", "-r", "nearest", mbtiles_path, "2", "4", "8", "16"]
        output = subprocess.check_output(args)
        print(output.decode("utf8"))
        logger.info(f"END: creating raster mbtiles:{mbtiles_path}")

    @classmethod
    def _save_contour_image(cls, figure, filepath, figure_dpi):
        logger.info(f"saving contour to image")
        figure.savefig(
            filepath + ".png", dpi=figure_dpi, bbox_inches="tight", pad_inches=0, transparent=True
        )

    def _create_contour_mbtiles(self, filepath, zoomfactor: float = None):
        logger.info("BEGIN: create contour mbtiles")
        if zoomfactor is not None:
            self.values = scipy.ndimage.zoom(self.values, zoom=zoomfactor, order=1)
            self.lon_range = scipy.ndimage.zoom(self.lon_range, zoom=zoomfactor, order=1)
            self.lat_range = scipy.ndimage.zoom(self.lat_range, zoom=zoomfactor, order=1)

        figure = Figure(frameon=False)
        FigureCanvas(figure)
        ax = figure.add_subplot(111)
        logger.info(f"creating matplotlib contour")
        contours = ax.contour(
            self.lon_range,
            self.lat_range,
            self.values,
            levels=self.config.levels,
            cmap=self.config.colormap,
            norm=self.config.norm,
        )
        figure.clear()

        logger.info("converting matplotlib contour to geojson")
        geojsoncontour.contour_to_geojson(
            contour=contours,
            geojson_filepath=filepath + ".geojson",
            unit=self.config.unit,
        )

        world_bounding_box_filepath = "data/world_bounding_box.geojson"
        assert os.path.exists(world_bounding_box_filepath)

        mbtiles_filepath = f"{filepath}_vector.mbtiles"
        logger.info(f"converting geojson_to_mbtiles at {mbtiles_filepath}")
        togeojsontiles.geojson_to_mbtiles(
            filepaths=[filepath + ".geojson", world_bounding_box_filepath],
            tippecanoe_dir=TIPPECANOE_DIR,
            mbtiles_file=mbtiles_filepath,
            minzoom=self.zoom_min,
            maxzoom=self.zoom_max,
            full_detail=10,
            lower_detail=9,
            min_detail=7,
            extra_args=["--layer", "contours"],
        )
        logger.info("DONE: create contour mbtiles")
