import { ClimateModel, ClimateScenario } from '../utils/enum';

export interface ClimateVariableResource {
  name: string;
  display_name: string;
  unit: string;
}

export interface ClimateMapResource {
  data_type: string;
  year_range: [number, number];
  variable: ClimateVariableResource;
  resolution: string;
  tiles_url: string;
  colormap_url: string;
  max_zoom_raster: number;
  max_zoom_vector: number;
  source: string | null;
  climate_model: ClimateModel | null;
  climate_scenario: ClimateScenario | null;
}

export class ClimateMap {
  constructor(
    public dataType: string,
    public yearRange: [number, number],
    public variable: ClimateVariable,
    public resolution: string,
    public tilesUrl: string,
    public colormapUrl: string,
    public maxZoomRaster: number,
    public maxZoomVector: number,
    public source: string | null,
    public climateModel: ClimateModel | null = null,
    public climateScenario: ClimateScenario | null = null,
  ) {}

  static fromResource(resource: ClimateMapResource): ClimateMap {
    return new ClimateMap(
      resource.data_type,
      resource.year_range,
      ClimateVariable.fromResource(resource.variable),
      resource.resolution,
      resource.tiles_url,
      resource.colormap_url,
      resource.max_zoom_raster,
      resource.max_zoom_vector,
      resource.source,
      resource.climate_model,
      resource.climate_scenario,
    );
  }

  static fromResources(resources: ClimateMapResource[]): ClimateMap[] {
    return resources.map((resource) => ClimateMap.fromResource(resource));
  }
}

export class ClimateVariable {
  constructor(
    public name: string,
    public displayName: string,
    public unit: string,
  ) {}

  static fromResource(resource: ClimateVariableResource): ClimateVariable {
    return new ClimateVariable(
      resource.name,
      resource.display_name,
      resource.unit,
    );
  }
}
