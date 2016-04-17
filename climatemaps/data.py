import numpy


def import_climate_data():
    ncols = 720
    nrows = 360
    digits = 5

    with open('./data/cloud/ccld6190.dat') as filein:
        lines = filein.readlines()
        line_n = 0
        grid_size = 0.50
        xmin = 0.25
        xmax = 360.25
        ymin = -89.75
        ymax = 90.25

        lonrange = numpy.arange(xmin, xmax, grid_size)
        latrange = numpy.arange(ymin, ymax, grid_size)
        Z = numpy.zeros((int(latrange.shape[0]), int(lonrange.shape[0])))
        print(len(lonrange))
        print(len(latrange))

        i = 0

        for line in lines:
            line_n += 1
            if line_n < 3:  # skip header
                continue
            if i >= nrows:  # read one month
                break
            value = ''
            values = []
            counter = 1
            j = 0
            for char in line:
                value += char
                if counter % digits == 0:
                    Z[i][j] = float(value)
                    values.append(value)
                    value = ''
                    j += 1
                counter += 1
            i += 1

    return latrange, lonrange, Z