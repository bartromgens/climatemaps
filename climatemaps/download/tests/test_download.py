import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from climatemaps.datasets import (
    ClimateVarKey,
    SpatialResolution,
    ClimateModel,
    ClimateScenario,
    ClimateDataConfig,
    FutureClimateDataConfig,
    DataFormat,
)
from climatemaps.download.worldclim import (
    WorldClimHistoricalDownloader,
    WorldClimFutureDownloader,
)
from climatemaps.download.cru_ts import CRUTSDownloader
from climatemaps.download.chelsa import CHELSADownloader
from climatemaps.download.osm import OSMLandPolygonsDownloader, OSMLandMaskCreator
from climatemaps.download import get_downloader, ensure_data_available, DOWNLOADER_REGISTRY
from climatemaps.geotiff import (
    read_geotiff_history,
    read_geotiff_future,
    read_geotiff_cru_ts,
    read_geotiff_chelsa,
)


def test_historical_url_generation() -> None:
    config = ClimateDataConfig(
        variable_type=ClimateVarKey.T_MIN,
        resolution_input=SpatialResolution.MIN10,
        year_range=(1970, 2000),
        format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
        filepath="test/path",
        reader_function=read_geotiff_history,
    )
    downloader = WorldClimHistoricalDownloader(config)
    url = downloader._get_url()
    assert url == "https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_10m_tmin.zip"

    config = ClimateDataConfig(
        variable_type=ClimateVarKey.T_MAX,
        resolution_input=SpatialResolution.MIN5,
        year_range=(1970, 2000),
        format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
        filepath="test/path",
        reader_function=read_geotiff_history,
    )
    downloader = WorldClimHistoricalDownloader(config)
    url = downloader._get_url()
    assert url == "https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_5m_tmax.zip"

    config = ClimateDataConfig(
        variable_type=ClimateVarKey.PRECIPITATION,
        resolution_input=SpatialResolution.MIN2_5,
        year_range=(1970, 2000),
        format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
        filepath="test/path",
        reader_function=read_geotiff_history,
    )
    downloader = WorldClimHistoricalDownloader(config)
    url = downloader._get_url()
    assert url == "https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_2.5m_prec.zip"


def test_future_url_generation() -> None:
    config = FutureClimateDataConfig(
        variable_type=ClimateVarKey.T_MIN,
        resolution_input=SpatialResolution.MIN10,
        year_range=(2021, 2040),
        climate_model=ClimateModel.EC_EARTH3_VEG,
        climate_scenario=ClimateScenario.SSP126,
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        filepath="test/path.tif",
        reader_function=read_geotiff_future,
    )
    downloader = WorldClimFutureDownloader(config)
    url = downloader._get_url()
    assert (
        url
        == "https://geodata.ucdavis.edu/cmip6/10m/EC-Earth3-Veg/ssp126/wc2.1_10m_tmin_EC-Earth3-Veg_ssp126_2021-2040.tif"
    )

    config = FutureClimateDataConfig(
        variable_type=ClimateVarKey.T_MAX,
        resolution_input=SpatialResolution.MIN5,
        year_range=(2081, 2100),
        climate_model=ClimateModel.ACCESS_CM2,
        climate_scenario=ClimateScenario.SSP585,
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        filepath="test/path.tif",
        reader_function=read_geotiff_future,
    )
    downloader = WorldClimFutureDownloader(config)
    url = downloader._get_url()
    assert (
        url
        == "https://geodata.ucdavis.edu/cmip6/5m/ACCESS-CM2/ssp585/wc2.1_5m_tmax_ACCESS-CM2_ssp585_2081-2100.tif"
    )


def test_unsupported_variable_raises_error() -> None:
    config = ClimateDataConfig(
        variable_type=ClimateVarKey.CLOUD_COVER,
        resolution_input=SpatialResolution.MIN10,
        year_range=(1970, 2000),
        format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
        filepath="test/path",
        reader_function=read_geotiff_history,
    )
    downloader = WorldClimHistoricalDownloader(config)
    with pytest.raises(ValueError):
        downloader._get_url()


