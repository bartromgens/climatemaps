import os

from climatemaps.config import ClimateMapsConfig
from climatemaps.datasets import ClimateDataConfig


def tile_files_exist(
    data_set_config: ClimateDataConfig, month: int, maps_config: ClimateMapsConfig
) -> bool:
    files_to_check = [
        f"{month}_raster.mbtiles",
        f"{month}_vector.mbtiles",
        f"{month}_colorbar.png",
    ]

    directory = os.path.join(maps_config.data_dir_out, data_set_config.data_type_slug)
    return _check_files_exist(directory, files_to_check)


def _check_files_exist(directory, filenames):
    if not os.path.isdir(directory):
        return False

    for filename in filenames:
        full_path = os.path.join(directory, filename)
        exists = os.path.isfile(full_path)
        if not exists:
            return False

    return True
