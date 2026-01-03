from enum import Enum
from typing import NamedTuple

import numpy as np


class BoundingBox(NamedTuple):
    lon_min: float
    lat_min: float
    lon_max: float
    lat_max: float

    def contains_point(self, lon: float, lat: float) -> bool:
        return self.lon_min <= lon <= self.lon_max and self.lat_min <= lat <= self.lat_max

    def intersects(self, other: "BoundingBox") -> bool:
        return not (
            self.lon_max < other.lon_min
            or self.lon_min > other.lon_max
            or self.lat_max < other.lat_min
            or self.lat_min > other.lat_max
        )

    def intersection(self, other: "BoundingBox") -> "BoundingBox | None":
        if not self.intersects(other):
            return None
        return BoundingBox(
            lon_min=max(self.lon_min, other.lon_min),
            lat_min=max(self.lat_min, other.lat_min),
            lon_max=min(self.lon_max, other.lon_max),
            lat_max=min(self.lat_max, other.lat_max),
        )


class Region(str, Enum):
    EUROPE_AFRICA = "europe-africa"
    EUROPE = "europe"
    ALPS = "alps"
    AFRICA = "africa"
    NORTH_AMERICA = "north-america"
    SOUTH_AMERICA = "south-america"
    ASIA = "asia"
    OCEANIA = "oceania"


REGION_BBOXES = {
    Region.EUROPE_AFRICA: BoundingBox(lon_min=-25, lat_min=-35, lon_max=55, lat_max=72),
    Region.EUROPE: BoundingBox(lon_min=-25, lat_min=35, lon_max=55, lat_max=72),
    Region.ALPS: BoundingBox(lon_min=4, lat_min=43, lon_max=18, lat_max=48.5),
    Region.AFRICA: BoundingBox(lon_min=-20, lat_min=-35, lon_max=55, lat_max=40),
    Region.NORTH_AMERICA: BoundingBox(lon_min=-170, lat_min=15, lon_max=-50, lat_max=75),
    Region.SOUTH_AMERICA: BoundingBox(lon_min=-85, lat_min=-56, lon_max=-30, lat_max=15),
    Region.ASIA: BoundingBox(lon_min=25, lat_min=-10, lon_max=150, lat_max=75),
    Region.OCEANIA: BoundingBox(lon_min=110, lat_min=-50, lon_max=180, lat_max=0),
}


def get_region_bbox(region: Region) -> BoundingBox:
    return REGION_BBOXES[region]