def test_unsupported_future_variable_raises_error() -> None:
    config = FutureClimateDataConfig(
        variable_type=ClimateVarKey.WET_DAYS,
        resolution_input=SpatialResolution.MIN10,
        year_range=(2021, 2040),
        climate_model=ClimateModel.EC_EARTH3_VEG,
        climate_scenario=ClimateScenario.SSP126,
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        filepath="test/path.tif",
        reader_function=read_geotiff_future,
    )
    downloader = WorldClimFutureDownloader(config)
    with pytest.raises(ValueError):
        downloader._get_url()


def test_ipcc_url_generation() -> None:
    config = ClimateDataConfig(
        variable_type=ClimateVarKey.CLOUD_COVER,
        resolution_input=SpatialResolution.MIN10,
        year_range=(1961, 1990),
        format=DataFormat.CRU_TS,
        filepath="test/path",
        reader_function=read_geotiff_cru_ts,
    )
    downloader = CRUTSDownloader(config)
    url = downloader._get_url()
    assert (
        url
        == "https://dap.ceda.ac.uk/badc/ipcc-ddc/data/obs/cru_ts2_1/clim_30/cld/cru_cld_clim_1961-1990.zip"
    )

    config = ClimateDataConfig(
        variable_type=ClimateVarKey.DIURNAL_TEMP_RANGE,
        resolution_input=SpatialResolution.MIN10,
        year_range=(1961, 1990),
        format=DataFormat.CRU_TS,
        filepath="test/path",
        reader_function=read_geotiff_cru_ts,
    )
    downloader = CRUTSDownloader(config)
    url = downloader._get_url()
    assert (
        url
        == "https://dap.ceda.ac.uk/badc/ipcc-ddc/data/obs/cru_ts2_1/clim_30/dtr/cru_dtr_clim_1961-1990.zip"
    )

    config = ClimateDataConfig(
        variable_type=ClimateVarKey.WET_DAYS,
        resolution_input=SpatialResolution.MIN10,
        year_range=(1961, 1990),
        format=DataFormat.CRU_TS,
        filepath="test/path",
        reader_function=read_geotiff_cru_ts,
    )
    downloader = CRUTSDownloader(config)
    url = downloader._get_url()
    assert (
        url
        == "https://dap.ceda.ac.uk/badc/ipcc-ddc/data/obs/cru_ts2_1/clim_30/wet/cru_wet_clim_1961-1990.zip"
    )

    config = ClimateDataConfig(
        variable_type=ClimateVarKey.FROST_DAYS,
        resolution_input=SpatialResolution.MIN10,
        year_range=(1961, 1990),
        format=DataFormat.CRU_TS,
        filepath="test/path",
        reader_function=read_geotiff_cru_ts,
    )
    downloader = CRUTSDownloader(config)
    url = downloader._get_url()
    assert (
        url
        == "https://dap.ceda.ac.uk/badc/ipcc-ddc/data/obs/cru_ts2_1/clim_30/frs/cru_frs_clim_1961-1990.zip"
    )

    config = ClimateDataConfig(
        variable_type=ClimateVarKey.VAPOUR_PRESSURE,
        resolution_input=SpatialResolution.MIN10,
        year_range=(1961, 1990),
        format=DataFormat.CRU_TS,
        filepath="test/path",
        reader_function=read_geotiff_cru_ts,
    )
    downloader = CRUTSDownloader(config)
    url = downloader._get_url()
    assert (
        url
        == "https://dap.ceda.ac.uk/badc/ipcc-ddc/data/obs/cru_ts2_1/clim_30/vap/cru_vap_clim_1961-1990.zip"
    )

    config = ClimateDataConfig(
        variable_type=ClimateVarKey.T_MAX,
        resolution_input=SpatialResolution.MIN10,
        year_range=(1961, 1990),
        format=DataFormat.CRU_TS,
        filepath="test/path",
        reader_function=read_geotiff_cru_ts,
    )
    downloader = CRUTSDownloader(config)
    url = downloader._get_url()
    assert (
        url
        == "https://dap.ceda.ac.uk/badc/ipcc-ddc/data/obs/cru_ts2_1/clim_30/tmx/cru_tmx_clim_1961-1990.zip"
    )

    config = ClimateDataConfig(
        variable_type=ClimateVarKey.T_MIN,
        resolution_input=SpatialResolution.MIN10,
        year_range=(1961, 1990),
        format=DataFormat.CRU_TS,
        filepath="test/path",
        reader_function=read_geotiff_cru_ts,
    )
    downloader = CRUTSDownloader(config)
    url = downloader._get_url()
    assert (
        url
        == "https://dap.ceda.ac.uk/badc/ipcc-ddc/data/obs/cru_ts2_1/clim_30/tmn/cru_tmn_clim_1961-1990.zip"
    )

    config = ClimateDataConfig(
        variable_type=ClimateVarKey.PRECIPITATION,
        resolution_input=SpatialResolution.MIN10,
        year_range=(1961, 1990),
        format=DataFormat.CRU_TS,
        filepath="test/path",
        reader_function=read_geotiff_cru_ts,
    )
    downloader = CRUTSDownloader(config)
    url = downloader._get_url()
    assert (
        url
        == "https://dap.ceda.ac.uk/badc/ipcc-ddc/data/obs/cru_ts2_1/clim_30/pre/cru_pre_clim_1961-1990.zip"
    )


