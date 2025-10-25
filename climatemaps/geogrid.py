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
    def lon_range_must_increase(cls, v: npt.NDArray[np.floating]) -> npt.NDArray[np.floating]:
        if not np.all(np.diff(v) > 0):
            raise ValueError("lon range must be monotonically increasing")
        return v

    @field_validator("lat_range")
    def lat_range_must_increase(cls, v: npt.NDArray[np.floating]) -> npt.NDArray[np.floating]:
        if not np.all(np.diff(v) < 0):
            raise ValueError("lat range must be monotonically decreasing")
        return v

    @model_validator(mode="after")
    def check_array_sizes(self) -> "GeoGrid":
        if self.values.size != self.lon_range.size * self.lat_range.size:
            raise ValueError("size of values does not match the lat and lon sizes")
        if self.values.shape[0] != self.lat_range.shape[0]:
            raise ValueError("shape of values does not match the lat size")
        if self.values.shape[1] != self.lon_range.shape[0]:
            raise ValueError("shape of values does not match the lon size")
        return self

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

    def downsample(self, factor: int = 2) -> "GeoGrid":
        """
        Reduce the resolution of the grid by the specified factor.
        For example, factor=2 will halve the resolution in both dimensions.
        """
        if factor < 1:
            raise ValueError("Downsampling factor must be >= 1")

        if factor == 1:
            return self

        logger.info(f"Downsampling geogrid from {self.resolution_mega_pixel:.1f} megapixels")

        # Calculate new dimensions
        new_lat_size = max(1, self.lat_range.size // factor)
        new_lon_size = max(1, self.lon_range.size // factor)

        # Create new coordinate arrays
        new_lat_range = np.linspace(self.lat_max, self.lat_min, new_lat_size)
        new_lon_range = np.linspace(self.lon_min, self.lon_max, new_lon_size)

        # Downsample values using scipy's zoom function
        zoom_factors = (new_lat_size / self.lat_range.size, new_lon_size / self.lon_range.size)
        new_values = scipy.ndimage.zoom(self.values, zoom=zoom_factors, order=1)

        new_geogrid = GeoGrid(lon_range=new_lon_range, lat_range=new_lat_range, values=new_values)
        logger.info(f"Downsampled geogrid to {new_geogrid.resolution_mega_pixel:.1f} megapixels")

        return new_geogrid

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
    def bin_width_lon(self):
        return 360.0 / len(self.lon_range)

    @property
    def bin_width_lat(self):
        return 180.0 / len(self.lat_range)

    @property
    def llcrnrlon(self):
        """lower left corner longitude"""
        return self.lon_min - self.bin_width_lon / 2

    @property
    def llcrnrlat(self):
        """lower left corner latitude"""
        return self.lat_min - self.bin_width_lat / 2

    @property
    def urcrnrlon(self):
        """upper right corner longitude"""
        return self.lon_max + self.bin_width_lon / 2

    @property
    def urcrnrlat(self):
        """upper right corner latitude"""
        return self.lat_max + self.bin_width_lat / 2

    @property
    def resolution_mega_pixel(self) -> float:
        """Total number of pixels in the grid, expressed in megapixels (millions of pixels)"""
        total_pixels = self.values.size
        return total_pixels / 1_000_000

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
