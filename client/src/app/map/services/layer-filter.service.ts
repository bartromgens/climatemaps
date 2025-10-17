import { Injectable } from '@angular/core';
import { ClimateMap } from '../../core/climatemap';
import {
  ClimateVarKey,
  SpatialResolution,
  ClimateScenario,
  ClimateModel,
} from '../../utils/enum';
import { ClimateVariableConfig, YearRange } from '../../core/metadata.service';
import { MapControlsData } from '../controls/map-controls.component';

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

  private matchesVariableType(
    map: ClimateMap,
    variableType: ClimateVarKey,
    climateVariables: Record<ClimateVarKey, ClimateVariableConfig>,
  ): boolean {
    return map.variable.name === climateVariables[variableType]?.name;
  }

  private matchesDifferenceMapCriteria(
    map: ClimateMap,
    showDifferenceMap: boolean,
    isHistorical: boolean,
  ): boolean {
    if (isHistorical) {
      return !map.isDifferenceMap;
    }
    return map.isDifferenceMap === showDifferenceMap;
  }

  private getBaseFilteredMaps(
    climateMaps: ClimateMap[],
    controlsData: MapControlsData,
    climateVariables: Record<ClimateVarKey, ClimateVariableConfig>,
    isHistorical: boolean,
  ): ClimateMap[] {
    return climateMaps.filter(
      (map) =>
        this.matchesVariableType(
          map,
          controlsData.selectedVariableType,
          climateVariables,
        ) &&
        this.matchesYearRange(map, controlsData.selectedYearRange!) &&
        this.matchesDifferenceMapCriteria(
          map,
          controlsData.showDifferenceMap,
          isHistorical,
        ),
    );
  }

  getAvailableVariableTypes(
    climateMaps: ClimateMap[],
    variableTypes: ClimateVarKey[],
    climateVariables: Record<ClimateVarKey, ClimateVariableConfig>,
  ): ClimateVarKey[] {
    return variableTypes.filter((variableType) =>
      climateMaps.some((map) =>
        this.matchesVariableType(map, variableType, climateVariables),
      ),
    );
  }

  getAvailableYearRanges(
    climateMaps: ClimateMap[],
    yearRanges: YearRange[],
    controlsData: MapControlsData,
    climateVariables: Record<ClimateVarKey, ClimateVariableConfig>,
  ): YearRange[] {
    return yearRanges.filter((yearRange) =>
      climateMaps.some((map) => {
        if (!this.matchesYearRange(map, yearRange)) return false;
        if (
          !this.matchesVariableType(
            map,
            controlsData.selectedVariableType,
            climateVariables,
          )
        )
          return false;

        const isHistorical =
          map.climateScenario === null && map.climateModel === null;
        return this.matchesDifferenceMapCriteria(
          map,
          controlsData.showDifferenceMap,
          isHistorical,
        );
      }),
    );
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

    let filteredMaps = this.getBaseFilteredMaps(
      climateMaps,
      controlsData,
      climateVariables,
      isHistorical,
    );

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
    if (!controlsData.selectedYearRange) return [];

    const isHistorical = isHistoricalYearRange(
      controlsData.selectedYearRange.value,
    );

    if (isHistorical) return [];

    const matchingMaps = this.getBaseFilteredMaps(
      climateMaps,
      controlsData,
      climateVariables,
      isHistorical,
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
    if (!controlsData.selectedYearRange) return [];

    const isHistorical = isHistoricalYearRange(
      controlsData.selectedYearRange.value,
    );

    if (isHistorical) return [];

    let filteredMaps = this.getBaseFilteredMaps(
      climateMaps,
      controlsData,
      climateVariables,
      isHistorical,
    );

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