def test_ipcc_url_different_year_ranges() -> None:
    config = ClimateDataConfig(
        variable_type=ClimateVarKey.CLOUD_COVER,
        resolution_input=SpatialResolution.MIN10,
        year_range=(1901, 1930),
        format=DataFormat.CRU_TS,
        filepath="test/path",
        reader_function=read_geotiff_cru_ts,
    )
    downloader = CRUTSDownloader(config)
    url = downloader._get_url()
    assert (
        url
        == "https://dap.ceda.ac.uk/badc/ipcc-ddc/data/obs/cru_ts2_1/clim_30/cld/cru_cld_clim_1901-1930.zip"
    )

    config = ClimateDataConfig(
        variable_type=ClimateVarKey.DIURNAL_TEMP_RANGE,
        resolution_input=SpatialResolution.MIN10,
        year_range=(1931, 1960),
        format=DataFormat.CRU_TS,
        filepath="test/path",
        reader_function=read_geotiff_cru_ts,
    )
    downloader = CRUTSDownloader(config)
    url = downloader._get_url()
    assert (
        url
        == "https://dap.ceda.ac.uk/badc/ipcc-ddc/data/obs/cru_ts2_1/clim_30/dtr/cru_dtr_clim_1931-1960.zip"
    )


def test_chelsa_url_generation() -> None:
    config = ClimateDataConfig(
        variable_type=ClimateVarKey.T_MIN,
        resolution_input=SpatialResolution.MIN0_5,
        year_range=(1981, 2010),
        format=DataFormat.CHELSA,
        filepath="test/path",
        reader_function=read_geotiff_chelsa,
    )
    downloader = CHELSADownloader(config)

    url_jan = downloader._get_url(1)
    assert (
        url_jan
        == "https://os.unil.cloud.switch.ch/chelsa02/chelsa/global/climatologies/tasmin/1981-2010/CHELSA_tasmin_01_1981-2010_V.2.1.tif"
    )

    url_dec = downloader._get_url(12)
    assert (
        url_dec
        == "https://os.unil.cloud.switch.ch/chelsa02/chelsa/global/climatologies/tasmin/1981-2010/CHELSA_tasmin_12_1981-2010_V.2.1.tif"
    )


