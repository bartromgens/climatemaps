import {
  ClimateVarKey,
  SpatialResolution,
  ClimateScenario,
  ClimateModel,
} from './enum';
import { YearRange } from '../core/metadata.service';

export interface URLControlsData {
  variable?: ClimateVarKey;
  resolution?: SpatialResolution;
  scenario?: ClimateScenario;
  model?: ClimateModel;
  difference?: boolean;
  month?: number;
  yearRange?: string; // Format: "startYear-endYear"
}

export class URLUtils {
  static encodeControls(controlsData: {
    selectedVariableType: ClimateVarKey;
    selectedResolution: SpatialResolution;
    selectedClimateScenario: ClimateScenario | null;
    selectedClimateModel: ClimateModel | null;
    showDifferenceMap: boolean;
    selectedMonth: number;
    selectedYearRange: YearRange | null;
  }): URLControlsData {
    const urlData: URLControlsData = {};

    if (controlsData.selectedVariableType) {
      urlData.variable = controlsData.selectedVariableType;
    }

    if (controlsData.selectedResolution) {
      urlData.resolution = controlsData.selectedResolution;
    }

    if (controlsData.selectedClimateScenario) {
      urlData.scenario = controlsData.selectedClimateScenario;
    }

    if (controlsData.selectedClimateModel) {
      urlData.model = controlsData.selectedClimateModel;
    }

    urlData.difference = controlsData.showDifferenceMap;
    urlData.month = controlsData.selectedMonth;

    if (controlsData.selectedYearRange) {
      urlData.yearRange = `${controlsData.selectedYearRange.value[0]}-${controlsData.selectedYearRange.value[1]}`;
    }

    return urlData;
  }

  static decodeControls(
    urlData: URLControlsData,
    yearRanges: YearRange[],
  ): {
    variable?: ClimateVarKey;
    resolution?: SpatialResolution;
    scenario?: ClimateScenario;
    model?: ClimateModel;
    difference?: boolean;
    month?: number;
    yearRange?: YearRange;
  } {
    const decoded: any = {};

    if (
      urlData.variable &&
      Object.values(ClimateVarKey).includes(urlData.variable)
    ) {
      decoded.variable = urlData.variable;
    }

    if (
      urlData.resolution &&
      Object.values(SpatialResolution).includes(urlData.resolution)
    ) {
      decoded.resolution = urlData.resolution;
    }

    if (
      urlData.scenario &&
      Object.values(ClimateScenario).includes(urlData.scenario)
    ) {
      decoded.scenario = urlData.scenario;
    }

    if (urlData.model && Object.values(ClimateModel).includes(urlData.model)) {
      decoded.model = urlData.model;
    }

    if (typeof urlData.difference === 'boolean') {
      decoded.difference = urlData.difference;
    }

    if (urlData.month && urlData.month >= 1 && urlData.month <= 12) {
      decoded.month = urlData.month;
    }

    if (urlData.yearRange) {
      try {
        const [startYear, endYear] = urlData.yearRange
          .split('-')
          .map((y) => parseInt(y, 10));
        const yearRange = yearRanges.find((yr) => {
          const matchesPrimary =
            yr.value[0] === startYear && yr.value[1] === endYear;
          const matchesAdditional = yr.additionalValues?.some(
            (additionalValue) =>
              additionalValue[0] === startYear &&
              additionalValue[1] === endYear,
          );
          return matchesPrimary || matchesAdditional;
        });
        if (yearRange) {
          decoded.yearRange = yearRange;
        }
      } catch {
        console.warn('Invalid year range parameter:', urlData.yearRange);
      }
    }

    return decoded;
  }

  static updateURLParams(params: URLControlsData): void {
    const url = new URL(window.location.href);

    // Preserve lat, lon, zoom parameters
    const lat = url.searchParams.get('lat');
    const lon = url.searchParams.get('lon');
    const zoom = url.searchParams.get('zoom');

    // Clear existing control parameters
    url.searchParams.delete('variable');
    url.searchParams.delete('resolution');
    url.searchParams.delete('scenario');
    url.searchParams.delete('model');
    url.searchParams.delete('difference');
    url.searchParams.delete('month');
    url.searchParams.delete('yearRange');

    // Set new parameters
    if (params.variable) {
      url.searchParams.set('variable', params.variable);
    }
    if (params.resolution) {
      url.searchParams.set('resolution', params.resolution);
    }
    if (params.scenario) {
      url.searchParams.set('scenario', params.scenario);
    }
    if (params.model) {
      url.searchParams.set('model', params.model);
    }
    if (typeof params.difference === 'boolean') {
      url.searchParams.set('difference', params.difference.toString());
    }
    if (params.month) {
      url.searchParams.set('month', params.month.toString());
    }
    if (params.yearRange) {
      url.searchParams.set('yearRange', params.yearRange);
    }

    // Restore lat, lon, zoom if they existed
    if (lat) url.searchParams.set('lat', lat);
    if (lon) url.searchParams.set('lon', lon);
    if (zoom) url.searchParams.set('zoom', zoom);

    window.history.replaceState({}, '', url.pathname + url.search);
  }
}
