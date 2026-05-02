#!/usr/bin/env python3
import argparse
import os
import shutil
import sys

module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

from climatemaps.config import get_config
from climatemaps.datasets.difference import DIFFERENCE_DATA_SETS
from climatemaps.datasets.future import FUTURE_DATA_SETS
from climatemaps.datasets.historic import HISTORIC_DATA_SETS
from climatemaps.logger import logger


def main(dry_run: bool = True) -> None:
    maps_config = get_config()
    tiles_dir = maps_config.data_dir_out

    if not os.path.isdir(tiles_dir):
        logger.info(f"Tiles directory does not exist: {tiles_dir}")
        return

    known_slugs = {cfg.data_type_slug for cfg in HISTORIC_DATA_SETS + FUTURE_DATA_SETS + DIFFERENCE_DATA_SETS}

    existing_dirs = [
        entry.name
        for entry in os.scandir(tiles_dir)
        if entry.is_dir()
    ]

    unused = sorted(name for name in existing_dirs if name not in known_slugs)

    if not unused:
        logger.info("No unused tile directories found.")
        return

    logger.info(f"Found {len(unused)} unused tile director{'y' if len(unused) == 1 else 'ies'}:")
    for name in unused:
        logger.info(f"  {os.path.join(tiles_dir, name)}")

    if dry_run:
        logger.info("Dry run — nothing removed. Pass --execute to delete.")
        return

    for name in unused:
        path = os.path.join(tiles_dir, name)
        shutil.rmtree(path)
        logger.info(f"Removed: {path}")

    logger.info(f"Removed {len(unused)} unused tile director{'y' if len(unused) == 1 else 'ies'}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove unused tile directories from data/tiles")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete directories (default is dry run)",
    )
    args = parser.parse_args()

    main(dry_run=not args.execute)
