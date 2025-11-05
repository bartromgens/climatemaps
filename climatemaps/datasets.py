import calendar
import enum
from dataclasses import dataclass, field
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import numpy as np
import numpy.typing as npt
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from pydantic import BaseModel

from climatemaps.contour_config import ContourPlotConfig


class DataFormat(enum.Enum):
    GEOTIFF_WORLDCLIM_CMIP6 = "GEOTIFF_WORLDCLIM_CMIP6"
    GEOTIFF_WORLDCLIM_HISTORY = "GEOTIFF_WORLDCLIM_HISTORY"
    CRU_TS = "CRU_TS"  # Climatic Research Unit (CRU) Time-Series (TS)


class SpatialResolution(enum.Enum):
    MIN30 = "30m"
    MIN10 = "10m"
    MIN5 = "5m"
    MIN2_5 = "2.5m"


class ClimateVarKey(enum.Enum):
    PRECIPITATION = "PRECIPITATION"
    T_MAX = "T_MAX"
    T_MIN = "T_MIN"
    CLOUD_COVER = "CLOUD_COVER"
    WET_DAYS = "WET_DAYS"
    FROST_DAYS = "FROST_DAYS"
    WIND_SPEED = "WIND_SPEED"
    RADIATION = "RADIATION"
    DIURNAL_TEMP_RANGE = "DIURNAL_TEMP_RANGE"
    VAPOUR_PRESSURE = "VAPOUR_PRESSURE"


class ClimateScenario(enum.Enum):
    """
    Shared Socioeconomic Pathways (SSP) + expected level of radiative forcing in the year 2100
    """

    SSP126 = "SSP126"
    SSP245 = "SSP245"
    SSP370 = "SSP370"
    SSP585 = "SSP585"


class ClimateModel(enum.Enum):
    """
    Climate models used for future climate predictions
    """

    ENSEMBLE_MEAN = "ENSEMBLE_MEAN"
    ACCESS_CM2 = "ACCESS_CM2"
    BCC_CSM2_MR = "BCC_CSM2_MR"
    CMCC_ESM2 = "CMCC_ESM2"
    EC_EARTH3_VEG = "EC_Earth3_Veg"
    FIO_ESM_2_0 = "FIO_ESM_2_0"
    GFDL_ESM4 = "GFDL_ESM4"
    GISS_E2_1_G = "GISS_E2_1_G"
    HADGEM3_GC31_LL = "HadGEM3_GC31_LL"
    INM_CM5_0 = "INM_CM5_0"
    IPSL_CM6A_LR = "IPSL_CM6A_LR"
    MIROC6 = "MIROC6"
    MPI_ESM1_2_HR = "MPI_ESM1_2_HR"
    MRI_ESM2_0 = "MRI_ESM2_0"
    UKESM1_0_LL = "UKESM1_0_LL"

    @property
    def filename(self) -> str:
        return self.value.replace("_", "-")


class ClimateVariable(BaseModel):
    name: str
    display_name: str
    unit: str
    filename: str


CLIMATE_VARIABLES: Dict[ClimateVarKey, ClimateVariable] = {
    ClimateVarKey.PRECIPITATION: ClimateVariable(
        name="Precipitation", display_name="Precipitation", unit="mm/month", filename="prec"
    ),
    ClimateVarKey.T_MAX: ClimateVariable(
        name="Tmax", display_name="Temperature (Day)", unit="°C", filename="tmax"
    ),
    ClimateVarKey.T_MIN: ClimateVariable(
        name="Tmin", display_name="Temperature (Night)", unit="°C", filename="tmin"
    ),
    ClimateVarKey.CLOUD_COVER: ClimateVariable(
        name="CloudCover", display_name="Cloud Cover", unit="%", filename="cloud"
    ),
    ClimateVarKey.WET_DAYS: ClimateVariable(
        name="WetDays", display_name="Wet Days", unit="days", filename="wetdays"
    ),
    ClimateVarKey.FROST_DAYS: ClimateVariable(
        name="FrostDays", display_name="Frost Days", unit="days", filename="frostdays"
    ),
    ClimateVarKey.RADIATION: ClimateVariable(
        name="Radiation", display_name="Radiation", unit="W/m^2", filename="radiation"
    ),
    ClimateVarKey.DIURNAL_TEMP_RANGE: ClimateVariable(
        name="DiurnalTempRange",
        display_name="Diurnal Temperature Range",
        unit="°C",
        filename="diurnaltemprange",
    ),
    ClimateVarKey.VAPOUR_PRESSURE: ClimateVariable(
        name="VapourPressure", display_name="Vapour Pressure", unit="hPa", filename="vapourpressure"
    ),
}