def test_chelsa_url_different_variables() -> None:
    config = ClimateDataConfig(
        variable_type=ClimateVarKey.PRECIPITATION,
        resolution_input=SpatialResolution.MIN0_5,
        year_range=(1981, 2010),
        format=DataFormat.CHELSA,
        filepath="test/path",
        reader_function=read_geotiff_chelsa,
    )
    downloader = CHELSADownloader(config)
    url = downloader._get_url(6)
    assert (
        url
        == "https://os.unil.cloud.switch.ch/chelsa02/chelsa/global/climatologies/pr/1981-2010/CHELSA_pr_06_1981-2010_V.2.1.tif"
    )

    config = ClimateDataConfig(
        variable_type=ClimateVarKey.T_MAX,
        resolution_input=SpatialResolution.MIN0_5,
        year_range=(1981, 2010),
        format=DataFormat.CHELSA,
        filepath="test/path",
        reader_function=read_geotiff_chelsa,
    )
    downloader = CHELSADownloader(config)
    url = downloader._get_url(3)
    assert (
        url
        == "https://os.unil.cloud.switch.ch/chelsa02/chelsa/global/climatologies/tasmax/1981-2010/CHELSA_tasmax_03_1981-2010_V.2.1.tif"
    )


def test_chelsa_month_filepath() -> None:
    config = ClimateDataConfig(
        variable_type=ClimateVarKey.T_MIN,
        resolution_input=SpatialResolution.MIN0_5,
        year_range=(1981, 2010),
        format=DataFormat.CHELSA,
        filepath="test/chelsa_data",
        reader_function=read_geotiff_chelsa,
    )
    downloader = CHELSADownloader(config)

    filepath_jan = downloader._get_month_filepath(1)
    assert filepath_jan == Path("test/chelsa_data/CHELSA_tasmin_1981-2010_01.tif")

    filepath_dec = downloader._get_month_filepath(12)
    assert filepath_dec == Path("test/chelsa_data/CHELSA_tasmin_1981-2010_12.tif")


def test_chelsa_unsupported_variable() -> None:
    with pytest.raises(ValueError, match="Unsupported CHELSA variable"):
        config = ClimateDataConfig(
            variable_type=ClimateVarKey.WET_DAYS,
            resolution_input=SpatialResolution.MIN0_5,
            year_range=(1981, 2010),
            format=DataFormat.CHELSA,
            filepath="test/path",
            reader_function=read_geotiff_chelsa,
        )
        CHELSADownloader(config)


def test_cru_ts_unsupported_variable() -> None:
    with pytest.raises(ValueError, match="Unsupported CRU-TS variable"):
        config = ClimateDataConfig(
            variable_type=ClimateVarKey.RADIATION,
            resolution_input=SpatialResolution.MIN30,
            year_range=(1961, 1990),
            format=DataFormat.CRU_TS,
            filepath="test/path",
            reader_function=read_geotiff_cru_ts,
        )
        CRUTSDownloader(config)


def test_osm_land_polygons_downloader() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        downloader = OSMLandPolygonsDownloader(tmpdir)

        assert not downloader.is_available()
        assert downloader.shapefile_path == Path(tmpdir) / "land_polygons.shp"


def test_osm_land_mask_creator() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        shapefile_path = Path(tmpdir) / "test.shp"
        output_path = Path(tmpdir) / "mask.tif"

        creator = OSMLandMaskCreator(
            shapefile_path=shapefile_path,
            output_path=output_path,
            resolution=0.1,
            bounds=(-10, -10, 10, 10),
        )

        assert not creator.is_available()
        assert creator.output_path == output_path


def test_registry_contains_all_formats() -> None:
    assert DataFormat.GEOTIFF_WORLDCLIM_HISTORY in DOWNLOADER_REGISTRY
    assert DataFormat.GEOTIFF_WORLDCLIM_CMIP6 in DOWNLOADER_REGISTRY
    assert DataFormat.CRU_TS in DOWNLOADER_REGISTRY
    assert DataFormat.CHELSA in DOWNLOADER_REGISTRY


