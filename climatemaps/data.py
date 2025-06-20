import numpy
import math


def import_climate_data(filepath, monthnr):
    ncols = 720
    nrows = 360
    digits = 5

    with open(filepath, "r") as filein:
        lines = filein.readlines()
        line_n = 0
        grid_size = 0.50
        xmin = 0.25 - 180
        xmax = 360.25 - 180
        ymin = -89.75
        ymax = 90.25

        lonrange = numpy.arange(xmin, xmax, grid_size)
        latrange = numpy.arange(ymin, ymax, grid_size)
        Z = numpy.zeros((int(latrange.shape[0]), int(lonrange.shape[0])))
        # print(len(lonrange))
        # print(len(latrange))

        i = 0
        rown = 0

        for line in lines:
            line_n += 1
            if line_n < 3:  # skip header
                continue
            if rown < (monthnr - 1) * nrows or rown >= monthnr * nrows:  # read one month
                rown += 1
                continue

            value = ""
            counter = 1
            j = 0
            for char in line:
                value += char
                if counter % digits == 0:
                    value = float(value)
                    if value == -9999:
                        value = numpy.nan
                    Z[i][j] = value
                    value = ""
                    j += 1
                counter += 1
            i += 1
            rown += 1

        Z_new = numpy.zeros((int(latrange.shape[0]), int(lonrange.shape[0])))
        half_size = int(Z.shape[1] / 2)
        for i in range(0, Z.shape[0]):
            for j in range(0, Z.shape[1]):
                if lonrange[j] >= 0.0:
                    Z_new[i][j - half_size] = Z[i][j]
                else:
                    Z_new[i][j + half_size] = Z[i][j]

    return latrange, lonrange, Z_new


def import_ascii_grid_generic(filepath, no_data_value=9e20):
    with open(filepath, "r") as filein:
        lines = filein.readlines()
        line_n = 0
        grid_size = 0.083333333
        xmin = -180.0
        xmax = 180.0
        ymin = -90.0
        ymax = 90.0

        lonrange = numpy.arange(xmin, xmax, grid_size)
        latrange = numpy.arange(ymin, ymax, grid_size)
        Z = numpy.zeros((int(latrange.shape[0]), int(lonrange.shape[0])))

        i = 0
        for line in lines:
            line_n += 1
            if line_n < 7:  # skip header
                continue

            j = 0
            values = line.split()
            for value in values:
                value = float(value)
                if value == no_data_value:
                    value = numpy.nan
                Z[i][j] = value
                j += 1
            i += 1

    print("import_ascii_grid_generic() - END")
    return latrange, lonrange, Z


def geographic_to_web_mercator(x_lon, y_lat):
    if abs(x_lon) <= 180 and abs(y_lat) < 90:
        num = x_lon * 0.017453292519943295
        x = 6378137.0 * num
        a = y_lat * 0.017453292519943295
        x_mercator = x
        y_mercator = 3189068.5 * math.log((1.0 + math.sin(a)) / (1.0 - math.sin(a)))
        return x_mercator, y_mercator
    else:
        print("Invalid coordinate values for conversion")
