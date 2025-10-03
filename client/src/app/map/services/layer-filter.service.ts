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
      return climateMaps.some(
        (map) =>
          map.yearRange[0] === yearRange.value[0] &&
          map.yearRange[1] === yearRange.value[1] &&
          map.variable.name ===
            climateVariables[controlsData.selectedVariableType]?.name &&
          map.isDifferenceMap === controlsData.showDifferenceMap,
      );
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

    const matchingMaps = climateMaps.filter(
      (map) =>
        map.variable.name ===
          climateVariables[controlsData.selectedVariableType]?.name &&
        map.yearRange[0] === controlsData.selectedYearRange!.value[0] &&
        map.yearRange[1] === controlsData.selectedYearRange!.value[1] &&
        map.isDifferenceMap === controlsData.showDifferenceMap,
    );

    let filteredMaps = matchingMaps;
    if (!isHistoricalYearRange(controlsData.selectedYearRange!.value)) {
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
    if (
      !controlsData.selectedYearRange ||
      (isHistoricalYearRange(controlsData.selectedYearRange.value) &&
        !controlsData.showDifferenceMap)
    ) {
      return [];
    }

    const matchingMaps = climateMaps.filter(
      (map) =>
        map.variable.name ===
          climateVariables[controlsData.selectedVariableType]?.name &&
        map.yearRange[0] === controlsData.selectedYearRange!.value[0] &&
        map.yearRange[1] === controlsData.selectedYearRange!.value[1] &&
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
    if (
      !controlsData.selectedYearRange ||
      (isHistoricalYearRange(controlsData.selectedYearRange.value) &&
        !controlsData.showDifferenceMap)
    ) {
      return [];
    }

    const matchingMaps = climateMaps.filter(
      (map) =>
        map.variable.name ===
          climateVariables[controlsData.selectedVariableType]?.name &&
        map.yearRange[0] === controlsData.selectedYearRange!.value[0] &&
        map.yearRange[1] === controlsData.selectedYearRange!.value[1] &&
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
