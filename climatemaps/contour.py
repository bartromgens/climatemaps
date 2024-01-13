import math
import os
import subprocess

from PIL import Image

from mpl_toolkits.basemap import Basemap
import numpy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.colors import SymLogNorm
import scipy.ndimage

import geojsoncontour
import togeojsontiles

from climatemaps.logger import logger


TIPPECANOE_DIR = '/usr/local/bin/'


def dotproduct(v1, v2):
    return sum((a * b) for a, b in zip(v1, v2))


def length(v):
    return math.sqrt(dotproduct(v, v))


def angle(v1, v2):
    cos_angle = dotproduct(v1, v2) / (length(v1) * length(v2))
    cos_angle = min(1.0, max(cos_angle, -1.0))
    assert cos_angle <= 1.0
    assert cos_angle >= -1.0
    return math.acos(cos_angle)


class ContourPlotConfig(object):
    def __init__(self,
                 level_lower=0,
                 level_upper=100,
                 colormap=plt.cm.jet,
                 title='',
                 unit='',
                 logscale=False,
                 n_contours=21):  # jet, jet_r, YlOrRd, gist_rainbow
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
            self.levels = numpy.logspace(
                start=self.level_lower,
                stop=math.log(self.level_upper+2),
                num=self.n_contours,
                base=math.e
            )
            # TODO: why is this needed?
            for i in range(0, len(self.levels)):
                self.levels[i] -= 1.0
        else:
            self.levels = numpy.linspace(
                start=self.level_lower,
                stop=self.level_upper,
                num=self.n_contours
            )

        if logscale:
            assert self.level_lower > 0
            self.levels_image = numpy.logspace(
                start=math.log(self.level_lower)-0.0001,  # TODO: why is this needed?
                stop=math.log(self.level_upper+2),
                num=self.n_contours*20,
                base=math.e
            )
            # TODO: why is this needed?
            # for i in range(0, len(self.levels_image)):
            #     self.levels_image[i] -= 1.0
            # print(self.levels_image)
        else:
            self.levels_image = numpy.linspace(
                start=self.level_lower,
                stop=self.level_upper,
                num=self.n_contours*20
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


class Contour(object):

    def __init__(self, config: ContourPlotConfig, lonrange, latrange, Z, zoom_min=0, zoom_max=5):
        logger.info(f'Contour zoom {zoom_min}-{zoom_max}')
        self.zoom_min = zoom_min
        self.zoom_max = zoom_max
        self.config = config
        for i in range(0, Z.shape[0]):
            for j in range(0, Z.shape[1]):
                if Z[i][j] >= config.level_upper:
                    Z[i][j] = config.level_upper
                elif Z[i][j] <= config.level_lower:
                    Z[i][j] = config.level_lower

        self.Z = Z
        self.lonrange = lonrange
        # self.latrange = latrange
        self.latrange = latrange[::-1]
        logger.info(f"lat min, max {self.lat_min}, {self.lat_max}")
        numpy.set_printoptions(3, threshold=100, suppress=True)  # .3f

    @property
    def lat_min(self):
        return self.latrange[-1]

    @property
    def lat_max(self):
        return self.latrange[0]

    @property
    def lon_min(self):
        return self.lonrange[0]

    @property
    def lon_max(self):
        return self.lonrange[-1]

    def create_contour_data(self, data_dir_out, name, month, figure_dpi=700, create_images=True, zoomfactor=2.0):
        logger.info(f'creating contour for {name} and month {month} and zoomfactor {zoomfactor}')
        figure = Figure(frameon=False)
        FigureCanvas(figure)

        ax = figure.add_subplot(111)
        logger.info(f'creating base map')
        m = Basemap(
            epsg='4326',
            # projection='cyl',
            # resolution='l',
            lon_0=0,
            ax=ax,
            llcrnrlon=self.lon_min,
            llcrnrlat=self.lat_min,
            urcrnrlon=self.lon_max,
            urcrnrlat=self.lat_max,
        )
        x, y = m(*numpy.meshgrid(self.lonrange, self.latrange))
        logger.info(f'creating matplotlib contourf')
        contour = m.contourf(
            x, y, self.Z,
            cmap=self.config.colormap,
            levels=self.config.levels_image,
            norm=self.config.norm
        )
        # m.drawcoastlines(linewidth=0.1)  # draw coastlines
        # cbar = figure.colorbar(contour, format='%.1f')
        ax.set_axis_off()

        data_dir = os.path.join(data_dir_out, name)
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)
        filepath = os.path.join(data_dir, str(month))
        self.save_contour_image(figure, filepath, figure_dpi)
        self.create_colorbar_image(ax, contour, figure, filepath)

        if create_images:
            self.create_image_tiles(filepath)
        else:
            logger.warning('skipping creation of image tiles')
        self.create_contour_json(filepath, zoomfactor=zoomfactor)
        logger.info(f'finished contour for {name} and month {month}')

    def create_colorbar_image(self, ax, contour, figure, filepath):
        logger.info(f'saving colorbar to image')
        cbar = figure.colorbar(contour, format='%.1f')
        cbar.set_label(self.config.title + ' [' + self.config.unit + ']')
        cbar.set_ticks(self.config.colorbar_ticks)
        ax.set_visible(False)
        figure.savefig(
            filepath + "_colorbar.png",
            dpi=150,
            bbox_inches='tight',
            pad_inches=0,
            transparent=True
        )

    @classmethod
    def save_contour_image(cls, figure, filepath, figure_dpi):
        logger.info(f'saving contour to image')
        figure.savefig(
            filepath + '.png',
            dpi=figure_dpi,
            bbox_inches='tight',
            pad_inches=0,
            transparent=True
        )

    def create_contour_json(self, filepath, zoomfactor: float = None):
        logger.info('START: create contour json tiles')
        if zoomfactor is not None:
            self.Z = scipy.ndimage.zoom(self.Z, zoom=zoomfactor, order=1)
            self.lonrange = scipy.ndimage.zoom(self.lonrange, zoom=zoomfactor, order=1)
            self.latrange = scipy.ndimage.zoom(self.latrange, zoom=zoomfactor, order=1)

        figure = Figure(frameon=False)
        FigureCanvas(figure)
        ax = figure.add_subplot(111)
        logger.info(f'creating matplotlib contour')
        contours = ax.contour(
            self.lonrange, self.latrange, self.Z,
            levels=self.config.levels,
            cmap=self.config.colormap,
            norm=self.config.norm
        )
        figure.clear()

        logger.info('converting matplotlib contour to geojson')
        geojsoncontour.contour_to_geojson(
            contour=contours,
            geojson_filepath=filepath + '.geojson',
            min_angle_deg=self.config.min_angle_between_segments,
            ndigits=4,
            unit=self.config.unit,
            stroke_width=1
        )

        world_bounding_box_filepath = 'data/world_bounding_box.geojson'
        assert os.path.exists(world_bounding_box_filepath)

        logger.info('converting geojson_to_mbtiles')
        togeojsontiles.geojson_to_mbtiles(
            filepaths=[filepath + '.geojson', world_bounding_box_filepath],
            tippecanoe_dir=TIPPECANOE_DIR,
            mbtiles_file='out.mbtiles',
            minzoom=self.zoom_min,
            maxzoom=self.zoom_max,
            full_detail=10,
            lower_detail=9,
            min_detail=7
        )

        logger.info('converting mbtiles to geojson-tiles')
        togeojsontiles.mbtiles_to_geojsontiles(
            tippecanoe_dir=TIPPECANOE_DIR,
            tile_dir=os.path.join(filepath, 'tiles/'),
            mbtiles_file='out.mbtiles',
        )
        logger.info('DONE: create contour json tiles')

    def create_image_tiles(self, filepath):
        self.create_world_file(filepath)
        logger.info(f'create image tiles for {filepath}')
        args = [
            'gdal2tiles.py',
            '-p', 'mercator',
            '--s_srs', 'EPSG:4326',
            '-z', f'{self.zoom_min}-{self.zoom_max}',
            filepath + '.png',
            os.path.join(filepath, 'maptiles')
        ]
        logger.info(args)
        output = subprocess.check_output(args)
        logger.info(output.decode('utf-8'))

    def create_world_file(self, filepath):
        logger.info(f'create world file for {filepath}')
        with Image.open(filepath + '.png') as im:
            width, height = im.size
        logger.info(f"image width {width}, image height {height}")

        with open(filepath + '.pgw', 'w') as worldfile:
            y_pixel_size = 180.0/height
            x_pixel_size = 360.0/width
            logger.info(f"y pixel size {y_pixel_size}, x pixel size {x_pixel_size}")
            worldfile.write(str(x_pixel_size) + '\n')
            worldfile.write('0.0' + '\n')
            worldfile.write('0.0' + '\n')
            worldfile.write(str(-y_pixel_size) + '\n')
            worldfile.write(str(-180+x_pixel_size/2) + '\n')
            worldfile.write(str(90-y_pixel_size/2) + '\n')