def test_get_downloader_worldclim_historical() -> None:
    config = ClimateDataConfig(
        variable_type=ClimateVarKey.T_MIN,
        resolution_input=SpatialResolution.MIN10,
        year_range=(1970, 2000),
        format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
        filepath="test/path",
        reader_function=read_geotiff_history,
    )
    downloader = get_downloader(config)
    assert isinstance(downloader, WorldClimHistoricalDownloader)


def test_get_downloader_worldclim_future() -> None:
    config = FutureClimateDataConfig(
        variable_type=ClimateVarKey.T_MIN,
        resolution_input=SpatialResolution.MIN10,
        year_range=(2021, 2040),
        climate_model=ClimateModel.EC_EARTH3_VEG,
        climate_scenario=ClimateScenario.SSP126,
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        filepath="test/path.tif",
        reader_function=read_geotiff_future,
    )
    downloader = get_downloader(config)
    assert isinstance(downloader, WorldClimFutureDownloader)


def test_get_downloader_cru_ts() -> None:
    config = ClimateDataConfig(
        variable_type=ClimateVarKey.CLOUD_COVER,
        resolution_input=SpatialResolution.MIN30,
        year_range=(1961, 1990),
        format=DataFormat.CRU_TS,
        filepath="test/path",
        reader_function=read_geotiff_cru_ts,
    )
    downloader = get_downloader(config)
    assert isinstance(downloader, CRUTSDownloader)


def test_get_downloader_chelsa() -> None:
    config = ClimateDataConfig(
        variable_type=ClimateVarKey.T_MIN,
        resolution_input=SpatialResolution.MIN0_5,
        year_range=(1981, 2010),
        format=DataFormat.CHELSA,
        filepath="test/path",
        reader_function=read_geotiff_chelsa,
    )
    downloader = get_downloader(config)
    assert isinstance(downloader, CHELSADownloader)


def test_get_downloader_unsupported_format() -> None:
    from unittest.mock import Mock

    config = Mock()
    config.format = Mock()
    config.format.name = "UNSUPPORTED_FORMAT"

    with pytest.raises(ValueError, match="No downloader registered for format"):
        get_downloader(config)


def test_downloader_is_available_false_when_file_missing() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        config = FutureClimateDataConfig(
            variable_type=ClimateVarKey.T_MIN,
            resolution_input=SpatialResolution.MIN10,
            year_range=(2021, 2040),
            climate_model=ClimateModel.EC_EARTH3_VEG,
            climate_scenario=ClimateScenario.SSP126,
            format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
            filepath=f"{tmpdir}/nonexistent.tif",
            reader_function=read_geotiff_future,
        )
        downloader = WorldClimFutureDownloader(config)
        assert not downloader.is_available()


def test_downloader_is_available_true_when_file_exists() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.tif"
        test_file.touch()

        config = FutureClimateDataConfig(
            variable_type=ClimateVarKey.T_MIN,
            resolution_input=SpatialResolution.MIN10,
            year_range=(2021, 2040),
            climate_model=ClimateModel.EC_EARTH3_VEG,
            climate_scenario=ClimateScenario.SSP126,
            format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
            filepath=str(test_file),
            reader_function=read_geotiff_future,
        )
        downloader = WorldClimFutureDownloader(config)
        assert downloader.is_available()


def test_worldclim_historical_data_type_extraction() -> None:
    config = ClimateDataConfig(
        variable_type=ClimateVarKey.PRECIPITATION,
        resolution_input=SpatialResolution.MIN10,
        year_range=(1970, 2000),
        format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
        filepath="data/raw/worldclim/history/wc2.1_10m_prec",
        reader_function=read_geotiff_history,
    )
    downloader = WorldClimHistoricalDownloader(config)
    assert downloader.data_type == "wc2.1_10m_prec"


