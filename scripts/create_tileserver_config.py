import json
import os
import sys
from typing import List


module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

from climatemaps.datasets import ClimateDataConfig
from climatemaps.settings import settings


config = {"options": {"paths": {"root": "./", "mbtiles": "tiles"}}, "data": {}}


def main(data_configs: List[ClimateDataConfig]):
    for data_config in data_configs:
        month_upper = 1 if settings.DEV_MODE else 12
        for month in range(1, month_upper + 1):
            # vector entry
            config["data"][f"{data_config.data_type_slug}_vector_{month}"] = {
                "mbtiles": f"{data_config.data_type_slug}/{month}_vector.mbtiles"
            }
            # raster entry
            config["data"][f"{data_config.data_type_slug}_raster_{month}"] = {
                "mbtiles": f"{data_config.data_type_slug}/{month}_raster.mbtiles"
            }

    # write to file
    with open("tileserver_config.json", "w") as f:
        json.dump(config, f, indent=2)


if __name__ == "__main__":
    main(settings.DATA_SETS_API)