def create_precipitation_colormap() -> LinearSegmentedColormap:
    """
    Create a custom precipitation colormap from the provided CSS gradient colors.
    The gradient goes from dark red through red, yellow, cyan, blue to white.
    """
    color_stops = [
        (0.0, (103, 0, 0)),
        (0.00245098, (107, 0, 0)),
        (0.00490196, (111, 0, 0)),
        (0.00735294, (114, 0, 0)),
        (0.00980392, (118, 0, 0)),
        (0.0122549, (122, 0, 0)),
        (0.0147059, (126, 0, 0)),
        (0.0171569, (130, 0, 0)),
        (0.0196078, (133, 0, 0)),
        (0.0220588, (137, 0, 0)),
        (0.0245098, (141, 0, 0)),
        (0.0269608, (145, 0, 0)),
        (0.0294118, (149, 0, 0)),
        (0.0318627, (152, 0, 0)),
        (0.0343137, (156, 0, 0)),
        (0.0367647, (160, 0, 0)),
        (0.0392157, (164, 0, 0)),
        (0.0416667, (168, 0, 0)),
        (0.0441176, (171, 0, 0)),
        (0.0465686, (175, 0, 0)),
        (0.0490196, (179, 0, 0)),
        (0.0514706, (183, 0, 0)),
        (0.0539216, (187, 0, 0)),
        (0.0563725, (190, 0, 0)),
        (0.0588235, (194, 0, 0)),
        (0.0612745, (198, 0, 0)),
        (0.0637255, (202, 0, 0)),
        (0.0661765, (206, 0, 0)),
        (0.0686275, (209, 0, 0)),
        (0.0710784, (213, 0, 0)),
        (0.0735294, (217, 0, 0)),
        (0.0759804, (221, 0, 0)),
        (0.0784314, (225, 0, 0)),
        (0.0808824, (228, 0, 0)),
        (0.0833333, (232, 0, 0)),
        (0.0857843, (236, 0, 0)),
        (0.0882353, (240, 0, 0)),
        (0.0906863, (244, 0, 0)),
        (0.0931373, (247, 0, 0)),
        (0.0955882, (251, 0, 0)),
        (0.0980392, (255, 0, 0)),
        (0.10049, (255, 6, 0)),
        (0.102941, (255, 11, 0)),
        (0.105392, (255, 17, 0)),
        (0.107843, (255, 23, 0)),
        (0.110294, (255, 28, 0)),
        (0.112745, (255, 34, 0)),
        (0.115196, (255, 40, 0)),
        (0.117647, (255, 45, 0)),
        (0.120098, (255, 51, 0)),
        (0.122549, (255, 57, 0)),
        (0.125, (255, 62, 0)),
        (0.127451, (255, 68, 0)),
        (0.129902, (255, 74, 0)),
        (0.132353, (255, 79, 0)),
        (0.134804, (255, 85, 0)),
        (0.137255, (255, 91, 0)),
        (0.139706, (255, 96, 0)),
        (0.142157, (255, 102, 0)),
        (0.144608, (255, 108, 0)),
        (0.147059, (255, 113, 0)),
        (0.14951, (255, 125, 0)),
        (0.151961, (255, 136, 0)),
        (0.154412, (255, 147, 0)),
        (0.156863, (255, 159, 0)),
        (0.159314, (255, 170, 0)),
        (0.161765, (255, 176, 0)),
        (0.164216, (255, 181, 0)),
        (0.166667, (255, 187, 0)),
        (0.169118, (255, 193, 0)),
        (0.171569, (255, 198, 0)),
        (0.17402, (255, 204, 0)),
        (0.176471, (255, 210, 0)),
        (0.178922, (255, 215, 0)),
        (0.181373, (255, 221, 0)),
        (0.183824, (255, 227, 0)),
        (0.186275, (255, 232, 0)),
        (0.188725, (255, 238, 0)),
        (0.191176, (255, 244, 0)),
        (0.193627, (255, 249, 0)),
        (0.196078, (255, 255, 0)),
        (0.198529, (246, 254, 0)),
        (0.20098, (237, 253, 0)),
        (0.203431, (228, 252, 0)),
        (0.205882, (219, 251, 0)),
        (0.208333, (210, 250, 0)),
        (0.210784, (201, 249, 0)),
        (0.213235, (192, 249, 0)),
        (0.215686, (183, 248, 0)),
        (0.218137, (174, 247, 0)),
        (0.220588, (165, 246, 0)),
        (0.223039, (156, 245, 0)),
        (0.22549, (147, 244, 0)),
        (0.227941, (139, 243, 0)),
        (0.230392, (130, 242, 0)),
        (0.232843, (121, 241, 0)),
        (0.235294, (112, 240, 0)),
        (0.237745, (103, 239, 0)),
        (0.240196, (94, 238, 0)),
        (0.242647, (85, 238, 0)),
        (0.245098, (76, 237, 0)),
        (0.247549, (67, 236, 0)),
        (0.25, (58, 235, 0)),
        (0.252451, (49, 234, 0)),
        (0.254902, (40, 233, 0)),
        (0.257353, (31, 232, 0)),
        (0.259804, (31, 228, 1)),
        (0.262255, (30, 224, 2)),
        (0.264706, (30, 220, 3)),
        (0.267157, (29, 217, 4)),
        (0.269608, (29, 213, 4)),
        (0.272059, (28, 209, 5)),
        (0.27451, (28, 205, 6)),
        (0.276961, (27, 201, 7)),
        (0.279412, (27, 197, 8)),
        (0.281863, (27, 194, 9)),
        (0.284314, (26, 190, 10)),
        (0.286765, (26, 186, 11)),
        (0.289216, (25, 182, 11)),
        (0.291667, (25, 178, 12)),
        (0.294118, (24, 174, 13)),
        (0.296569, (24, 171, 14)),
        (0.29902, (24, 167, 15)),
        (0.301471, (23, 163, 16)),
        (0.303922, (23, 159, 17)),
        (0.306373, (22, 155, 18)),
        (0.308824, (22, 151, 18)),
        (0.311275, (21, 148, 19)),
        (0.313725, (21, 144, 20)),
        (0.316176, (20, 140, 21)),
        (0.318627, (20, 136, 22)),
        (0.321078, (19, 141, 31)),
        (0.323529, (18, 146, 41)),
        (0.32598, (18, 150, 50)),
        (0.328431, (17, 155, 59)),
        (0.330882, (16, 160, 69)),
        (0.333333, (15, 165, 78)),
        (0.335784, (14, 169, 87)),
        (0.338235, (14, 174, 97)),
        (0.340686, (13, 179, 106)),
        (0.343137, (12, 184, 115)),
        (0.345588, (11, 188, 125)),
        (0.348039, (10, 193, 134)),
        (0.35049, (10, 198, 143)),
        (0.352941, (9, 203, 152)),
        (0.355392, (8, 207, 162)),
        (0.357843, (7, 212, 171)),
        (0.360294, (6, 217, 180)),
        (0.362745, (6, 222, 190)),
        (0.365196, (5, 226, 199)),
        (0.367647, (4, 231, 208)),
        (0.370098, (3, 236, 218)),
        (0.372549, (2, 241, 227)),
        (0.375, (2, 245, 236)),
        (0.377451, (1, 250, 246)),
        (0.379902, (0, 255, 255)),
        (0.382353, (0, 252, 255)),
        (0.384804, (0, 249, 255)),
        (0.387255, (0, 246, 255)),
        (0.389706, (0, 243, 255)),
        (0.392157, (0, 240, 255)),
        (0.394608, (0, 237, 255)),
        (0.397059, (0, 234, 255)),
        (0.39951, (0, 231, 255)),
        (0.401961, (0, 228, 255)),
        (0.404412, (0, 225, 255)),
        (0.406863, (0, 222, 255)),
        (0.409314, (0, 219, 255)),
        (0.411765, (0, 215, 255)),
        (0.414216, (0, 212, 255)),
        (0.416667, (0, 209, 255)),
        (0.419118, (0, 206, 255)),
        (0.421569, (0, 203, 255)),
        (0.42402, (0, 200, 255)),
        (0.426471, (0, 197, 255)),
        (0.428922, (0, 194, 255)),
        (0.431373, (0, 191, 255)),
        (0.433824, (0, 188, 255)),
        (0.436275, (0, 185, 255)),
        (0.438725, (0, 182, 255)),
        (0.441176, (0, 179, 255)),
        (0.443627, (0, 176, 255)),
        (0.446078, (0, 173, 255)),
        (0.448529, (0, 171, 255)),
        (0.45098, (0, 168, 255)),
        (0.453431, (0, 165, 255)),
        (0.455882, (0, 162, 255)),
        (0.458333, (0, 160, 255)),
        (0.460784, (0, 157, 255)),
        (0.463235, (0, 154, 255)),
        (0.465686, (0, 151, 255)),
        (0.468137, (0, 149, 255)),
        (0.470588, (0, 146, 255)),
        (0.473039, (0, 143, 255)),
        (0.47549, (0, 140, 255)),
        (0.477941, (0, 138, 255)),
        (0.480392, (0, 135, 255)),
        (0.482843, (0, 132, 255)),
        (0.485294, (0, 129, 255)),
        (0.487745, (0, 127, 255)),
        (0.490196, (0, 124, 255)),
        (0.492647, (0, 121, 255)),
        (0.495098, (0, 118, 255)),
        (0.497549, (0, 116, 255)),
        (0.5, (0, 113, 255)),
        (0.502451, (0, 110, 255)),
        (0.504902, (0, 106, 255)),
        (0.507353, (0, 101, 255)),
        (0.509804, (0, 97, 255)),
        (0.512255, (0, 92, 255)),
        (0.514706, (0, 88, 255)),
        (0.517157, (0, 84, 255)),
        (0.519608, (0, 79, 255)),
        (0.522059, (0, 75, 255)),
        (0.52451, (0, 70, 255)),
        (0.526961, (0, 66, 255)),
        (0.529412, (0, 62, 255)),
        (0.531863, (0, 57, 255)),
        (0.534314, (0, 53, 255)),
        (0.536765, (0, 48, 255)),
        (0.539216, (0, 44, 255)),
        (0.541667, (0, 40, 255)),
        (0.544118, (0, 35, 255)),
        (0.546569, (0, 31, 255)),
        (0.54902, (0, 26, 255)),
        (0.551471, (0, 22, 255)),
        (0.553922, (0, 18, 255)),
        (0.556373, (0, 13, 255)),
        (0.558824, (0, 9, 255)),
        (0.561275, (0, 4, 255)),
        (0.563725, (0, 0, 255)),
        (0.566176, (5, 0, 251)),
        (0.568627, (10, 1, 247)),
        (0.571078, (15, 1, 243)),
        (0.573529, (20, 2, 239)),
        (0.57598, (25, 2, 236)),
        (0.578431, (30, 3, 232)),
        (0.580882, (35, 3, 228)),
        (0.583333, (40, 4, 224)),
        (0.585784, (45, 4, 220)),
        (0.588235, (50, 5, 216)),
        (0.590686, (55, 5, 212)),
        (0.593137, (60, 6, 208)),
        (0.595588, (64, 6, 205)),
        (0.598039, (69, 7, 201)),
        (0.60049, (74, 7, 197)),
        (0.602941, (79, 8, 193)),
        (0.605392, (84, 8, 189)),
        (0.607843, (89, 9, 185)),
        (0.610294, (94, 9, 181)),
        (0.612745, (99, 10, 177)),
        (0.615196, (104, 10, 174)),
        (0.617647, (109, 11, 170)),
        (0.620098, (114, 11, 166)),
        (0.622549, (119, 12, 162)),
        (0.625, (124, 12, 158)),
        (0.627451, (127, 12, 160)),
        (0.629902, (129, 12, 162)),
        (0.632353, (132, 11, 164)),
        (0.634804, (134, 11, 166)),
        (0.637255, (137, 11, 168)),
        (0.639706, (140, 11, 170)),
        (0.642157, (142, 10, 172)),
        (0.644608, (145, 10, 174)),
        (0.647059, (148, 10, 175)),
        (0.64951, (150, 10, 177)),
        (0.651961, (153, 9, 179)),
        (0.654412, (155, 9, 181)),
        (0.656863, (158, 9, 183)),
        (0.659314, (161, 9, 185)),
        (0.661765, (163, 8, 187)),
        (0.664216, (166, 8, 189)),
        (0.666667, (169, 8, 191)),
        (0.669118, (171, 8, 193)),
        (0.671569, (174, 7, 195)),
        (0.67402, (176, 7, 197)),
        (0.676471, (179, 7, 199)),
        (0.678922, (182, 7, 201)),
        (0.681373, (184, 6, 203)),
        (0.683824, (187, 6, 205)),
        (0.686275, (190, 6, 206)),
        (0.688725, (196, 5, 211)),
        (0.691176, (203, 5, 216)),
        (0.693627, (209, 4, 221)),
        (0.696078, (216, 4, 226)),
        (0.698529, (222, 3, 231)),
        (0.70098, (229, 2, 236)),
        (0.703431, (235, 2, 240)),
        (0.705882, (242, 1, 245)),
        (0.708333, (248, 1, 250)),
        (0.710784, (255, 0, 255)),
        (0.713235, (255, 2, 255)),
        (0.715686, (255, 3, 255)),
        (0.718137, (255, 5, 255)),
        (0.720588, (255, 6, 255)),
        (0.723039, (255, 8, 255)),
        (0.72549, (255, 9, 255)),
        (0.727941, (255, 11, 255)),
        (0.730392, (255, 12, 255)),
        (0.732843, (255, 14, 255)),
        (0.735294, (255, 15, 255)),
        (0.737745, (255, 19, 254)),
        (0.740196, (255, 22, 254)),
        (0.742647, (255, 25, 254)),
        (0.745098, (255, 28, 254)),
        (0.747549, (255, 31, 254)),
        (0.75, (255, 34, 254)),
        (0.752451, (255, 37, 254)),
        (0.754902, (255, 40, 254)),
        (0.757353, (255, 43, 254)),
        (0.759804, (255, 46, 254)),
        (0.762255, (255, 49, 254)),
        (0.764706, (255, 53, 253)),
        (0.767157, (255, 56, 253)),
        (0.769608, (255, 59, 253)),
        (0.772059, (255, 62, 253)),
        (0.77451, (255, 65, 253)),
        (0.776961, (255, 68, 253)),
        (0.779412, (255, 71, 253)),
        (0.781863, (255, 74, 253)),
        (0.784314, (255, 77, 253)),
        (0.786765, (255, 80, 253)),
        (0.789216, (255, 83, 253)),
        (0.791667, (255, 87, 252)),
        (0.794118, (255, 90, 252)),
        (0.796569, (255, 93, 252)),
        (0.79902, (255, 96, 252)),
        (0.801471, (255, 99, 252)),
        (0.803922, (255, 102, 252)),
        (0.806373, (255, 105, 252)),
        (0.808824, (255, 108, 252)),
        (0.811275, (255, 111, 252)),
        (0.813725, (255, 114, 252)),
        (0.816176, (255, 117, 252)),
        (0.818627, (255, 121, 251)),
        (0.821078, (255, 124, 251)),
        (0.823529, (255, 127, 251)),
        (0.82598, (255, 130, 251)),
        (0.828431, (255, 133, 251)),
        (0.830882, (255, 136, 251)),
        (0.833333, (255, 139, 251)),
        (0.835784, (255, 142, 251)),
        (0.838235, (255, 145, 251)),
        (0.840686, (255, 148, 251)),
        (0.843137, (255, 151, 251)),
        (0.845588, (255, 155, 250)),
        (0.848039, (255, 158, 250)),
        (0.85049, (255, 161, 250)),
        (0.852941, (255, 164, 250)),
        (0.855392, (255, 167, 250)),
        (0.857843, (255, 170, 250)),
        (0.860294, (255, 171, 250)),
        (0.862745, (255, 172, 251)),
        (0.865196, (255, 172, 250)),
        (0.867647, (255, 173, 250)),
        (0.870098, (255, 174, 251)),
        (0.872549, (255, 174, 250)),
        (0.875, (255, 175, 250)),
        (0.877451, (255, 176, 251)),
        (0.879902, (255, 176, 250)),
        (0.882353, (255, 177, 250)),
        (0.884804, (255, 178, 250)),
        (0.887255, (255, 180, 251)),
        (0.889706, (255, 181, 251)),
        (0.892157, (255, 183, 251)),
        (0.894608, (255, 185, 251)),
        (0.897059, (255, 186, 251)),
        (0.89951, (255, 188, 251)),
        (0.901961, (255, 190, 251)),
        (0.904412, (255, 191, 251)),
        (0.906863, (255, 193, 251)),
        (0.909314, (255, 195, 251)),
        (0.911765, (255, 196, 252)),
        (0.914216, (255, 198, 252)),
        (0.916667, (255, 199, 252)),
        (0.919118, (255, 201, 252)),
        (0.921569, (255, 203, 252)),
        (0.92402, (255, 204, 252)),
        (0.926471, (255, 206, 252)),
        (0.928922, (255, 208, 252)),
        (0.931373, (255, 209, 252)),
        (0.933824, (255, 211, 252)),
        (0.936275, (255, 212, 252)),
        (0.938725, (255, 214, 253)),
        (0.941176, (255, 216, 253)),
        (0.943627, (255, 217, 253)),
        (0.946078, (255, 219, 253)),
        (0.948529, (255, 221, 253)),
        (0.95098, (255, 222, 253)),
        (0.953431, (255, 224, 253)),
        (0.955882, (255, 226, 253)),
        (0.958333, (255, 227, 253)),
        (0.960784, (255, 229, 253)),
        (0.963235, (255, 230, 254)),
        (0.965686, (255, 232, 254)),
        (0.968137, (255, 234, 254)),
        (0.970588, (255, 235, 254)),
        (0.973039, (255, 237, 254)),
        (0.97549, (255, 239, 254)),
        (0.977941, (255, 240, 254)),
        (0.980392, (255, 242, 254)),
        (0.982843, (255, 244, 254)),
        (0.985294, (255, 245, 254)),
        (0.987745, (255, 247, 255)),
        (0.990196, (255, 248, 255)),
        (0.992647, (255, 250, 255)),
        (0.995098, (255, 252, 255)),
        (0.997549, (255, 253, 255)),
        (1.0, (255, 255, 255)),
    ]

    colors = [(r / 255.0, g / 255.0, b / 255.0) for _, (r, g, b) in color_stops]
    positions = [pos for pos, _ in color_stops]

    cdict = {
        "red": [(pos, r, r) for pos, (r, g, b) in zip(positions, colors)],
        "green": [(pos, g, g) for pos, (r, g, b) in zip(positions, colors)],
        "blue": [(pos, b, b) for pos, (r, g, b) in zip(positions, colors)],
    }

    return LinearSegmentedColormap("precipitation_custom", cdict, N=256)


