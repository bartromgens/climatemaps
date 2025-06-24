import json
import os
import sys
from typing import List

module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

from climatemaps.config import ClimateMap
from climatemaps.settings import settings


config = {"options": {"paths": {"root": "../website", "mbtiles": "data"}}, "data": {}}


def main(data_sets: List[ClimateMap]):
    for data_set in data_sets:
        for month in range(1, 13):
            # vector entry
            config["data"][f"{data_set.data_type}_vector_{month}"] = {
                "mbtiles": f"{data_set.data_type}/{month}_vector.mbtiles"
            }
            # raster entry
            config["data"][f"{data_set.data_type}_raster_{month}"] = {
                "mbtiles": f"{data_set.data_type}/{month}_raster.mbtiles"
            }

    # write to file
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)


if __name__ == "__main__":
    main(settings.DATA_SETS_API)
