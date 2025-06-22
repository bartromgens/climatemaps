from climatemaps.datasets import HISTORIC_DATA_SETS

DEV_MODE = False

TILE_SERVER_URL = "http://localhost:8080/data"
ZOOM_MAX_RASTER = 4

DATA_SETS_API = HISTORIC_DATA_SETS

TIPPECANOE_DIR = "/usr/local/bin/"

# Attempt to import local overrides
try:
    from .settings_local import *  # noqa
except ImportError:
    import warnings

    warnings.warn("No local_settings.py found. Using base settings only.")