PRECIPITATION_COLORMAP = create_precipitation_colormap()


CLIMATE_CONTOUR_CONFIGS: Dict[ClimateVarKey, ContourPlotConfig] = {
    ClimateVarKey.PRECIPITATION: ContourPlotConfig(
        level_lower=5,
        level_upper=400,
        colormap=PRECIPITATION_COLORMAP,
        title="Precipitation",
        unit="mm/month",
        log_scale=True,
    ),
    ClimateVarKey.T_MAX: ContourPlotConfig(
        level_lower=-20, level_upper=45, colormap=plt.cm.jet, title="Temperature (Day)", unit="C"
    ),
    ClimateVarKey.T_MIN: ContourPlotConfig(
        level_lower=-30, level_upper=28, colormap=plt.cm.jet, title="Temperature (Night)", unit="C"
    ),
    ClimateVarKey.CLOUD_COVER: ContourPlotConfig(
        level_lower=0, level_upper=100, colormap=plt.cm.RdYlBu, title="Cloud coverage", unit="%"
    ),
    ClimateVarKey.WET_DAYS: ContourPlotConfig(
        level_lower=0, level_upper=30, colormap=plt.cm.RdYlBu, title="Wet days", unit="days"
    ),
    ClimateVarKey.FROST_DAYS: ContourPlotConfig(
        level_lower=0, level_upper=30, colormap=plt.cm.RdYlBu, title="Frost days", unit="days"
    ),
    ClimateVarKey.RADIATION: ContourPlotConfig(
        level_lower=0, level_upper=300, colormap=plt.cm.RdYlBu_r, title="Radiation", unit="W/m^2"
    ),
    ClimateVarKey.DIURNAL_TEMP_RANGE: ContourPlotConfig(
        level_lower=5,
        level_upper=20,
        colormap=plt.cm.jet,
        title="Diurnal temperature range",
        unit="C",
    ),
    ClimateVarKey.VAPOUR_PRESSURE: ContourPlotConfig(
        level_lower=1, level_upper=34, colormap=plt.cm.jet, title="Vapour pressure", unit="hPa"
    ),
}

