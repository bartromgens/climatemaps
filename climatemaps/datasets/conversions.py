import calendar

import numpy as np
import numpy.typing as npt


def chelsa_temperature_conversion(
    values: npt.NDArray[np.floating], month: int
) -> npt.NDArray[np.floating]:
    """
    Convert CHELSA temperature data from tenths of Kelvin to Celsius.

    CHELSA temperature data is stored in tenths of Kelvin, so we need to:
    1. Convert from tenths of Kelvin to Kelvin (already done by conversion_factor=0.1)
    2. Convert from Kelvin to Celsius (subtract 273.15)
    """
    return values - 273.15


def convert_per_month_to_per_day(
    v: npt.NDArray[np.floating], month: int
) -> npt.NDArray[np.floating]:
    days_in_month = calendar.monthrange(2025, month)[1]
    return v / days_in_month
