// Climate Variable Type enum matching the backend
export enum ClimateVarKey {
  PRECIPITATION = 'PRECIPITATION',
  T_MAX = 'T_MAX',
  T_MIN = 'T_MIN',
  CLOUD_COVER = 'CLOUD_COVER',
  WET_DAYS = 'WET_DAYS',
  FROST_DAYS = 'FROST_DAYS',
  WIND_SPEED = 'WIND_SPEED',
  RADIATION = 'RADIATION',
  DIURNAL_TEMP_RANGE = 'DIURNAL_TEMP_RANGE',
  VAPOUR_PRESSURE = 'VAPOUR_PRESSURE',
}

// Spatial Resolution enum matching the backend
export enum SpatialResolution {
  MIN30 = '30m',
  MIN10 = '10m',
  MIN5 = '5m',
  MIN2_5 = '2.5m',
}

// Climate Model enum matching the backend
export enum ClimateModel {
  ACCESS_CM2 = 'ACCESS-CM2',
  BCC_CSM2_MR = 'BCC-CSM2-MR',
  CMCC_ESM2 = 'CMCC-ESM2',
  EC_EARTH3_VEG = 'EC-Earth3-Veg',
  FIO_ESM_2_0 = 'FIO-ESM-2-0',
  GFDL_ESM4 = 'GFDL-ESM4',
  GISS_E2_1_G = 'GISS-E2-1-G',
  HADGEM3_GC31_LL = 'HadGEM3-GC31-LL',
  INM_CM5_0 = 'INM-CM5-0',
  IPSL_CM6A_LR = 'IPSL-CM6A-LR',
  MIROC6 = 'MIROC6',
  MPI_ESM1_2_HR = 'MPI-ESM1-2-HR',
  MRI_ESM2_0 = 'MRI-ESM2-0',
  UKESM1_0_LL = 'UKESM1-0-LL',
}

// Climate Scenario enum matching the backend
export enum ClimateScenario {
  SSP126 = 'SSP126',
  SSP245 = 'SSP245',
  SSP370 = 'SSP370',
  SSP585 = 'SSP585',
}

// Data format enum matching the backend
export enum DataFormat {
  GEOTIFF_WORLDCLIM_CMIP6 = 'GEOTIFF_WORLDCLIM_CMIP6',
  GEOTIFF_WORLDCLIM_HISTORY = 'GEOTIFF_WORLDCLIM_HISTORY',
  CRU_TS = 'CRU_TS',
}

// Note: Climate variable configurations and year ranges are now dynamically
// loaded from the API via the MetadataService instead of being hardcoded here.

// eslint-disable-next-line @typescript-eslint/no-namespace
export namespace EnumUtils {
  export function getEnumKeyByValue<T extends Record<string, string | number>>(
    enumObj: T,
    value: string | number,
  ): string | undefined {
    return Object.keys(enumObj).find(
      (key) => enumObj[key as keyof T] === value,
    );
  }
}
