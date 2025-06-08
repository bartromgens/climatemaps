export interface ClimateVariableResource {
  name: string;
  display_name: string;
  unit: string;
}

export interface ClimateMapResource {
  year: number;
  year_range: [number, number];
  variable: ClimateVariableResource
  resolution: string;
  tiles_url: URL;
  colormap_url: URL;
  max_zoom_raster: number;
  max_zoom_vector: number;
  source: string;
}

export class ClimateMap {
  constructor(
    public year: number,
    public yearRange: [number, number],
    public variable: ClimateVariable,
    public resolution: string,
    public tilesUrl: URL,
    public colormapUrl: URL,
    public maxZoomRaster: number,
    public maxZoomVector: number,
    public source: string,
  ) {
  }

  static fromResource(resource: ClimateMapResource): ClimateMap {
    return new ClimateMap(
      Number(resource.year),
      resource.year_range,
      ClimateVariable.fromResource(resource.variable),
      resource.resolution,
      resource.tiles_url,
      resource.colormap_url,
      resource.max_zoom_raster,
      resource.max_zoom_vector,
      resource.source,
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
  ) {
  }

  static fromResource(resource: ClimateVariableResource): ClimateVariable {
    return new ClimateVariable(
      resource.name,
      resource.display_name,
      resource.unit
    );
  }
}
