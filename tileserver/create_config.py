import json
import sys
from typing import List

sys.path.append('../climatemaps')

from climatemaps.config import ClimateMap
from climatemaps.settings import DATA_SETS_API


config = {
    "options": {
        "paths": {
            "root": "../website",
            "mbtiles": "data"
        }
    },
    "data": {}
}


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
    main(DATA_SETS_API)
