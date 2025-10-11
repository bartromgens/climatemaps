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
        value: historicalRange1.value,
        label: `${historicalRange1.label} / ${historicalRange2.label}`,
        additionalValues: [historicalRange2.value],
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

    return Array.from(resolutions) as SpatialResolution[];
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

    return Array.from(scenarios) as ClimateScenario[];
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

    return Array.from(models) as ClimateModel[];
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
      WindSpeed: ClimateVarKey.WIND_SPEED,
      Radiation: ClimateVarKey.RADIATION,
      DiurnalTempRange: ClimateVarKey.DIURNAL_TEMP_RANGE,
      VapourPressure: ClimateVarKey.VAPOUR_PRESSURE,
    };

    return nameToKey[name] || null;
  }

  private formatYearRangeLabel(start: number, end: number): string {
    return `${start}-${end}`;
  }
}