def test_cru_ts_file_pattern() -> None:
    config = ClimateDataConfig(
        variable_type=ClimateVarKey.CLOUD_COVER,
        resolution_input=SpatialResolution.MIN30,
        year_range=(1961, 1990),
        format=DataFormat.CRU_TS,
        filepath="test/path",
        reader_function=read_geotiff_cru_ts,
    )
    downloader = CRUTSDownloader(config)
    assert downloader.file_pattern == "cru_cld_clim_1961-1990_{:02d}.tif"
    assert downloader.abbr == "cld"
    assert downloader.year_str == "1961-1990"


def test_future_downloader_multiple_scenarios() -> None:
    scenarios = [ClimateScenario.SSP126, ClimateScenario.SSP245, ClimateScenario.SSP585]
    for scenario in scenarios:
        config = FutureClimateDataConfig(
            variable_type=ClimateVarKey.T_MIN,
            resolution_input=SpatialResolution.MIN10,
            year_range=(2021, 2040),
            climate_model=ClimateModel.EC_EARTH3_VEG,
            climate_scenario=scenario,
            format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
            filepath="test/path.tif",
            reader_function=read_geotiff_future,
        )
        downloader = WorldClimFutureDownloader(config)
        url = downloader._get_url()
        assert scenario.name.lower() in url


def test_future_downloader_multiple_time_periods() -> None:
    time_periods = [(2021, 2040), (2041, 2060), (2061, 2080), (2081, 2100)]
    for year_range in time_periods:
        config = FutureClimateDataConfig(
            variable_type=ClimateVarKey.T_MIN,
            resolution_input=SpatialResolution.MIN10,
            year_range=year_range,
            climate_model=ClimateModel.EC_EARTH3_VEG,
            climate_scenario=ClimateScenario.SSP126,
            format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
            filepath="test/path.tif",
            reader_function=read_geotiff_future,
        )
        downloader = WorldClimFutureDownloader(config)
        url = downloader._get_url()
        assert f"{year_range[0]}-{year_range[1]}" in url


def test_chelsa_is_available_checks_all_months() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ClimateDataConfig(
            variable_type=ClimateVarKey.T_MIN,
            resolution_input=SpatialResolution.MIN0_5,
            year_range=(1981, 2010),
            format=DataFormat.CHELSA,
            filepath=tmpdir,
            reader_function=read_geotiff_chelsa,
        )
        downloader = CHELSADownloader(config)

        month_01 = downloader._get_month_filepath(1)
        month_01.parent.mkdir(parents=True, exist_ok=True)
        month_01.touch()

        assert downloader.is_available(month_upper=1), "Month 1 exists, should return True"
        assert not downloader.is_available(
            month_upper=2
        ), "Month 2 missing, should return False even though month 1 exists"
        assert not downloader.is_available(month_upper=6), "Months 2-6 missing, should return False"
        assert not downloader.is_available(
            month_upper=12
        ), "Months 2-12 missing, should return False"

        for month in range(2, 7):
            month_file = downloader._get_month_filepath(month)
            month_file.touch()

        assert downloader.is_available(month_upper=6), "Months 1-6 exist, should return True"
        assert not downloader.is_available(
            month_upper=7
        ), "Month 7 missing, should return False even though 1-6 exist"
        assert not downloader.is_available(
            month_upper=12
        ), "Months 7-12 missing, should return False"


def test_worldclim_historical_is_available_checks_all_months() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ClimateDataConfig(
            variable_type=ClimateVarKey.T_MIN,
            resolution_input=SpatialResolution.MIN10,
            year_range=(1970, 2000),
            format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
            filepath=f"{tmpdir}/wc2.1_10m_tmin",
            reader_function=read_geotiff_history,
        )
        downloader = WorldClimHistoricalDownloader(config)

        downloader.data_dir.mkdir(parents=True, exist_ok=True)
        month_01 = downloader._get_month_filepath(1)
        month_01.touch()

        assert downloader.is_available(month_upper=1)
        assert not downloader.is_available(month_upper=2)
        assert not downloader.is_available(month_upper=12)

        for month in range(2, 4):
            month_file = downloader._get_month_filepath(month)
            month_file.touch()

        assert downloader.is_available(month_upper=3)
        assert not downloader.is_available(month_upper=4)


