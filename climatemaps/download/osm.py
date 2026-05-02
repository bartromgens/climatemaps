import zipfile
from pathlib import Path

from osgeo import gdal, ogr

from climatemaps.download.utils import download_file
from climatemaps.logger import logger


OSM_LAND_POLYGONS_URL = "https://osmdata.openstreetmap.de/download/land-polygons-complete-4326.zip"


class OSMLandPolygonsDownloader:
    def __init__(self, output_dir: Path | str = "data/raw/osm_land"):
        self.output_dir = Path(output_dir)
        self.shapefile_path = self.output_dir / "land_polygons.shp"

    def is_available(self) -> bool:
        return self.shapefile_path.exists()

    def download(self, force_redownload: bool = False) -> Path:
        if self.is_available() and not force_redownload:
            logger.info(f"OSM land polygons already exist at {self.shapefile_path}")
            return self.shapefile_path

        self.output_dir.mkdir(parents=True, exist_ok=True)
        zip_path = self.output_dir / "land-polygons-complete-4326.zip"

        logger.info(f"Downloading OSM land polygons from {OSM_LAND_POLYGONS_URL}")
        download_file(OSM_LAND_POLYGONS_URL, zip_path, verify=False)

        logger.info(f"Extracting OSM land polygons to {self.output_dir}")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(self.output_dir)

        zip_path.unlink()

        extracted_dir = self.output_dir / "land-polygons-complete-4326"
        if extracted_dir.exists():
            for file in extracted_dir.iterdir():
                file.rename(self.output_dir / file.name)
            extracted_dir.rmdir()

        logger.info(f"OSM land polygons extracted to {self.shapefile_path}")
        return self.shapefile_path


class OSMLandMaskCreator:
    def __init__(
        self,
        shapefile_path: Path | str,
        output_path: Path | str = "data/raw/land_mask_osm.tif",
        resolution: float = 0.008333333333333,
        bounds: tuple[float, float, float, float] = (-180, -90, 180, 90),
    ):
        self.shapefile_path = Path(shapefile_path)
        self.output_path = Path(output_path)
        self.resolution = resolution
        self.bounds = bounds

    def is_available(self) -> bool:
        return self.output_path.exists()

    def create(self, force_recreate: bool = False) -> Path:
        if self.is_available() and not force_recreate:
            logger.info(f"OSM land mask already exists at {self.output_path}")
            return self.output_path

        if not self.shapefile_path.exists():
            raise FileNotFoundError(f"Shapefile not found: {self.shapefile_path}")

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        min_lon, min_lat, max_lon, max_lat = self.bounds
        width = int((max_lon - min_lon) / self.resolution)
        height = int((max_lat - min_lat) / self.resolution)

        logger.info(f"Creating land mask: {width}x{height} pixels at {self.resolution}° resolution")

        driver = gdal.GetDriverByName("GTiff")
        out_raster = driver.Create(
            str(self.output_path),
            width,
            height,
            1,
            gdal.GDT_Byte,
            options=["COMPRESS=LZW", "TILED=YES"],
        )

        out_raster.SetGeoTransform((min_lon, self.resolution, 0, max_lat, 0, -self.resolution))

        srs = ogr.osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        out_raster.SetProjection(srs.ExportToWkt())

        band = out_raster.GetRasterBand(1)
        band.SetNoDataValue(255)
        band.Fill(0)

        logger.info("Rasterizing land polygons (this may take a while)...")
        shp_ds = ogr.Open(str(self.shapefile_path))
        layer = shp_ds.GetLayer()

        gdal.RasterizeLayer(out_raster, [1], layer, burn_values=[1])

        band.FlushCache()
        out_raster = None
        shp_ds = None

        logger.info(f"Land mask created at {self.output_path}")
        return self.output_path


def download_osm_land_polygons(
    output_dir: Path | str = "data/raw/osm_land",
    force_redownload: bool = False,
) -> Path:
    downloader = OSMLandPolygonsDownloader(output_dir)
    return downloader.download(force_redownload)


def create_land_mask_from_osm(
    shapefile_path: Path | str,
    output_path: Path | str = "data/raw/land_mask_osm.tif",
    resolution: float = 0.008333333333333,
    bounds: tuple[float, float, float, float] = (-180, -90, 180, 90),
) -> Path:
    creator = OSMLandMaskCreator(shapefile_path, output_path, resolution, bounds)
    return creator.create()


def ensure_osm_land_mask(
    output_path: Path | str = "data/raw/land_mask_osm.tif",
    resolution: float = 0.008333333333333,
    force_redownload: bool = False,
) -> Path:
    output_path = Path(output_path)

    if output_path.exists() and not force_redownload:
        logger.info(f"OSM land mask already exists at {output_path}")
        return output_path

    shapefile_path = download_osm_land_polygons(force_redownload=force_redownload)
    return create_land_mask_from_osm(shapefile_path, output_path, resolution)
