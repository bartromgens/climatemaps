import pytest

from climatemaps.datasets import (
    ClimateVarKey,
    SpatialResolution,
    ClimateModel,
    ClimateScenario,
)
from climatemaps.download import (
    _get_worldclim_historical_url,
    _get_worldclim_future_url,
    _get_ipcc_url,
)


def test_historical_url_generation() -> None:
    url = _get_worldclim_historical_url(SpatialResolution.MIN10, ClimateVarKey.T_MIN)
    assert url == "https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_10m_tmin.zip"

    url = _get_worldclim_historical_url(SpatialResolution.MIN5, ClimateVarKey.T_MAX)
    assert url == "https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_5m_tmax.zip"

    url = _get_worldclim_historical_url(SpatialResolution.MIN2_5, ClimateVarKey.PRECIPITATION)
    assert url == "https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_2.5m_prec.zip"


def test_future_url_generation() -> None:
    url = _get_worldclim_future_url(
        SpatialResolution.MIN10,
        ClimateVarKey.T_MIN,
        ClimateModel.EC_EARTH3_VEG,
        ClimateScenario.SSP126,
        (2021, 2040),
    )
    assert (
        url
        == "https://geodata.ucdavis.edu/cmip6/10m/EC-Earth3-Veg/ssp126/wc2.1_10m_tmin_EC-Earth3-Veg_ssp126_2021-2040.tif"
    )

    url = _get_worldclim_future_url(
        SpatialResolution.MIN5,
        ClimateVarKey.T_MAX,
        ClimateModel.ACCESS_CM2,
        ClimateScenario.SSP585,
        (2081, 2100),
    )
    assert (
        url
        == "https://geodata.ucdavis.edu/cmip6/5m/ACCESS-CM2/ssp585/wc2.1_5m_tmax_ACCESS-CM2_ssp585_2081-2100.tif"
    )


def test_unsupported_variable_raises_error() -> None:
    with pytest.raises(ValueError):
        _get_worldclim_historical_url(SpatialResolution.MIN10, ClimateVarKey.CLOUD_COVER)


def test_unsupported_future_variable_raises_error() -> None:
    with pytest.raises(ValueError):
        _get_worldclim_future_url(
            SpatialResolution.MIN10,
            ClimateVarKey.WET_DAYS,
            ClimateModel.EC_EARTH3_VEG,
            ClimateScenario.SSP126,
            (2021, 2040),
        )


def test_ipcc_url_generation() -> None:
    url = _get_ipcc_url(ClimateVarKey.CLOUD_COVER, (1961, 1990))
    assert url == "https://www.ipcc-data.org/download_data/obs/ccld6190.zip"

    url = _get_ipcc_url(ClimateVarKey.DIURNAL_TEMP_RANGE, (1961, 1990))
    assert url == "https://www.ipcc-data.org/download_data/obs/cdtr6190.zip"

    url = _get_ipcc_url(ClimateVarKey.WET_DAYS, (1961, 1990))
    assert url == "https://www.ipcc-data.org/download_data/obs/cwet6190.zip"

    url = _get_ipcc_url(ClimateVarKey.WIND_SPEED, (1961, 1990))
    assert url == "https://www.ipcc-data.org/download_data/obs/cwnd6190.zip"

    url = _get_ipcc_url(ClimateVarKey.RADIATION, (1961, 1990))
    assert url == "https://www.ipcc-data.org/download_data/obs/crad6190.zip"

    url = _get_ipcc_url(ClimateVarKey.VAPOUR_PRESSURE, (1961, 1990))
    assert url == "https://www.ipcc-data.org/download_data/obs/cvap6190.zip"

    url = _get_ipcc_url(ClimateVarKey.T_MAX, (1961, 1990))
    assert url == "https://www.ipcc-data.org/download_data/obs/ctmx6190.zip"

    url = _get_ipcc_url(ClimateVarKey.T_MIN, (1961, 1990))
    assert url == "https://www.ipcc-data.org/download_data/obs/ctmn6190.zip"

    url = _get_ipcc_url(ClimateVarKey.PRECIPITATION, (1961, 1990))
    assert url == "https://www.ipcc-data.org/download_data/obs/cpre6190.zip"


def test_ipcc_url_different_year_ranges() -> None:
    url = _get_ipcc_url(ClimateVarKey.CLOUD_COVER, (1901, 1930))
    assert url == "https://www.ipcc-data.org/download_data/obs/ccld0130.zip"

    url = _get_ipcc_url(ClimateVarKey.DIURNAL_TEMP_RANGE, (1931, 1960))
    assert url == "https://www.ipcc-data.org/download_data/obs/cdtr3160.zip"
