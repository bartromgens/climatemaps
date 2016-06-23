import math
import os
import subprocess

from PIL import Image

from mpl_toolkits.basemap import Basemap
import numpy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.colors import LogNorm, SymLogNorm
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
                 unit='',
                 logscale=False,
                 n_contours=21):  # jet, jet_r, YlOrRd, gist_rainbow
        self.n_contours = n_contours
        self.min_angle_between_segments = 5
        self.level_lower = level_lower
        self.level_upper = level_upper
        self.colormap = colormap
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
                num=self.n_contours*10,
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
                num=self.n_contours*10
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
    def __init__(self, config, lonrange, latrange, Z):
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
        numpy.set_printoptions(3, threshold=100, suppress=True)  # .3f

    def create_contour_data(self, data_dir_out, data_type, month, figure_dpi=700):
        logger.info('start')
        figure = Figure(frameon=False)
        FigureCanvas(figure)
        
        ax = figure.add_subplot(111)
        m = Basemap(
            projection='cyl',
            resolution='l',
            lon_0=0,
            ax=ax,
            llcrnrlon=-180,
            llcrnrlat=-85,
            urcrnrlon=180,
            urcrnrlat=85,
        )
        x, y = m(*numpy.meshgrid(self.lonrange, self.latrange))
        contour = m.contourf(x, y, self.Z,
                             cmap=self.config.colormap,
                             levels=self.config.levels_image,
                             norm=self.config.norm
                             )
        # m.drawcoastlines(linewidth=0.1)  # draw coastlines
        # cbar = figure.colorbar(contour, format='%.1f')
        ax.set_axis_off()
        data_dir = os.path.join(data_dir_out, data_type)
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)
        filepath = os.path.join(data_dir, str(month))
        figure.savefig(
            filepath + '.png',
            dpi=figure_dpi,
            bbox_inches='tight',
            pad_inches=0,
            transparent=True
        )

        cbar = figure.colorbar(contour, format='%.1f')
        cbar.set_label(self.config.unit)
        cbar.set_ticks(self.config.colorbar_ticks)
        ax.set_visible(False)
        figure.savefig(
            filepath + "_colorbar.svg",
            # dpi=300,
            bbox_inches='tight',
            pad_inches=0,
            transparent=True
        )

        self.create_image_tiles(filepath)
        self.create_contour_json(filepath)
        logger.info('end')

    def create_contour_json(self, filepath):
        logger.info('START: create contour json tiles')
        zoomfactor = 2.0
        self.Z = scipy.ndimage.zoom(self.Z, zoom=zoomfactor, order=1)
        self.lonrange = scipy.ndimage.zoom(self.lonrange, zoom=zoomfactor, order=1)
        self.latrange = scipy.ndimage.zoom(self.latrange, zoom=zoomfactor, order=1)

        figure = Figure(frameon=False)
        FigureCanvas(figure)
        ax = figure.add_subplot(111)
        contours = ax.contour(
            self.lonrange, self.latrange, self.Z,
            levels=self.config.levels,
            cmap=self.config.colormap,
            norm=self.config.norm
        )
        figure.clear()
        plt.cla()

        ndigits = 4
        logger.info('converting contour to geojson')
        geojsoncontour.contour_to_geojson(
            contour=contours,
            geojson_filepath=filepath + '.geojson',
            contour_levels=self.config.levels,
            min_angle_deg=self.config.min_angle_between_segments,
            ndigits=ndigits,
            unit=self.config.unit,
            stroke_width=1
        )

        world_bounding_box_filepath = 'data/world_bounding_box.geojson'
        assert os.path.exists(world_bounding_box_filepath)

        togeojsontiles.geojson_to_mbtiles(
            filepaths=[filepath + '.geojson', world_bounding_box_filepath],
            tippecanoe_dir=TIPPECANOE_DIR,
            mbtiles_file='out.mbtiles',
            maxzoom=5
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
        logger.info('create image tiles')
        args = [
            'gdal2tiles.py',
            '-p', 'mercator',
            '--s_srs', 'EPSG:4326',
            '-z', '0-5',
            filepath + '.png',
            os.path.join(filepath, 'maptiles')
        ]
        logger.info(args)
        output = subprocess.check_output(args)
        logger.info(output.decode('utf-8'))

    def create_world_file(self, filepath):
        with Image.open(filepath + '.png') as im:
            width, height = im.size

        with open(filepath + '.pgw', 'w') as worldfile:
            worldfile.write(str(360.0/width) + '\n')
            worldfile.write('0.0' + '\n')
            worldfile.write('0.0' + '\n')
            worldfile.write(str(-170.0/height) + '\n')
            worldfile.write('-180.0' + '\n')
            worldfile.write('85.0' + '\n')
