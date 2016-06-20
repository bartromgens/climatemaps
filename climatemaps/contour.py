import json
import math
import os

from mpl_toolkits.basemap import Basemap
import numpy
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, SymLogNorm, rgb2hex

import scipy.ndimage
from scipy.ndimage.filters import gaussian_filter
from geojson import Feature, LineString, FeatureCollection
import geojson

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

    def create_contour_data(self, data_dir_out, data_type, month):
        logger.info('start')
        figure = plt.figure(frameon=False)
        ax = figure.add_subplot(111)
        m = Basemap(
            projection='merc',
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
            dpi=700,
            bbox_inches='tight',
            pad_inches=0,
            transparent=True
        )

        cbar = figure.colorbar(contour, format='%.1f')
        cbar.set_label(self.config.unit)
        cbar.set_ticks(self.config.levels)
        ax.set_visible(False)
        figure.savefig(
            filepath + "_colorbar.svg",
            # dpi=300,
            bbox_inches='tight',
            pad_inches=0,
            transparent=True
        )

        self.create_contour_json(filepath)
        logger.info('end')

    def create_contour_json(self, filepath):
        logger.info('create contour plot')
        # self.lonrange = gaussian_filter(self.lonrange, sigma=0.5)
        # self.latrange = gaussian_filter(self.latrange, sigma=0.5)
        # self.Z = gaussian_filter(self.Z, sigma=3.0, mode='wrap', truncate=10.0)
        zoomfactor = 2.0
        self.Z = scipy.ndimage.zoom(self.Z, zoom=zoomfactor, order=1)
        self.lonrange = scipy.ndimage.zoom(self.lonrange, zoom=zoomfactor, order=1)
        self.latrange = scipy.ndimage.zoom(self.latrange, zoom=zoomfactor, order=1)

        figure = plt.figure()
        ax = figure.add_subplot(111)

        # for i in range(0, len(self.config.levels)):
        #     self.config.levels[i] -= 0.7

        contours = ax.contour(
            self.lonrange, self.latrange, self.Z,
            levels=self.config.levels,
            cmap=self.config.colormap,
            norm=self.config.norm
        )

        cbar = figure.colorbar(contours, ax=ax, format='%.1f')
        cbar.set_label(self.config.unit)
        ax.set_visible(False)
        figure.savefig(
            filepath + "_colorbar2.svg",
            # dpi=300,
            bbox_inches='tight',
            pad_inches=0,
            transparent=True
        )

        ndigits = 4
        logger.info('converting contour to geojson')
        geojsoncontour.contour_to_geojson(
            contours,
            filepath + '.geojson',
            self.config.levels,
            self.config.min_angle_between_segments,
            ndigits,
            self.config.unit
        )

        togeojsontiles.geojson_to_mbtiles(
            filepaths=[filepath + '.geojson',],
            tippecanoe_dir=TIPPECANOE_DIR,
            mbtiles_file='out.mbtiles',
            maxzoom=4
        )

        togeojsontiles.mbtiles_to_geojsontiles(
            tippecanoe_dir=TIPPECANOE_DIR,
            tile_dir=os.path.join(filepath, 'tiles/'),
            mbtiles_file='out.mbtiles',
        )
