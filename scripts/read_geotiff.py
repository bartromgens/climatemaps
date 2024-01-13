import climatemaps

tiff_file = "../data/climate_models/wc2.1_10m_prec_ACCESS-CM2_ssp126_2021-2040.tif"


if __name__ == "__main__":
    lonrange, latrange, Z = climatemaps.geotiff.read_geotiff_month(tiff_file, 0)
