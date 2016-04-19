import json
import math
import os

from mpl_toolkits.basemap import Basemap
import numpy
import matplotlib.pyplot as plt

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
    def __init__(self, level_lower=0, level_upper=100, colormap=plt.cm.jet, unit=''):  # jet, jet_r, YlOrRd, gist_rainbow
        self.n_contours = 160
        self.min_angle_between_segments = 15
        self.level_lower = level_lower
        self.level_upper = level_upper
        self.colormap = colormap
        self.unit = unit


class Contour(object):
    def __init__(self, config, lonrange, latrange, Z):
        self.config = config
        self.Z = Z
        self.lonrange = lonrange
        self.latrange = latrange[::-1]
        numpy.set_printoptions(3, threshold=100, suppress=True)  # .3f

    def create_contour_data(self, filepath):
        figure = plt.figure(figsize=(10, 10), frameon=False)
        ax = figure.add_subplot(111)
        m = Basemap(
            projection='merc',
            resolution='c',
            lon_0=360,
            ax=ax,
            llcrnrlon=-180,
            llcrnrlat=-85,
            urcrnrlon=180,
            urcrnrlat=85,
        )
        x, y = m(*numpy.meshgrid(self.lonrange, self.latrange))
        # levels = numpy.linspace(10, 90, num=self.config.n_contours)
        levels = numpy.linspace(self.config.level_lower, self.config.level_upper, num=self.config.n_contours)
        # contours = plt.contourf(lonrange, latrange, Z, levels=levels, cmap=plt.cm.plasma)
        m.contourf(x, y, self.Z, levels=levels, cmap=self.config.colormap)
        m.drawcoastlines(linewidth=0.2)  # draw coastlines
        # m.drawmapboundary()  # draw a line around the map region
        # m.drawparallels(numpy.arange(-90., 120., 30.), labels=[1, 0, 0, 0])  # draw parallels
        # m.drawmeridians(numpy.arange(0., 420., 60.), labels=[0, 0, 0, 1])  # draw meridians
        # cbar = figure.colorbar(contours, format='%.1f')
        # ax.set_xlim([0, 360e5])
        ax.set_axis_off()
        plt.savefig(filepath + '.png', dpi=700, bbox_inches='tight', pad_inches=0)
        # contours = plt.contourf(self.lonrange, self.latrange, self.Z, levels=levels, cmap=self.config.colormap)
        ndigits = 3
        # contour_to_json(contours, filepath, levels, self.config.min_angle_between_segments, ndigits, self.config.unit)


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
                    u"label": str(int(contour_labels[contour_index])) + ' ' + unit
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