# Contour configurations for difference maps (future - historical)
# Only includes variables that have both historical and future data available
CLIMATE_DIFFERENCE_CONTOUR_CONFIGS: Dict[ClimateVarKey, ContourPlotConfig] = {
    ClimateVarKey.PRECIPITATION: ContourPlotConfig(
        level_lower=-35,
        level_upper=35,
        colormap=plt.cm.RdBu,
        title="Precipitation Change",
        unit="mm/month",
    ),
    ClimateVarKey.T_MAX: ContourPlotConfig(
        level_lower=-6,
        level_upper=6,
        colormap=plt.cm.RdYlBu_r,
        title="Temperature (Day) Change",
        unit="°C",
    ),
    ClimateVarKey.T_MIN: ContourPlotConfig(
        level_lower=-5,
        level_upper=5,
        colormap=plt.cm.RdYlBu_r,
        title="Temperature (Night) Change",
        unit="°C",
    ),
}


def convert_per_month_to_per_day(
    v: npt.NDArray[np.floating], month: int
) -> npt.NDArray[np.floating]:
    days_in_month = calendar.monthrange(2025, month)[1]
    return v / days_in_month


@dataclass
class ClimateDataConfig:
    variable_type: ClimateVarKey
    filepath: str
    format: DataFormat
    resolution: SpatialResolution
    year_range: Tuple[int, int]
    conversion_function: Callable[[npt.NDArray[np.floating], int], npt.NDArray[np.floating]] = None
    conversion_factor: float = 1
    source: Optional[str] = None

    @property
    def variable(self) -> ClimateVariable:
        return CLIMATE_VARIABLES[self.variable_type]

    @property
    def data_type_slug(self) -> str:
        return f"{self.variable.name}_{self.year_range[0]}_{self.year_range[1]}_{self.resolution.value}".lower().replace(
            ".", "_"
        )

    @property
    def contour_config(self) -> ContourPlotConfig:
        return CLIMATE_CONTOUR_CONFIGS[self.variable_type]


