import numpy
from geotiff import GeoTiff


def read_geotiff_month(filepath, month):
    geo_tiff = GeoTiff(filepath)
    # print("geo_tiff shape:", geo_tiff.tif_shape)
    # print(geo_tiff.tif_bBox)
    print(geo_tiff.tif_bBox_wgs_84)
    zarr_array = geo_tiff.read()
    array = numpy.array(zarr_array)
    array = array[:, :, month]

    lon_array, lat_array = geo_tiff.get_coord_arrays(geo_tiff.tif_bBox)
    lon_array = lon_array[0, :]
    lat_array = lat_array[:, 0]
    return lon_array, lat_array, array
