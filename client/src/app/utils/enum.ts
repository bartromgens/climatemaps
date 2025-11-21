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
  RELATIVE_HUMIDITY = 'RELATIVE_HUMIDITY',
  MOISTURE_INDEX = 'MOISTURE_INDEX',
  VAPOUR_PRESSURE_DEFICIT = 'VAPOUR_PRESSURE_DEFICIT',
}

export const CLIMATE_VAR_KEY_TO_NAME: Record<ClimateVarKey, string> = {
  [ClimateVarKey.T_MAX]: 'tmax',
  [ClimateVarKey.T_MIN]: 'tmin',
  [ClimateVarKey.PRECIPITATION]: 'precipitation',
  [ClimateVarKey.CLOUD_COVER]: 'cloud_cover',
  [ClimateVarKey.WET_DAYS]: 'wet_days',
  [ClimateVarKey.FROST_DAYS]: 'frost_days',
  [ClimateVarKey.WIND_SPEED]: 'wind_speed',
  [ClimateVarKey.RADIATION]: 'radiation',
  [ClimateVarKey.DIURNAL_TEMP_RANGE]: 'diurnal_temp_range',
  [ClimateVarKey.VAPOUR_PRESSURE]: 'vapour_pressure',
  [ClimateVarKey.RELATIVE_HUMIDITY]: 'relative_humidity',
  [ClimateVarKey.MOISTURE_INDEX]: 'moisture_index',
  [ClimateVarKey.VAPOUR_PRESSURE_DEFICIT]: 'vapour_pressure_deficit',
};

export const CLIMATE_VAR_NAME_TO_KEY: Record<string, ClimateVarKey> =
  Object.fromEntries(
    (Object.entries(CLIMATE_VAR_KEY_TO_NAME) as [ClimateVarKey, string][]).map(
      ([key, name]) => [name, key],
    ),
  ) as Record<string, ClimateVarKey>;

export const CLIMATE_VAR_DISPLAY_NAMES: Record<ClimateVarKey, string> = {
  [ClimateVarKey.T_MAX]: 'Temperature (Day)',
  [ClimateVarKey.T_MIN]: 'Temperature (Night)',
  [ClimateVarKey.PRECIPITATION]: 'Precipitation',
  [ClimateVarKey.CLOUD_COVER]: 'Cloud Cover',
  [ClimateVarKey.WET_DAYS]: 'Wet Days',
  [ClimateVarKey.FROST_DAYS]: 'Frost Days',
  [ClimateVarKey.WIND_SPEED]: 'Wind Speed',
  [ClimateVarKey.RADIATION]: 'Radiation',
  [ClimateVarKey.DIURNAL_TEMP_RANGE]: 'Diurnal Temperature Range',
  [ClimateVarKey.VAPOUR_PRESSURE]: 'Vapour Pressure',
  [ClimateVarKey.RELATIVE_HUMIDITY]: 'Relative Humidity',
  [ClimateVarKey.MOISTURE_INDEX]: 'Moisture Index',
  [ClimateVarKey.VAPOUR_PRESSURE_DEFICIT]: 'Vapour Pressure Deficit',
};

export const CLIMATE_VAR_UNITS: Record<ClimateVarKey, string> = {
  [ClimateVarKey.T_MAX]: '°C',
  [ClimateVarKey.T_MIN]: '°C',
  [ClimateVarKey.PRECIPITATION]: 'mm/month',
  [ClimateVarKey.CLOUD_COVER]: '%',
  [ClimateVarKey.WET_DAYS]: 'days',
  [ClimateVarKey.FROST_DAYS]: 'days',
  [ClimateVarKey.WIND_SPEED]: 'm/s',
  [ClimateVarKey.RADIATION]: 'W/m²',
  [ClimateVarKey.DIURNAL_TEMP_RANGE]: '°C',
  [ClimateVarKey.VAPOUR_PRESSURE]: 'hPa',
  [ClimateVarKey.RELATIVE_HUMIDITY]: '%',
  [ClimateVarKey.MOISTURE_INDEX]: 'mm/month',
  [ClimateVarKey.VAPOUR_PRESSURE_DEFICIT]: 'Pa',
};

// Spatial Resolution enum matching the backend
export enum SpatialResolution {
  MIN30 = '30m',
  MIN10 = '10m',
  MIN5 = '5m',
  MIN2_5 = '2.5m',
  MIN0_5 = '0.5m',
}

// Climate Model enum matching the backend
export enum ClimateModel {
  ENSEMBLE_MEAN = 'ENSEMBLE_MEAN',
  ENSEMBLE_STD_DEV = 'ENSEMBLE_STD_DEV',
  ACCESS_CM2 = 'ACCESS_CM2',
  BCC_CSM2_MR = 'BCC_CSM2_MR',
  CMCC_ESM2 = 'CMCC_ESM2',
  EC_EARTH3_VEG = 'EC_Earth3_Veg',
  FIO_ESM_2_0 = 'FIO_ESM_2_0',
  GFDL_ESM4 = 'GFDL_ESM4',
  GISS_E2_1_G = 'GISS_E2_1_G',
  HADGEM3_GC31_LL = 'HadGEM3_GC31_LL',
  INM_CM5_0 = 'INM_CM5_0',
  IPSL_CM6A_LR = 'IPSL_CM6A_LR',
  MIROC6 = 'MIROC6',
  MPI_ESM1_2_HR = 'MPI_ESM1_2_HR',
  MRI_ESM2_0 = 'MRI_ESM2_0',
  UKESM1_0_LL = 'UKESM1_0_LL',
}

// Climate Scenario enum matching the backend
export enum ClimateScenario {
  SSP126 = 'SSP126',
  SSP245 = 'SSP245',
  SSP370 = 'SSP370',
  SSP585 = 'SSP585',
}

export const CLIMATE_SCENARIO_DISPLAY_NAMES: Record<ClimateScenario, string> = {
  [ClimateScenario.SSP126]: 'Strong climate action (SSP1-2.6)',
  [ClimateScenario.SSP245]: 'Moderate climate action (SSP2-4.5)',
  [ClimateScenario.SSP370]: 'Limited climate action (SSP3-7.0)',
  [ClimateScenario.SSP585]: 'Minimal climate action (SSP5-8.5)',
};

export function getClimateModelDisplayName(model: ClimateModel): string {
  if (model === ClimateModel.ENSEMBLE_MEAN) {
    return 'Ensemble Mean';
  }
  if (model === ClimateModel.ENSEMBLE_STD_DEV) {
    return 'Ensemble Std. Deviation';
  }
  return model.replace(/_/g, '-');
}

// Data format enum matching the backend
export enum DataFormat {
  GEOTIFF_WORLDCLIM_CMIP6 = 'GEOTIFF_WORLDCLIM_CMIP6',
  GEOTIFF_WORLDCLIM_HISTORY = 'GEOTIFF_WORLDCLIM_HISTORY',
  CRU_TS = 'CRU_TS',
}

// Note: Climate variable configurations and year ranges are now dynamically
// loaded from the API via the MetadataService instead of being hardcoded here.

export function getClimateVarKeyFromDataType(
  dataType: string,
): ClimateVarKey | null {
  const firstPart = dataType.split('_')[0];
  return CLIMATE_VAR_NAME_TO_KEY[firstPart] || null;
}

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
