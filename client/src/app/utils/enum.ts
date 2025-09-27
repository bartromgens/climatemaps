// Climate Model enum matching the backend
export enum ClimateModel {
  ACCESS_CM2 = 'ACCESS_CM2',
  BCC_CSM2_MR = 'BCC_CSM2_MR',
  CMCC_ESM2 = 'CMCC_ESM2',
  EC_EARTH3_VEG = 'EC-Earth3-Veg',
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
