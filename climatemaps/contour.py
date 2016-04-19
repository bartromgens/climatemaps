import json
import math
import os

from mpl_toolkits.basemap import Basemap
import numpy
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, SymLogNorm

import scipy.ndimage
from scipy.ndimage.filters import gaussian_filter

from climatemaps.logger import logger


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
                 logscale=False):  # jet, jet_r, YlOrRd, gist_rainbow
        self.n_contours = 11
        self.min_angle_between_segments = 15
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
                stop=math.log(self.level_upper+1),
                num=self.n_contours,
                base=math.e
            )
            for i in range(0, len(self.levels)):
                self.levels[i] -= 1
        else:
            self.levels = numpy.linspace(
                start=self.level_lower,
                stop=self.level_upper,
                num=self.n_contours
            )

        if logscale:
            assert self.level_lower > 0
            self.levels_image = numpy.logspace(
                start=math.log(self.level_lower),
                stop=math.log(self.level_upper+2),
                num=self.n_contours*20,
                base=math.e
            )
            for i in range(0, len(self.levels_image)):
                self.levels_image[i] -= 1
        else:
            self.levels_image = numpy.linspace(
                start=self.level_lower,
                stop=self.level_upper,
                num=self.n_contours*20
            )
        print(self.levels)


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

    def create_contour_data(self, filepath):
        figure = plt.figure(figsize=(10, 10), frameon=False)
        ax = figure.add_subplot(111)
        m = Basemap(
            projection='merc',
            resolution='c',
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
        m.drawcoastlines(linewidth=0.3)  # draw coastlines
        # m.drawmapboundary()  # draw a line around the map region
        # m.drawparallels(numpy.arange(-90., 120., 30.), labels=[1, 0, 0, 0])  # draw parallels
        # m.drawmeridians(numpy.arange(0., 420., 60.), labels=[0, 0, 0, 1])  # draw meridians
        # cbar = figure.colorbar(contour, format='%.1f')
        ax.set_axis_off()
        plt.savefig(filepath + '.png', dpi=400, bbox_inches='tight', pad_inches=0, transparent=True)

        self.create_contour_json(filepath)

    def create_contour_json(self, filepath):
        # self.lonrange = gaussian_filter(self.lonrange, sigma=0.5)
        # self.latrange = gaussian_filter(self.latrange, sigma=0.5)
        # self.Z = gaussian_filter(self.Z, sigma=3.0, mode='wrap', truncate=10.0)
        zoomfactor = 2.0
        self.Z = scipy.ndimage.zoom(self.Z, zoom=zoomfactor, order=1)
        self.lonrange = scipy.ndimage.zoom(self.lonrange, zoom=zoomfactor, order=1)
        self.latrange = scipy.ndimage.zoom(self.latrange, zoom=zoomfactor, order=1)
        figure = plt.figure()
        ax = figure.add_subplot(222)

        for i in range(0, len(self.config.levels)):
            self.config.levels[i] -= 0.7

        contours = ax.contour(
            self.lonrange, self.latrange, self.Z,
            levels=self.config.levels,
            cmap=self.config.colormap,
            norm=self.config.norm
        )
        # cbar = figure.colorbar(contours, format='%.1f')
        ndigits = 3
        contour_to_json(contours, filepath, self.config.levels, self.config.min_angle_between_segments, ndigits, self.config.unit)


def contour_to_json(contour, filename, contour_labels, min_angle=2, ndigits=5, unit=''):
    # min_angle: only create a new line segment if the angle is larger than this angle, to compress output
    collections = contour.collections
    with open(filename + '.json', 'w') as fileout:
        total_points = 0
        total_points_original = 0
        collections_json = []
        contour_index = 0
        assert len(contour_labels) == len(collections)
        for collection in collections:
            paths = collection.get_paths()
            color = collection.get_edgecolor()
            paths_json = []
            for path in paths:
                v = path.vertices
                if len(v) < 2:
                    continue
                x = []
                y = []
                v1 = v[1] - v[0]
                x.append(round(v[0][0], ndigits))
                y.append(round(v[0][1], ndigits))
                for i in range(1, len(v) - 2):
                    v2 = v[i + 1] - v[i - 1]
                    diff_angle = math.fabs(angle(v1, v2) * 180.0 / math.pi)
                    # print(diff_angle)
                    if diff_angle > min_angle:
                        x.append(round(v[i][0], ndigits))
                        y.append(round(v[i][1], ndigits))
                        v1 = v[i] - v[i - 1]
                x.append(round(v[-1][0], ndigits))
                y.append(round(v[-1][1], ndigits))
                total_points += len(x)
                total_points_original += len(v)

                # x = v[:,0].tolist()
                # y = v[:,1].tolist()
                paths_json.append({
                    u"x": x,
                    u"y": y,
                    u"linecolor": color[0].tolist(),
                    u"label": ('% 12.1f' % contour_labels[contour_index]) + ' ' + unit
                })
            contour_index += 1

            if paths_json:
                collections_json.append({u"paths": paths_json})
        collections_json_f = {}
        collections_json_f[u"contours"] = collections_json
        fileout.write(json.dumps(collections_json_f, sort_keys=True))  # indent=2)
        if total_points_original > 0:
            logger.info('total points: ' + str(total_points) + ', compression: ' + str(int((1.0 - total_points / total_points_original) * 100)) + '%')
        else:
            logger.warning('no points found')