@dataclass
class FutureClimateDataConfig(ClimateDataConfig):
    climate_scenario: ClimateScenario = field(default=None)
    climate_model: ClimateModel = field(default=None)

    @property
    def data_type_slug(self) -> str:
        base_slug = super().data_type_slug
        return f"{base_slug}_{self.climate_scenario.name}_{self.climate_model.name}".lower()


@dataclass
class ClimateDifferenceDataConfig(ClimateDataConfig):
    """
    Configuration for climate difference maps (future - historical)
    """

    historical_config: ClimateDataConfig = field(default=None)
    future_config: FutureClimateDataConfig = field(default=None)

    @property
    def data_type_slug(self) -> str:
        if self.future_config and self.historical_config:
            return f"difference_{self.variable.name}_{self.historical_config.year_range[0]}_{self.historical_config.year_range[1]}_to_{self.future_config.year_range[0]}_{self.future_config.year_range[1]}_{self.resolution.value}_{self.future_config.climate_scenario.name}_{self.future_config.climate_model.name}".lower().replace(
                ".", "_"
            )
        return super().data_type_slug

    @property
    def contour_config(self) -> ContourPlotConfig:
        return CLIMATE_DIFFERENCE_CONTOUR_CONFIGS[self.variable_type]


@dataclass
class ClimateDataConfigGroup:
    variable_types: List[ClimateVarKey]
    format: DataFormat
    resolutions: List[SpatialResolution]
    year_ranges: List[Tuple[int, int]]
    conversion_function: Callable[[npt.NDArray[np.floating], int], npt.NDArray[np.floating]] = None
    conversion_factor: float = 1
    source: Optional[str] = None
    configs: List[ClimateDataConfig] = ()
    filepath_template: Optional[str] = None

    def __post_init__(self):
        for cfg in self.configs:
            cfg.group = self

    def create_configs(self) -> List[ClimateDataConfig]:
        configs: List[ClimateDataConfig] = []
        for variable_type in self.variable_types:
            for year_range in self.year_ranges:
                for resolution in self.resolutions:
                    variable = CLIMATE_VARIABLES[variable_type]
                    config = ClimateDataConfig(
                        variable_type=variable_type,
                        format=self.format,
                        resolution=resolution,
                        year_range=year_range,
                        filepath=self.filepath_template.format(
                            resolution=resolution.value,
                            year_range=year_range,
                            variable_name=variable.filename.lower(),
                        ),
                        conversion_function=self.conversion_function,
                        conversion_factor=self.conversion_factor,
                    )
                    configs.append(config)
        return configs


