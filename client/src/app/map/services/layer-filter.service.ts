import { Injectable } from '@angular/core';
import { ClimateMap } from '../../core/climatemap';
import {
  ClimateVarKey,
  SpatialResolution,
  ClimateScenario,
  ClimateModel,
} from '../../utils/enum';
import { ClimateVariableConfig, YearRange } from '../../core/metadata.service';
import { MapControlsData } from '../map-controls.component';

@Injectable({
  providedIn: 'root',
})
export class LayerFilterService {
  private matchesYearRange(map: ClimateMap, yearRange: YearRange): boolean {
    const matchesPrimary =
      map.yearRange[0] === yearRange.value[0] &&
      map.yearRange[1] === yearRange.value[1];

    const matchesAdditional = yearRange.additionalValues?.some(
      (additionalValue) =>
        map.yearRange[0] === additionalValue[0] &&
        map.yearRange[1] === additionalValue[1],
    );

    return matchesPrimary || !!matchesAdditional;
  }

  getAvailableVariableTypes(
    climateMaps: ClimateMap[],
    variableTypes: ClimateVarKey[],
    climateVariables: Record<ClimateVarKey, ClimateVariableConfig>,
  ): ClimateVarKey[] {
    return variableTypes.filter((variableType) => {
      return climateMaps.some(
        (map) => map.variable.name === climateVariables[variableType]?.name,
      );
    });
  }

  getAvailableYearRanges(
    climateMaps: ClimateMap[],
    yearRanges: YearRange[],
    controlsData: MapControlsData,
    climateVariables: Record<ClimateVarKey, ClimateVariableConfig>,
  ): YearRange[] {
    return yearRanges.filter((yearRange) => {
      return climateMaps.some((map) => {
        if (!this.matchesYearRange(map, yearRange)) return false;
        if (
          map.variable.name !==
          climateVariables[controlsData.selectedVariableType]?.name
        )
          return false;

        // Historical data: ignore showDifferenceMap checkbox, only match non-difference maps
        const isHistorical =
          map.climateScenario === null && map.climateModel === null;
        if (isHistorical) {
          return !map.isDifferenceMap;
        }

        // Future data: respect showDifferenceMap checkbox
        return controlsData.showDifferenceMap
          ? true
          : map.isDifferenceMap === controlsData.showDifferenceMap;
      });
    });
  }

  getAvailableResolutions(
    climateMaps: ClimateMap[],
    resolutions: SpatialResolution[],
    controlsData: MapControlsData,
    climateVariables: Record<ClimateVarKey, ClimateVariableConfig>,
    isHistoricalYearRange: (yearRange: readonly [number, number]) => boolean,
  ): SpatialResolution[] {
    if (!controlsData.selectedYearRange) return [];

    const isHistorical = isHistoricalYearRange(
      controlsData.selectedYearRange.value,
    );

    const matchingMaps = climateMaps.filter((map) => {
      if (
        map.variable.name !==
        climateVariables[controlsData.selectedVariableType]?.name
      )
        return false;
      if (!this.matchesYearRange(map, controlsData.selectedYearRange!))
        return false;

      // For historical data, ignore showDifferenceMap checkbox and only match non-difference maps
      if (isHistorical) {
        return !map.isDifferenceMap;
      }

      // For future data, respect showDifferenceMap checkbox
      return map.isDifferenceMap === controlsData.showDifferenceMap;
    });

    let filteredMaps = matchingMaps;
    if (!isHistorical) {
      if (controlsData.selectedClimateScenario) {
        filteredMaps = filteredMaps.filter(
          (map) => map.climateScenario === controlsData.selectedClimateScenario,
        );
      }
      if (controlsData.selectedClimateModel) {
        filteredMaps = filteredMaps.filter(
          (map) => map.climateModel === controlsData.selectedClimateModel,
        );
      }
    }

    return resolutions.filter((resolution) =>
      filteredMaps.some((map) => map.resolution === resolution),
    );
  }

  getAvailableClimateScenarios(
    climateMaps: ClimateMap[],
    climateScenarios: ClimateScenario[],
    controlsData: MapControlsData,
    climateVariables: Record<ClimateVarKey, ClimateVariableConfig>,
    isHistoricalYearRange: (yearRange: readonly [number, number]) => boolean,
  ): ClimateScenario[] {
    if (!controlsData.selectedYearRange) {
      return [];
    }

    const isHistorical = isHistoricalYearRange(
      controlsData.selectedYearRange.value,
    );

    // Historical data doesn't have climate scenarios
    if (isHistorical) {
      return [];
    }

    const matchingMaps = climateMaps.filter(
      (map) =>
        map.variable.name ===
          climateVariables[controlsData.selectedVariableType]?.name &&
        this.matchesYearRange(map, controlsData.selectedYearRange!) &&
        map.isDifferenceMap === controlsData.showDifferenceMap,
    );

    return climateScenarios.filter((scenario) =>
      matchingMaps.some((map) => map.climateScenario === scenario),
    );
  }

  getAvailableClimateModels(
    climateMaps: ClimateMap[],
    climateModels: ClimateModel[],
    controlsData: MapControlsData,
    climateVariables: Record<ClimateVarKey, ClimateVariableConfig>,
    isHistoricalYearRange: (yearRange: readonly [number, number]) => boolean,
  ): ClimateModel[] {
    if (!controlsData.selectedYearRange) {
      return [];
    }

    const isHistorical = isHistoricalYearRange(
      controlsData.selectedYearRange.value,
    );

    // Historical data doesn't have climate models
    if (isHistorical) {
      return [];
    }

    const matchingMaps = climateMaps.filter(
      (map) =>
        map.variable.name ===
          climateVariables[controlsData.selectedVariableType]?.name &&
        this.matchesYearRange(map, controlsData.selectedYearRange!) &&
        map.isDifferenceMap === controlsData.showDifferenceMap,
    );

    let filteredMaps = matchingMaps;
    if (controlsData.selectedClimateScenario) {
      filteredMaps = filteredMaps.filter(
        (map) => map.climateScenario === controlsData.selectedClimateScenario,
      );
    }

    return climateModels.filter((model) =>
      filteredMaps.some((map) => map.climateModel === model),
    );
  }
}
