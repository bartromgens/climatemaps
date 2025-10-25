import { Injectable } from '@angular/core';
import { ClimateMap } from './climatemap';
import {
  ClimateVarKey,
  SpatialResolution,
  ClimateModel,
  ClimateScenario,
} from '../utils/enum';

export interface ClimateVariableConfig {
  name: string;
  displayName: string;
  unit: string;
}

export interface YearRange {
  value: [number, number];
  label: string;
  additionalValues?: [number, number][];
}

@Injectable({
  providedIn: 'root',
})
export class MetadataService {
  private readonly VARIABLE_ORDER: ClimateVarKey[] = [
    ClimateVarKey.T_MAX,
    ClimateVarKey.T_MIN,
    ClimateVarKey.PRECIPITATION,
    ClimateVarKey.WET_DAYS,
    ClimateVarKey.CLOUD_COVER,
    ClimateVarKey.FROST_DAYS,
    ClimateVarKey.DIURNAL_TEMP_RANGE,
    ClimateVarKey.VAPOUR_PRESSURE,
    ClimateVarKey.VAPOUR_PRESSURE_DEFICIT,
    ClimateVarKey.RADIATION,
    ClimateVarKey.WIND_SPEED,
    ClimateVarKey.RELATIVE_HUMIDITY,
    ClimateVarKey.MOISTURE_INDEX,
  ];

  private readonly RESOLUTION_ORDER: SpatialResolution[] = [
    SpatialResolution.MIN0_5,
    SpatialResolution.MIN2_5,
    SpatialResolution.MIN5,
    SpatialResolution.MIN10,
    SpatialResolution.MIN30,
  ];

  private readonly MODEL_ORDER: ClimateModel[] = [
    ClimateModel.ENSEMBLE_MEAN,
    ClimateModel.ACCESS_CM2,
    ClimateModel.BCC_CSM2_MR,
    ClimateModel.CMCC_ESM2,
    ClimateModel.EC_EARTH3_VEG,
    ClimateModel.FIO_ESM_2_0,
    ClimateModel.GFDL_ESM4,
    ClimateModel.GISS_E2_1_G,
    ClimateModel.HADGEM3_GC31_LL,
    ClimateModel.INM_CM5_0,
    ClimateModel.IPSL_CM6A_LR,
    ClimateModel.MIROC6,
    ClimateModel.MPI_ESM1_2_HR,
    ClimateModel.MRI_ESM2_0,
    ClimateModel.UKESM1_0_LL,
  ];

  private readonly SCENARIO_ORDER: ClimateScenario[] = [
    ClimateScenario.SSP126,
    ClimateScenario.SSP245,
    ClimateScenario.SSP370,
    ClimateScenario.SSP585,
  ];

  /**
   * Extract unique climate variables from API data
   */
  getClimateVariables(
    climateMaps: ClimateMap[],
  ): Record<ClimateVarKey, ClimateVariableConfig> {
    const variables: Record<string, ClimateVariableConfig> = {};

    climateMaps.forEach((map) => {
      const key = this.getVariableKeyFromName(map.variable.name);
      if (key && !variables[key]) {
        variables[key] = {
          name: map.variable.name,
          displayName: map.variable.displayName,
          unit: map.variable.unit,
        };
      }
    });

    return variables as Record<ClimateVarKey, ClimateVariableConfig>;
  }

  /**
   * Extract unique year ranges from API data
   */
  getYearRanges(climateMaps: ClimateMap[]): YearRange[] {
    const yearRanges = new Set<string>();

    climateMaps.forEach((map) => {
      const key = `${map.yearRange[0]}-${map.yearRange[1]}`;
      yearRanges.add(key);
    });

    const ranges = Array.from(yearRanges)
      .map((key) => {
        const [start, end] = key.split('-').map(Number);
        return {
          value: [start, end] as [number, number],
          label: this.formatYearRangeLabel(start, end),
        };
      })
      .sort((a, b) => a.value[0] - b.value[0]);

    const historicalRange1 = ranges.find(
      (r) => r.value[0] === 1961 && r.value[1] === 1990,
    );
    const historicalRange2 = ranges.find(
      (r) => r.value[0] === 1970 && r.value[1] === 2000,
    );

    if (historicalRange1 && historicalRange2) {
      const mergedRange: YearRange = {
        value: historicalRange2.value,
        label: '1970-2000',
        additionalValues: [historicalRange1.value],
      };

      return ranges
        .filter(
          (r) =>
            !(r.value[0] === 1961 && r.value[1] === 1990) &&
            !(r.value[0] === 1970 && r.value[1] === 2000),
        )
        .concat([mergedRange])
        .sort((a, b) => a.value[0] - b.value[0]);
    }

    return ranges;
  }