@dataclass
class FutureClimateDataConfigGroup(ClimateDataConfigGroup):
    climate_scenarios: List[ClimateScenario] = field(default_factory=list)
    climate_models: List[ClimateModel] = field(default_factory=list)
    configs: List[FutureClimateDataConfig] = field(default_factory=list)

    def create_configs(self) -> List[FutureClimateDataConfig]:
        configs: List[FutureClimateDataConfig] = []
        for variable_type in self.variable_types:
            for year_range in self.year_ranges:
                for resolution in self.resolutions:
                    for climate_scenario in self.climate_scenarios:
                        for climate_model in self.climate_models:
                            config = FutureClimateDataConfig(
                                variable_type=variable_type,
                                format=self.format,
                                resolution=resolution,
                                year_range=year_range,
                                climate_scenario=climate_scenario,
                                climate_model=climate_model,
                                filepath=self.filepath_template.format(
                                    resolution=resolution.value,
                                    year_range=year_range,
                                    variable_name=CLIMATE_VARIABLES[variable_type].filename.lower(),
                                    climate_scenario=climate_scenario.name.lower(),
                                    climate_model=climate_model.filename,
                                ),
                                conversion_function=self.conversion_function,
                                conversion_factor=self.conversion_factor,
                                source=self.source,
                            )
                            configs.append(config)
        return configs