def test_cru_ts_is_available_checks_all_months() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ClimateDataConfig(
            variable_type=ClimateVarKey.CLOUD_COVER,
            resolution_input=SpatialResolution.MIN30,
            year_range=(1961, 1990),
            format=DataFormat.CRU_TS,
            filepath=tmpdir,
            reader_function=read_geotiff_cru_ts,
        )
        downloader = CRUTSDownloader(config)

        downloader.data_dir.mkdir(parents=True, exist_ok=True)
        month_01 = downloader._get_month_filepath(1)
        month_01.touch()

        assert downloader.is_available(month_upper=1)
        assert not downloader.is_available(month_upper=2)
        assert not downloader.is_available(month_upper=12)


def test_chelsa_verify_checks_all_months() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ClimateDataConfig(
            variable_type=ClimateVarKey.T_MIN,
            resolution_input=SpatialResolution.MIN0_5,
            year_range=(1981, 2010),
            format=DataFormat.CHELSA,
            filepath=tmpdir,
            reader_function=read_geotiff_chelsa,
        )
        downloader = CHELSADownloader(config)

        downloader.base_dir.mkdir(parents=True, exist_ok=True)

        month_01 = downloader._get_month_filepath(1)
        month_01.touch()

        with patch("climatemaps.download.base.verify_geotiff_file") as mock_verify:
            mock_verify.return_value = True

            assert downloader.verify(month_upper=1)
            assert not downloader.verify(month_upper=2)

            for month in range(2, 4):
                month_file = downloader._get_month_filepath(month)
                month_file.touch()

            assert downloader.verify(month_upper=3)
            assert not downloader.verify(month_upper=4)


def test_ensure_data_available_downloads_when_partial_months_exist() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ClimateDataConfig(
            variable_type=ClimateVarKey.T_MIN,
            resolution_input=SpatialResolution.MIN0_5,
            year_range=(1981, 2010),
            format=DataFormat.CHELSA,
            filepath=tmpdir,
            reader_function=read_geotiff_chelsa,
        )

        downloader = CHELSADownloader(config)
        downloader.base_dir.mkdir(parents=True, exist_ok=True)

        for month in range(1, 4):
            month_file = downloader._get_month_filepath(month)
            month_file.touch()

        assert downloader.is_available(month_upper=3)
        assert not downloader.is_available(month_upper=6)

        with patch.object(downloader, "_do_download") as mock_download:
            downloader.ensure_available(month_upper=3, skip_verification=True)
            mock_download.assert_not_called()

            downloader.ensure_available(month_upper=6, skip_verification=True)
            mock_download.assert_called_once_with(skip_verification=True, month_upper=6)


def test_chelsa_do_download_skips_existing_valid_files() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ClimateDataConfig(
            variable_type=ClimateVarKey.T_MIN,
            resolution_input=SpatialResolution.MIN0_5,
            year_range=(1981, 2010),
            format=DataFormat.CHELSA,
            filepath=tmpdir,
            reader_function=read_geotiff_chelsa,
        )

        downloader = CHELSADownloader(config)
        downloader.base_dir.mkdir(parents=True, exist_ok=True)

        month_01 = downloader._get_month_filepath(1)
        month_01.touch()
        month_02 = downloader._get_month_filepath(2)
        month_02.touch()

        with patch("climatemaps.geotiff.verify_geotiff_file") as mock_verify:
            mock_verify.return_value = True

            with patch("climatemaps.download.chelsa.download_file") as mock_download_file:
                downloader._do_download(skip_verification=False, month_upper=3)

                assert mock_download_file.call_count == 1

                called_destination = mock_download_file.call_args[0][1]
                assert called_destination == downloader._get_month_filepath(3)
