import logging

import numpy as np
import numpy.typing as npt
import scipy
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator
from pydantic import model_validator

logger = logging.getLogger(__name__)


class GeoGrid(BaseModel):
    lon_range: npt.NDArray[np.floating]
    lat_range: npt.NDArray[np.floating]
    values: npt.NDArray[np.floating]

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    @field_validator("lon_range")
    def lon_range_must_increase(cls, v, values):
        if not np.all(np.diff(v) > 0):
            raise ValueError("lon range must be monotonically increasing")
        return v

    @field_validator("lat_range")
    def lat_range_must_increase(cls, v, values):
        if not np.all(np.diff(v) < 0):
            raise ValueError("lat range must be monotonically decreasing")
        return v

    @model_validator(mode="after")
    def check_array_sizes(cls, model: "GeoGrid"):
        if model.values.size != model.lon_range.size * model.lat_range.size:
            raise ValueError("size of values does not match the lat and lon sizes")
        if model.values.shape[0] != model.lat_range.shape[0]:
            raise ValueError("shape of values does not match the lat size")
        if model.values.shape[1] != model.lon_range.shape[0]:
            raise ValueError("shape of values does not match the lon size")
        return model

    def clipped_values(self, lower: float, upper: float) -> npt.NDArray[np.floating]:
        return np.clip(self.values.astype(float), lower, upper)

    def zoom(self, zoom_factor: float) -> "GeoGrid":
        """
        Increase resolution of the data by using spline interpolation.
        Returns a new zoomed GeoGrid object.
        """
        values = scipy.ndimage.zoom(self.values, zoom=zoom_factor, order=1)
        lon_range = scipy.ndimage.zoom(self.lon_range, zoom=zoom_factor, order=1)
        lat_range = scipy.ndimage.zoom(self.lat_range, zoom=zoom_factor, order=1)
        return GeoGrid(lon_range=lon_range, lat_range=lat_range, values=values)

    def difference(self, other: "GeoGrid") -> "GeoGrid":
        """
        Return a new GeoGrid equal to (self.values - other.values).
        """
        if self.values.shape != other.values.shape:
            raise ValueError(
                f"Shape mismatch: self.values is {self.values.shape}, "
                f"other.values is {other.values.shape}"
            )

        diff_vals = self.values - other.values
        return GeoGrid(lon_range=self.lon_range, lat_range=self.lat_range, values=diff_vals)

    @property
    def lat_min(self):
        return self.lat_range[-1]

    @property
    def lat_max(self):
        return self.lat_range[0]

    @property
    def lon_min(self):
        return self.lon_range[0]

    @property
    def lon_max(self):
        return self.lon_range[-1]

    @property
    def bin_width(self):
        assert self.bin_width_lon == self.bin_width_lat
        return self.bin_width_lon

    @property
    def bin_width_lon(self):
        return 360.0 / len(self.lon_range)

    @property
    def bin_width_lat(self):
        return 180.0 / len(self.lat_range)

    @property
    def llcrnrlon(self):
        """lower left corner longitude"""
        return self.lon_min - self.bin_width / 2

    @property
    def llcrnrlat(self):
        """lower left corner latitude"""
        return self.lat_min - self.bin_width / 2

    @property
    def urcrnrlon(self):
        """upper right corner longitude"""
        return self.lon_max + self.bin_width / 2

    @property
    def urcrnrlat(self):
        """upper right corner latitude"""
        return self.lat_max + self.bin_width / 2

    def get_value_at_coordinate(self, lon: float, lat: float) -> float:
        if lon < self.lon_min or lon > self.lon_max:
            raise ValueError(f"Longitude {lon} is out of range [{self.lon_min}, {self.lon_max}]")
        if lat < self.lat_min or lat > self.lat_max:
            raise ValueError(f"Latitude {lat} is out of range [{self.lat_min}, {self.lat_max}]")

        from scipy.interpolate import RegularGridInterpolator

        interpolator = RegularGridInterpolator(
            (self.lat_range, self.lon_range),
            self.values,
            method="linear",
            bounds_error=False,
            fill_value=np.nan,
        )

        value = float(interpolator([lat, lon])[0])

        if np.isnan(value):
            raise ValueError(f"No data available at coordinates (lat={lat}, lon={lon})")

        return value