CRU_TS_FILE_ABBREVIATIONS: Dict[ClimateVarKey, str] = {
    ClimateVarKey.CLOUD_COVER: "cld",
    ClimateVarKey.DIURNAL_TEMP_RANGE: "dtr",
    ClimateVarKey.WET_DAYS: "wet",
    ClimateVarKey.FROST_DAYS: "frs",
    ClimateVarKey.VAPOUR_PRESSURE: "vap",
    ClimateVarKey.T_MAX: "tmx",
    ClimateVarKey.T_MIN: "tmn",
    ClimateVarKey.PRECIPITATION: "pre",
}


@dataclass
class CRUTSClimateDataConfigGroup(ClimateDataConfigGroup):
    def create_configs(self) -> List[ClimateDataConfig]:
        configs: List[ClimateDataConfig] = []
        for variable_type in self.variable_types:
            for year_range in self.year_ranges:
                for resolution in self.resolutions:
                    abbr = CRU_TS_FILE_ABBREVIATIONS[variable_type]
                    config = ClimateDataConfig(
                        variable_type=variable_type,
                        format=self.format,
                        resolution=resolution,
                        year_range=year_range,
                        filepath=f"data/raw/cruts/cru_{abbr}_clim_{year_range[0]}-{year_range[1]}",
                        conversion_function=self.conversion_function,
                        conversion_factor=self.conversion_factor,
                        source=self.source,
                    )
                    configs.append(config)
        return configs


HISTORIC_DATA_GROUPS: List[ClimateDataConfigGroup] = [
    ClimateDataConfigGroup(
        variable_types=[ClimateVarKey.T_MAX, ClimateVarKey.T_MIN, ClimateVarKey.PRECIPITATION],
        format=DataFormat.GEOTIFF_WORLDCLIM_HISTORY,
        source="https://www.worldclim.org/data/worldclim21.html",
        resolutions=[SpatialResolution.MIN10, SpatialResolution.MIN5],
        year_ranges=[(1970, 2000)],
        filepath_template="data/raw/worldclim/history/wc2.1_{resolution}_{variable_name}",
    ),
    CRUTSClimateDataConfigGroup(
        variable_types=[
            ClimateVarKey.WET_DAYS,
            ClimateVarKey.FROST_DAYS,
        ],
        format=DataFormat.CRU_TS,
        source="https://ipcc-browser.ipcc-data.org/browser/dataset/653/0",
        resolutions=[SpatialResolution.MIN30],
        year_ranges=[(1961, 1990)],
        conversion_factor=0.124,
    ),
    CRUTSClimateDataConfigGroup(
        variable_types=[
            ClimateVarKey.DIURNAL_TEMP_RANGE,
        ],
        format=DataFormat.CRU_TS,
        source="https://ipcc-browser.ipcc-data.org/browser/dataset/653/0",
        resolutions=[SpatialResolution.MIN30],
        year_ranges=[(1961, 1990)],
        conversion_factor=0.16,
    ),
    CRUTSClimateDataConfigGroup(
        variable_types=[
            ClimateVarKey.VAPOUR_PRESSURE,
        ],
        format=DataFormat.CRU_TS,
        source="https://ipcc-browser.ipcc-data.org/browser/dataset/653/0",
        resolutions=[SpatialResolution.MIN30],
        year_ranges=[(1961, 1990)],
        conversion_factor=0.2,
    ),
    CRUTSClimateDataConfigGroup(
        variable_types=[ClimateVarKey.CLOUD_COVER],
        format=DataFormat.CRU_TS,
        source="https://ipcc-browser.ipcc-data.org/browser/dataset/653/0",
        resolutions=[SpatialResolution.MIN30],
        year_ranges=[(1961, 1990)],
        conversion_factor=0.4,  # https://www.ipcc-data.org/obs/info/cru10/cru_cld_clim_1901-1910.html
    ),
]