  /**
   * Extract unique resolutions from API data
   */
  getResolutions(climateMaps: ClimateMap[]): SpatialResolution[] {
    const resolutions = new Set<string>();

    climateMaps.forEach((map) => {
      resolutions.add(map.resolution);
    });

    const resolutionArray = Array.from(resolutions) as SpatialResolution[];

    return this.sortByOrder(resolutionArray, this.RESOLUTION_ORDER);
  }

  /**
   * Extract unique climate scenarios from API data
   */
  getClimateScenarios(climateMaps: ClimateMap[]): ClimateScenario[] {
    const scenarios = new Set<string>();

    climateMaps.forEach((map) => {
      if (map.climateScenario) {
        scenarios.add(map.climateScenario);
      }
    });

    const scenarioArray = Array.from(scenarios) as ClimateScenario[];

    return this.sortByOrder(scenarioArray, this.SCENARIO_ORDER);
  }

  /**
   * Extract unique climate models from API data
   */
  getClimateModels(climateMaps: ClimateMap[]): ClimateModel[] {
    const models = new Set<string>();

    climateMaps.forEach((map) => {
      if (map.climateModel) {
        models.add(map.climateModel);
      }
    });

    const modelArray = Array.from(models) as ClimateModel[];

    return this.sortByOrder(modelArray, this.MODEL_ORDER);
  }

  getSortedVariableTypes(
    climateVariables: Record<ClimateVarKey, ClimateVariableConfig>,
  ): ClimateVarKey[] {
    const variableKeys = Object.keys(climateVariables) as ClimateVarKey[];
    return this.sortByOrder(variableKeys, this.VARIABLE_ORDER);
  }

  /**
   * Check if a year range is historical (before 2000)
   */
  isHistoricalYearRange(yearRange: readonly [number, number]): boolean {
    return yearRange[0] < 2000;
  }

  private getVariableKeyFromName(name: string): ClimateVarKey | null {
    const nameToKey: Record<string, ClimateVarKey> = {
      Precipitation: ClimateVarKey.PRECIPITATION,
      Tmax: ClimateVarKey.T_MAX,
      Tmin: ClimateVarKey.T_MIN,
      CloudCover: ClimateVarKey.CLOUD_COVER,
      WetDays: ClimateVarKey.WET_DAYS,
      FrostDays: ClimateVarKey.FROST_DAYS,
      WindSpeed: ClimateVarKey.WIND_SPEED,
      Radiation: ClimateVarKey.RADIATION,
      DiurnalTempRange: ClimateVarKey.DIURNAL_TEMP_RANGE,
      VapourPressure: ClimateVarKey.VAPOUR_PRESSURE,
      VapourPressureDeficit: ClimateVarKey.VAPOUR_PRESSURE_DEFICIT,
      RelativeHumidity: ClimateVarKey.RELATIVE_HUMIDITY,
      MoistureIndex: ClimateVarKey.MOISTURE_INDEX,
    };

    const result = nameToKey[name];
    if (!result) {
      console.error(
        `Unknown variable name: ${name}. Available names: ${Object.keys(nameToKey).join(', ')}`,
      );
    }
    return result || null;
  }

  private formatYearRangeLabel(start: number, end: number): string {
    // Show specific labels for known historical ranges
    if (start === 1961 && end === 1990) {
      return '1961-1990';
    }
    if (start === 1970 && end === 2000) {
      return '1970-2000';
    }
    if (start === 1981 && end === 2010) {
      return '1981-2010';
    }
    // For other historical ranges, show the actual range
    if (start < 2000) {
      return `${start}-${end}`;
    }
    return `${start}-${end}`;
  }

  private sortByOrder<T>(items: T[], order: T[]): T[] {
    return items.sort((a, b) => {
      const indexA = order.indexOf(a);
      const indexB = order.indexOf(b);

      if (indexA === -1 && indexB === -1) return 0;
      if (indexA === -1) return 1;
      if (indexB === -1) return -1;

      return indexA - indexB;
    });
  }
}
