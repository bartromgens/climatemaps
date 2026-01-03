#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

from climatemaps.download.osm import OSMCountryBordersDownloader
from climatemaps.logger import logger


def main(
    force_redownload: bool = False,
    force_recreate_geojson: bool = False,
    force_recreate_mbtiles: bool = False,
    simplify_tolerance: float = 0.01,
    minzoom: int = 0,
    maxzoom: int = 5,
) -> None:
    logger.info("Starting country borders tile creation")

    downloader = OSMCountryBordersDownloader()
    geojson_path = Path("data/raw/osm_countries/country_borders.geojson")
    mbtiles_path = Path("data/tiles/country_borders/country_borders.mbtiles")

    if not downloader.is_available() or force_redownload:
        logger.info("Downloading country borders shapefile")
        downloader.download(force_redownload=force_redownload)
    else:
        logger.info("Country borders shapefile already exists")

    if not geojson_path.exists() or force_recreate_geojson:
        if force_recreate_geojson and geojson_path.exists():
            logger.info(f"Deleting existing GeoJSON file: {geojson_path}")
            geojson_path.unlink()
        logger.info("Converting country borders to GeoJSON")
        geojson = downloader.to_geojson(
            output_path=geojson_path, simplify_tolerance=simplify_tolerance
        )
        logger.info(f"GeoJSON created with {len(geojson['features'])} features")
    else:
        logger.info("GeoJSON already exists, skipping conversion")

    if not mbtiles_path.exists() or force_recreate_mbtiles:
        if force_recreate_mbtiles and mbtiles_path.exists():
            logger.info(f"Deleting existing MBTiles file: {mbtiles_path}")
            mbtiles_path.unlink()
        if not geojson_path.exists():
            logger.error(f"GeoJSON file not found at {geojson_path}. Cannot create MBTiles.")
            sys.exit(1)

        logger.info("Converting GeoJSON to MBTiles")
        try:
            downloader.to_mbtiles(
                geojson_path=geojson_path,
                mbtiles_path=mbtiles_path,
                minzoom=minzoom,
                maxzoom=maxzoom,
            )
            logger.info(f"MBTiles created at {mbtiles_path}")
        except Exception as e:
            logger.error(f"Failed to create MBTiles: {e}")
            sys.exit(1)
    else:
        logger.info("MBTiles already exists, skipping conversion")

    logger.info("Country borders tile creation completed successfully")


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download country borders data and create GeoJSON and MBTiles tiles."
    )
    parser.add_argument(
        "--force-redownload",
        action="store_true",
        help="Force re-download of the shapefile even if it exists",
    )
    parser.add_argument(
        "--force-recreate-geojson",
        action="store_true",
        help="Force recreation of GeoJSON file even if it exists",
    )
    parser.add_argument(
        "--force-recreate-mbtiles",
        action="store_true",
        help="Force recreation of MBTiles file even if it exists",
    )
    parser.add_argument(
        "--simplify-tolerance",
        type=float,
        default=0.01,
        help="Simplification tolerance for GeoJSON conversion (default: 0.01)",
    )
    parser.add_argument(
        "--minzoom",
        type=int,
        default=0,
        help="Minimum zoom level for MBTiles (default: 0)",
    )
    parser.add_argument(
        "--maxzoom",
        type=int,
        default=5,
        help="Maximum zoom level for MBTiles (default: 5)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_arguments()

    main(
        force_redownload=args.force_redownload,
        force_recreate_geojson=args.force_recreate_geojson,
        force_recreate_mbtiles=args.force_recreate_mbtiles,
        simplify_tolerance=args.simplify_tolerance,
        minzoom=args.minzoom,
        maxzoom=args.maxzoom,
    )
