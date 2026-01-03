import json
import os
import zipfile
from pathlib import Path

from osgeo import gdal, ogr
import togeojsontiles

from climatemaps.download.utils import download_file
from climatemaps.logger import logger
from climatemaps.settings import settings


OSM_LAND_POLYGONS_URL = "https://osmdata.openstreetmap.de/download/land-polygons-complete-4326.zip"
NATURAL_EARTH_COUNTRIES_URL = (
    "https://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_0_countries.zip"
)


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


class OSMCountryBordersDownloader:
    def __init__(self, output_dir: Path | str = "data/raw/osm_countries"):
        self.output_dir = Path(output_dir)
        self.shapefile_path = self.output_dir / "ne_50m_admin_0_countries.shp"

    def is_available(self) -> bool:
        return self.shapefile_path.exists()

    def download(self, force_redownload: bool = False) -> Path:
        if self.is_available() and not force_redownload:
            logger.info(f"Country borders already exist at {self.shapefile_path}")
            return self.shapefile_path

        self.output_dir.mkdir(parents=True, exist_ok=True)
        zip_path = self.output_dir / "ne_50m_admin_0_countries.zip"

        logger.info(f"Downloading country borders from {NATURAL_EARTH_COUNTRIES_URL}")
        download_file(NATURAL_EARTH_COUNTRIES_URL, zip_path, verify=False)

        logger.info(f"Extracting country borders to {self.output_dir}")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(self.output_dir)

        zip_path.unlink()

        extracted_dir = self.output_dir / "ne_50m_admin_0_countries"
        if extracted_dir.exists():
            for file in extracted_dir.iterdir():
                file.rename(self.output_dir / file.name)
            extracted_dir.rmdir()

        logger.info(f"Country borders extracted to {self.shapefile_path}")
        return self.shapefile_path

    def to_geojson(
        self, output_path: Path | str | None = None, simplify_tolerance: float = 0.01
    ) -> dict:
        if not self.is_available():
            raise FileNotFoundError(f"Shapefile not found: {self.shapefile_path}")

        if output_path:
            output_path = Path(output_path)
            if output_path.exists():
                with open(output_path, "r") as f:
                    return json.load(f)

        logger.info(
            f"Converting country borders to GeoJSON (simplify tolerance: {simplify_tolerance})"
        )

        driver = ogr.GetDriverByName("ESRI Shapefile")
        data_source = driver.Open(str(self.shapefile_path), 0)

        if data_source is None:
            raise RuntimeError(f"Could not open shapefile: {self.shapefile_path}")

        layer = data_source.GetLayer()

        geojson = {"type": "FeatureCollection", "features": []}

        feature_count = layer.GetFeatureCount()
        logger.info(f"Processing {feature_count} country features")

        for i, feature in enumerate(layer):
            if i % 100 == 0 and i > 0:
                logger.info(f"Processed {i}/{feature_count} features")

            geometry = feature.GetGeometryRef()
            if geometry is None:
                continue

            geometry_type = geometry.GetGeometryType()
            properties = {}
            for j in range(feature.GetFieldCount()):
                field_name = feature.GetFieldDefnRef(j).GetName()
                field_value = feature.GetField(j)
                if field_value:
                    properties[field_name] = field_value

            if geometry_type == ogr.wkbMultiPolygon or geometry_type == ogr.wkbMultiPolygon25D:
                logger.debug(f"Converting MultiPolygon with {geometry.GetGeometryCount()} polygons")
                for j in range(geometry.GetGeometryCount()):
                    polygon = geometry.GetGeometryRef(j)
                    if polygon is None:
                        continue
                    if simplify_tolerance > 0:
                        polygon = polygon.Simplify(simplify_tolerance)
                    geom_json = json.loads(polygon.ExportToJson())
                    if geom_json.get("type") == "Polygon":
                        geojson["features"].append(
                            {"type": "Feature", "geometry": geom_json, "properties": properties}
                        )
            else:
                if simplify_tolerance > 0:
                    geometry = geometry.Simplify(simplify_tolerance)
                geom_json = json.loads(geometry.ExportToJson())
                geom_type = geom_json.get("type")
                if geom_type in ["Polygon", "LineString", "Point"]:
                    geojson["features"].append(
                        {"type": "Feature", "geometry": geom_json, "properties": properties}
                    )
                else:
                    logger.warning(f"Skipping unsupported geometry type: {geom_type}")

        data_source = None

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(geojson, f)
            logger.info(f"GeoJSON saved to {output_path}")

        logger.info(f"Converted {len(geojson['features'])} country features to GeoJSON")
        return geojson

    def to_mbtiles(
        self,
        geojson_path: Path | str,
        mbtiles_path: Path | str,
        minzoom: int = 0,
        maxzoom: int = 5,
    ) -> Path:
        if not self.is_available():
            raise FileNotFoundError(f"Shapefile not found: {self.shapefile_path}")

        geojson_path = Path(geojson_path)
        mbtiles_path = Path(mbtiles_path)
        mbtiles_temp_path = Path(f"{mbtiles_path}.tmp")

        if mbtiles_path.exists():
            logger.info(f"MBTiles already exists at {mbtiles_path}")
            return mbtiles_path

        if not geojson_path.exists():
            raise FileNotFoundError(f"GeoJSON file not found: {geojson_path}")

        logger.info(f"Converting country borders GeoJSON to MBTiles: {mbtiles_path}")

        mbtiles_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            togeojsontiles.geojson_to_mbtiles(
                filepaths=[str(geojson_path)],
                tippecanoe_dir=settings.TIPPECANOE_DIR,
                mbtiles_file=str(mbtiles_temp_path),
                minzoom=minzoom,
                maxzoom=maxzoom,
                full_detail=12,
                lower_detail=8,
                min_detail=7,
                extra_args=[
                    "--layer",
                    "countries",
                    "--no-feature-limit",
                    "--no-tile-size-limit",
                    "--force",
                ],
            )

            logger.info(f"Atomically moving {mbtiles_temp_path} to {mbtiles_path}")
            os.replace(mbtiles_temp_path, mbtiles_path)
            logger.info(f"Country borders MBTiles created at {mbtiles_path}")
            return mbtiles_path
        except Exception as e:
            logger.error(f"Failed to create country borders MBTiles: {e}")
            if mbtiles_temp_path.exists():
                logger.info(f"Removing incomplete temp file: {mbtiles_temp_path}")
                os.remove(mbtiles_temp_path)
            raise