FUTURE_FILE_TEMPLATE = "data/raw/worldclim/future/wc2.1_{resolution}_{variable_name}_{climate_model}_{climate_scenario}_{year_range[0]}-{year_range[1]}.tif"
FUTURE_DATE_RANGES = [(2021, 2040), (2041, 2060), (2061, 2080), (2081, 2100)]

FUTURE_DATA_GROUPS: List[FutureClimateDataConfigGroup] = [
    FutureClimateDataConfigGroup(
        variable_types=[ClimateVarKey.T_MIN, ClimateVarKey.T_MAX, ClimateVarKey.PRECIPITATION],
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source="https://www.worldclim.org/data/cmip6/cmip6climate.html",
        resolutions=[SpatialResolution.MIN10, SpatialResolution.MIN5],
        year_ranges=FUTURE_DATE_RANGES,
        climate_scenarios=[
            ClimateScenario.SSP126,
            ClimateScenario.SSP245,
            ClimateScenario.SSP370,
            ClimateScenario.SSP585,
        ],
        climate_models=[
            ClimateModel.ENSEMBLE_MEAN,
        ],
        filepath_template=FUTURE_FILE_TEMPLATE,
    ),
    FutureClimateDataConfigGroup(
        variable_types=[ClimateVarKey.T_MIN, ClimateVarKey.T_MAX, ClimateVarKey.PRECIPITATION],
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source="https://www.worldclim.org/data/cmip6/cmip6climate.html",
        resolutions=[SpatialResolution.MIN10],
        year_ranges=FUTURE_DATE_RANGES,
        climate_scenarios=[
            ClimateScenario.SSP126,
            ClimateScenario.SSP245,
            ClimateScenario.SSP370,
            ClimateScenario.SSP585,
        ],
        climate_models=[
            ClimateModel.EC_EARTH3_VEG,
            ClimateModel.ACCESS_CM2,
            ClimateModel.MPI_ESM1_2_HR,
        ],
        filepath_template=FUTURE_FILE_TEMPLATE,
    ),
    FutureClimateDataConfigGroup(
        variable_types=[ClimateVarKey.T_MIN, ClimateVarKey.T_MAX, ClimateVarKey.PRECIPITATION],
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source="https://www.worldclim.org/data/cmip6/cmip6climate.html",
        resolutions=[SpatialResolution.MIN10],
        year_ranges=FUTURE_DATE_RANGES,
        climate_scenarios=[
            ClimateScenario.SSP126,
            ClimateScenario.SSP370,
        ],
        climate_models=[
            ClimateModel.GFDL_ESM4,
        ],
        filepath_template=FUTURE_FILE_TEMPLATE,
    ),
]

HISTORIC_DATA_SETS: List[ClimateDataConfig] = [
    cfg for data_group in HISTORIC_DATA_GROUPS for cfg in data_group.create_configs()
]

FUTURE_DATA_SETS: List[FutureClimateDataConfig] = [
    cfg for data_group in FUTURE_DATA_GROUPS for cfg in data_group.create_configs()
]


def create_difference_map_configs() -> List[ClimateDifferenceDataConfig]:
    """
    Create difference map configurations by pairing historical and future data
    """
    difference_configs = []

    for future_config in FUTURE_DATA_SETS:
        # Find matching historical config with same variable and resolution
        historical_config = None
        for hist_config in HISTORIC_DATA_SETS:
            if (
                hist_config.variable_type == future_config.variable_type
                and hist_config.resolution == future_config.resolution
            ):
                historical_config = hist_config
                break

        if historical_config:
            diff_config = ClimateDifferenceDataConfig(
                variable_type=future_config.variable_type,
                filepath="",  # Not used for difference maps
                format=future_config.format,
                resolution=future_config.resolution,
                year_range=future_config.year_range,
                conversion_function=None,
                conversion_factor=1,
                source=f"Difference: {future_config.source} - {historical_config.source}",
                historical_config=historical_config,
                future_config=future_config,
            )
            difference_configs.append(diff_config)

    return difference_configs


DIFFERENCE_DATA_SETS: List[ClimateDifferenceDataConfig] = create_difference_map_configs()
