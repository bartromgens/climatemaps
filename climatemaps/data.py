import numpy


def import_climate_data(filepath, monthnr, factor_to_SI=1):
    ncols = 720
    nrows = 360
    digits = 5

    with open(filepath, 'r') as filein:
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
        rown = 0

        for line in lines:
            line_n += 1
            if line_n < 3:  # skip header
                continue
            if rown < (monthnr-1)*nrows or rown >= monthnr*nrows:  # read one month
                rown += 1
                continue

            value = ''
            counter = 1
            j = 0
            for char in line:
                value += char
                if counter % digits == 0:
                    value = float(value)
                    if value == -9999:
                        value = numpy.nan
                    Z[i][j] = value*factor_to_SI
                    value = ''
                    j += 1
                counter += 1
            i += 1
            rown += 1

    return latrange, lonrange, Z