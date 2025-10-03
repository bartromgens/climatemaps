import { Injectable } from '@angular/core';
import { ClimateMap } from '../../core/climatemap';

export interface LayerOption {
  name: string;
  rasterUrl: string;
  vectorUrl: string;
  rasterMaxZoom: number;
  vectorMaxZoom: number;
  metadata?: {
    dataType: string;
    yearRange: [number, number];
    resolution: string;
    climateModel: string | null;
    climateScenario: string | null;
    variableType: string;
    isDifferenceMap: boolean;
  };
  climateMap?: ClimateMap;
}

@Injectable({
  providedIn: 'root',
})
export class LayerBuilderService {
  buildLayerOptions(climateMaps: ClimateMap[]): LayerOption[] {
    const layerOptions: LayerOption[] = [];

    for (const climateMap of climateMaps) {
      let displayName = `${climateMap.variable.displayName} (${climateMap.variable.unit})`;

      if (climateMap.climateModel && climateMap.climateScenario) {
        displayName += ` - ${climateMap.climateModel} ${climateMap.climateScenario}`;
      }

      layerOptions.push({
        name: displayName,
        rasterUrl: `${climateMap.tilesUrl}_raster`,
        vectorUrl: `${climateMap.tilesUrl}_vector`,
        rasterMaxZoom: climateMap.maxZoomRaster,
        vectorMaxZoom: climateMap.maxZoomVector,
        metadata: {
          dataType: climateMap.dataType,
          yearRange: climateMap.yearRange,
          resolution: climateMap.resolution,
          climateModel: climateMap.climateModel,
          climateScenario: climateMap.climateScenario,
          variableType: climateMap.variable.name,
          isDifferenceMap: climateMap.isDifferenceMap,
        },
        climateMap: climateMap,
      });
    }

    return layerOptions;
  }
}
