import json
import os
import sys
from typing import List


module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

from climatemaps.config import ClimateMapsConfig
from climatemaps.config import get_config
from climatemaps.datasets import ClimateDataConfig
from climatemaps.settings import settings
from climatemaps.tile import tile_files_exist
from climatemaps.logger import logger

maps_config: ClimateMapsConfig = get_config()


def main(data_configs: List[ClimateDataConfig]):
    config = _create_config(data_configs, dev_mode=False)
    config_dev = _create_config(data_configs, dev_mode=True)
    filename = "tileserver_config.json"
    filename_dev = "tileserver_config_dev.json"

    # write to file
    with open(filename, "w") as f:
        json.dump(config, f, indent=2)
    with open(filename_dev, "w") as f:
        json.dump(config_dev, f, indent=2)

    logger.info(
        f"Tileserver config created for production and dev mode: {filename} ({len(config['data'])} configs) and {filename_dev} ({len(config_dev['data'])} configs)"
    )


def _create_config(data_configs, dev_mode: bool = False):
    logger.info(
        f"Creating tileserver config for {len(data_configs)} data configs. Dev mode: {dev_mode}"
    )
    config = {"options": {"paths": {"root": "./", "mbtiles": "data/tiles"}}, "data": {}}
    for data_config in data_configs:
        month_upper = 12
        for month in range(1, month_upper + 1):
            if dev_mode and not tile_files_exist(data_config, month, maps_config):
                logger.warning(
                    f"Tiles for {data_config.data_type_slug} {month} does not exist. Excluded from config (dev_mode={dev_mode})."
                )
                continue
            # vector entry
            config["data"][f"{data_config.data_type_slug}_vector_{month}"] = {
                "mbtiles": f"{data_config.data_type_slug}/{month}_vector.mbtiles"
            }
            # raster entry
            config["data"][f"{data_config.data_type_slug}_raster_{month}"] = {
                "mbtiles": f"{data_config.data_type_slug}/{month}_raster.mbtiles"
            }
            logger.info(f"Added {data_config.data_type_slug} {month} to config")
    return config


if __name__ == "__main__":
    main(settings.DATA_SETS_API)
