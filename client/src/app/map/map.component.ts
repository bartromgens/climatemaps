import { Component, OnInit } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';

import { LeafletModule } from '@bluehalo/ngx-leaflet';
import {
  Control,
  latLng,
  Layer,
  LeafletEvent,
  LeafletMouseEvent,
  Map,
  tileLayer,
} from 'leaflet';
import 'leaflet.vectorgrid'; // bring in the vectorgrid plugin

import { environment } from '../../environments/environment';
import { MonthSliderComponent } from './month-slider.component';
import { YearSliderComponent } from './year-slider.component';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { ClimateMapService } from '../core/climatemap.service';
import { ClimateMap } from '../core/climatemap';
import {
  MetadataService,
  ClimateVariableConfig,
  YearRange,
} from '../core/metadata.service';
import {
  ClimateVarKey,
  SpatialResolution,
  ClimateScenario,
  ClimateModel,
} from '../utils/enum';

interface LayerOption {
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
  };
}

@Component({
  selector: 'app-map',
  standalone: true,
  imports: [
    CommonModule,
    LeafletModule,
    MatIconModule,
    MatSidenavModule,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatSelectModule,
    MonthSliderComponent,
    YearSliderComponent,
  ],
  templateUrl: './map.component.html',
  styleUrl: './map.component.scss',
})
export class MapComponent implements OnInit {
  private readonly ZOOM_DEFAULT: number = 5;
  layerOptions: LayerOption[] = [];
  selectedOption: LayerOption | undefined;
  private monthSelected = 1;

  // Climate maps data from backend
  climateMaps: ClimateMap[] = [];

  // Dropdown selections
  selectedVariableType: ClimateVarKey = ClimateVarKey.PRECIPITATION;
  selectedYearRange: YearRange | null = null;
  selectedResolution: SpatialResolution = SpatialResolution.MIN10;
  selectedClimateScenario: ClimateScenario | null = null;
  selectedClimateModel: ClimateModel | null = null;

  // Available options for dropdowns (populated from API data)
  variableTypes: ClimateVarKey[] = [];
  yearRanges: YearRange[] = [];
  resolutions: SpatialResolution[] = [];
  climateScenarios: ClimateScenario[] = [];
  climateModels: ClimateModel[] = [];

  // Helper properties
  climateVariables: Record<ClimateVarKey, ClimateVariableConfig> = {} as Record<
    ClimateVarKey,
    ClimateVariableConfig
  >;
  isHistoricalYearRange!: (yearRange: readonly [number, number]) => boolean;

  // Populate metadata from API data
  private populateMetadataFromAPI(climateMaps: ClimateMap[]): void {
    this.climateVariables =
      this.metadataService.getClimateVariables(climateMaps);
    this.yearRanges = this.metadataService.getYearRanges(climateMaps);
    this.resolutions = this.metadataService.getResolutions(climateMaps);
    this.climateScenarios =
      this.metadataService.getClimateScenarios(climateMaps);
    this.climateModels = this.metadataService.getClimateModels(climateMaps);

    // Set variable types from the climate variables
    this.variableTypes = Object.keys(this.climateVariables) as ClimateVarKey[];

    // Set default year range if none selected
    if (!this.selectedYearRange && this.yearRanges.length > 0) {
      this.selectedYearRange = this.yearRanges[0];
    }
  }

  // Computed properties for filtering available options based on actual data
  get availableVariableTypes() {
    return this.variableTypes.filter((variableType) => {
      return this.climateMaps.some(
        (map) =>
          map.variable.name === this.climateVariables[variableType]?.name,
      );
    });
  }

  get availableYearRanges() {
    return this.yearRanges.filter((yearRange) => {
      return this.climateMaps.some(
        (map) =>
          map.yearRange[0] === yearRange.value[0] &&
          map.yearRange[1] === yearRange.value[1] &&
          map.variable.name ===
            this.climateVariables[this.selectedVariableType]?.name,
      );
    });
  }

  get availableResolutions() {
    if (!this.selectedYearRange) return [];

    // First, get all maps that match the current variable type and year range
    const matchingMaps = this.climateMaps.filter(
      (map) =>
        map.variable.name ===
          this.climateVariables[this.selectedVariableType]?.name &&
        map.yearRange[0] === this.selectedYearRange!.value[0] &&
        map.yearRange[1] === this.selectedYearRange!.value[1],
    );

    // For future data, further filter by climate scenario and model if selected
    let filteredMaps = matchingMaps;
    if (!this.isHistoricalYearRange(this.selectedYearRange!.value)) {
      if (this.selectedClimateScenario) {
        filteredMaps = filteredMaps.filter(
          (map) => map.climateScenario === this.selectedClimateScenario,
        );
      }
      if (this.selectedClimateModel) {
        filteredMaps = filteredMaps.filter(
          (map) => map.climateModel === this.selectedClimateModel,
        );
      }
    }

    // Get unique resolutions from the filtered maps
    const availableResolutions = this.resolutions.filter((resolution) =>
      filteredMaps.some((map) => map.resolution === resolution),
    );

    return availableResolutions;
  }

  get availableClimateScenarios() {
    // Only show climate scenarios for future data
    if (
      !this.selectedYearRange ||
      this.isHistoricalYearRange(this.selectedYearRange.value)
    ) {
      return [];
    }

    // Get all maps that match the current variable type and year range
    const matchingMaps = this.climateMaps.filter(
      (map) =>
        map.variable.name ===
          this.climateVariables[this.selectedVariableType]?.name &&
        map.yearRange[0] === this.selectedYearRange!.value[0] &&
        map.yearRange[1] === this.selectedYearRange!.value[1],
    );

    // Get unique climate scenarios from the matching maps
    const availableScenarios = this.climateScenarios.filter((scenario) =>
      matchingMaps.some((map) => map.climateScenario === scenario),
    );

    return availableScenarios;
  }

  get availableClimateModels() {
    // Only show climate models for future data
    if (
      !this.selectedYearRange ||
      this.isHistoricalYearRange(this.selectedYearRange.value)
    ) {
      return [];
    }

    // Get all maps that match the current variable type and year range
    const matchingMaps = this.climateMaps.filter(
      (map) =>
        map.variable.name ===
          this.climateVariables[this.selectedVariableType]?.name &&
        map.yearRange[0] === this.selectedYearRange!.value[0] &&
        map.yearRange[1] === this.selectedYearRange!.value[1],
    );

    // Further filter by climate scenario if selected
    let filteredMaps = matchingMaps;
    if (this.selectedClimateScenario) {
      filteredMaps = filteredMaps.filter(
        (map) => map.climateScenario === this.selectedClimateScenario,
      );
    }

    // Get unique climate models from the filtered maps
    return this.climateModels.filter((model) =>
      filteredMaps.some((map) => map.climateModel === model),
    );
  }

  Object = Object;
  private baseLayer = tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    {
      maxZoom: 20,
      attribution: '...',
    },
  );
  options = {
    layers: [this.baseLayer],
    zoom: this.ZOOM_DEFAULT,
    center: latLng(52.1, 5.58),
  };
  sidebarOpened = false;
  debug = !environment.production;

  private map: Map | null = null;
  private readonly control: Control.Layers;
  private rasterLayer: Layer | null = null;
  private vectorLayer: Layer | null = null;

  constructor(
    private route: ActivatedRoute,
    private location: Location,
    private climateMapService: ClimateMapService,
    private metadataService: MetadataService,
  ) {
    this.control = new Control.Layers(undefined, undefined, {
      collapsed: false,
    });
    this.isHistoricalYearRange =
      this.metadataService.isHistoricalYearRange.bind(this.metadataService);
  }

  ngOnInit(): void {
    this.route.queryParamMap.subscribe((params) => {
      if (params.has('lat') && params.has('lon') && params.has('zoom')) {
        this.updateLocationZoomFromURL(params);
      }
    });
    this.climateMapService.getClimateMapList().subscribe((climateMaps) => {
      console.log('Loaded climate maps:', climateMaps.length);
      this.climateMaps = climateMaps;

      // Populate metadata from API data
      this.populateMetadataFromAPI(climateMaps);

      this.layerOptions = this.buildLayerOptions(climateMaps);
      console.log('Built layer options:', this.layerOptions.length);

      // Reset selections to ensure they are available
      this.resetInvalidSelections();

      console.log('Initial selections:', {
        variableType: this.selectedVariableType,
        yearRange: this.selectedYearRange?.value,
        resolution: this.selectedResolution,
        climateScenario: this.selectedClimateScenario,
        climateModel: this.selectedClimateModel,
        isHistorical: this.selectedYearRange
          ? this.isHistoricalYearRange(this.selectedYearRange.value)
          : false,
      });
      this.findMatchingLayer();
      this.updateLayers();
    });
  }

  onLayerChange() {
    this.updateLayers();
  }

  onVariableTypeChange() {
    this.resetInvalidSelections();
    this.findMatchingLayer();
    this.updateLayers();
  }

  onYearRangeChange() {
    // Reset climate scenario and model for historical data
    if (
      this.selectedYearRange &&
      this.isHistoricalYearRange(this.selectedYearRange.value)
    ) {
      this.selectedClimateScenario = null;
      this.selectedClimateModel = null;
    } else {
      // Set default values for future data if not already set
      if (!this.selectedClimateScenario) {
        this.selectedClimateScenario = ClimateScenario.SSP126;
      }
      if (!this.selectedClimateModel) {
        this.selectedClimateModel = ClimateModel.EC_EARTH3_VEG;
      }
    }
    this.resetInvalidSelections();
    this.findMatchingLayer();
    this.updateLayers();
  }

  onResolutionChange() {
    this.resetInvalidSelections();
    this.findMatchingLayer();
    this.updateLayers();
  }

  onClimateScenarioChange() {
    this.resetInvalidSelections();
    this.findMatchingLayer();
    this.updateLayers();
  }

  onClimateModelChange() {
    this.findMatchingLayer();
    this.updateLayers();
  }

  private resetInvalidSelections() {
    // Reset year range if not available for current selections
    if (
      this.selectedYearRange &&
      !this.availableYearRanges.includes(this.selectedYearRange)
    ) {
      this.selectedYearRange = this.availableYearRanges[0] || null;
    }

    // Reset resolution if not available for current selections
    if (!this.availableResolutions.includes(this.selectedResolution)) {
      this.selectedResolution =
        this.availableResolutions[0] || SpatialResolution.MIN10;
    }

    // Reset climate scenario if not available for current selections
    if (
      this.selectedClimateScenario &&
      !this.availableClimateScenarios.includes(this.selectedClimateScenario)
    ) {
      this.selectedClimateScenario = this.availableClimateScenarios[0] || null;
    }

    // Reset climate model if not available for current selections
    if (
      this.selectedClimateModel &&
      !this.availableClimateModels.includes(this.selectedClimateModel)
    ) {
      this.selectedClimateModel = this.availableClimateModels[0] || null;
    }
  }

  private buildLayerOptions(climateMaps: any[]): LayerOption[] {
    const layerOptions: LayerOption[] = [];
    for (const climateMap of climateMaps) {
      let displayName = `${climateMap.variable.displayName} (${climateMap.variable.unit})`;

      // Add climate model and scenario information if available
      if (climateMap.climateModel && climateMap.climateScenario) {
        displayName += ` - ${climateMap.climateModel} ${climateMap.climateScenario}`;
      }

      layerOptions.push({
        name: displayName,
        rasterUrl: `${climateMap.tilesUrl}_raster`,
        vectorUrl: `${climateMap.tilesUrl}_vector`,
        rasterMaxZoom: climateMap.maxZoomRaster,
        vectorMaxZoom: climateMap.maxZoomVector,
        // Store additional metadata for better matching
        metadata: {
          dataType: climateMap.dataType,
          yearRange: climateMap.yearRange,
          resolution: climateMap.resolution,
          climateModel: climateMap.climateModel,
          climateScenario: climateMap.climateScenario,
          variableType: climateMap.variable.name,
        },
      });
    }
    return layerOptions;
  }

  private findMatchingLayer() {
    console.log('Finding matching layer for:', {
      variableType: this.selectedVariableType,
      yearRange: this.selectedYearRange,
      resolution: this.selectedResolution,
    });

    // Find the layer that matches the current selections
    const matchingLayer = this.layerOptions.find((option) => {
      if (!option.metadata) {
        return false;
      }

      const metadata = option.metadata;

      // Check if the variable type matches
      const expectedVariableName =
        this.climateVariables[this.selectedVariableType]?.name;
      if (metadata.variableType !== expectedVariableName) {
        return false;
      }

      // Check if the year range matches
      if (
        metadata.yearRange[0] !== this.selectedYearRange!.value[0] ||
        metadata.yearRange[1] !== this.selectedYearRange!.value[1]
      ) {
        return false;
      }

      // Check if the resolution matches
      if (metadata.resolution !== this.selectedResolution) {
        return false;
      }

      // For future data, check climate scenario and model
      if (!this.isHistoricalYearRange(this.selectedYearRange!.value)) {
        if (
          this.selectedClimateScenario &&
          metadata.climateScenario !== this.selectedClimateScenario
        ) {
          return false;
        }
        if (
          this.selectedClimateModel &&
          metadata.climateModel !== this.selectedClimateModel
        ) {
          return false;
        }
      } else {
        // For historical data, ensure no climate scenario or model is set
        if (metadata.climateScenario || metadata.climateModel) {
          return false;
        }
      }

      return true;
    });

    if (matchingLayer) {
      this.selectedOption = matchingLayer;
      console.log('Found matching layer:', matchingLayer.name);
    } else {
      // No exact match found - clear current layer
      this.selectedOption = undefined;
      console.log(
        'No exact match found for current selections - clearing current layer',
      );
      // Remove any existing layers from the map
      this.removeCurrentLayers();
    }
  }

  private initializeMap(): void {
    console.log('initializeMap');
    if (!this.map) {
      console.assert(false, 'map is not defined');
      return;
    }
    this.update();
    this.addControls();
  }

  private removeCurrentLayers(): void {
    if (this.rasterLayer) {
      console.log('remove raster layer');
      this.map?.removeLayer(this.rasterLayer);
      this.rasterLayer = null;
    }
    if (this.vectorLayer) {
      console.log('remove vector layer');
      this.map?.removeLayer(this.vectorLayer);
      this.vectorLayer = null;
    }
  }

  private updateLayers(): void {
    console.log('initializeLayers selectedOption', this.selectedOption);

    // Remove existing layers first
    this.removeCurrentLayers();

    // Only add layers if a valid option is selected
    if (this.selectedOption) {
      this.rasterLayer = tileLayer(
        `${this.selectedOption.rasterUrl}_${this.monthSelected}/{z}/{x}/{y}.png`,
        {
          // attribution: '&copy; My Raster Tiles',
          minZoom: 0,
          maxNativeZoom: this.selectedOption.rasterMaxZoom,
          maxZoom: 12,
          tileSize: 256,
          opacity: 0.8,
          // tms: true, // uncomment if your MBTiles uses TMS y‐axis
        },
      );

      this.vectorLayer = (window as any).L.vectorGrid.protobuf(
        `${this.selectedOption.vectorUrl}_${this.monthSelected}/{z}/{x}/{y}.pbf`,
        {
          vectorTileLayerStyles: {
            contours: (properties: any) => ({
              color: properties.stroke,
              weight: 2,
              opacity: 1,
            }),
          },
          interactive: true,
          maxNativeZoom: this.selectedOption.vectorMaxZoom,
          maxZoom: 18,
        },
      );

      // Add new layers to map
      if (this.rasterLayer) {
        this.map?.addLayer(this.rasterLayer);
      }
      if (this.vectorLayer) {
        this.map?.addLayer(this.vectorLayer);
      }
    } else {
      console.log('No layer selected - not adding any layers to map');
    }
  }

  private addControls() {
    if (!this.map) {
      console.assert(false, 'map is not defined');
      return;
    }
    this.control.addTo(this.map);
    new Control.Scale().addTo(this.map);
  }

  private update(): void {
    console.log('update');
    if (!this.map) {
      console.assert(false, 'map is not defined');
      return;
    }
  }

  private updateLocationZoomFromURL(params: ParamMap) {
    const lat = Number(params.get('lat'));
    const lon = Number(params.get('lon'));
    const zoom = Number(params.get('zoom'));
    if (lat === null || lon === null || zoom === null) {
      return;
    }
    this.options.center = latLng(lat, lon);
    this.options.zoom = zoom;
    this.map?.setView([lat, lon], zoom);
  }

  onMapClick(event: LeafletMouseEvent): void {
    console.log('mapClick', event);
  }

  onMapReady(map: Map): void {
    this.map = map;
    this.initializeMap();
  }

  onMove(event: LeafletEvent): void {
    console.log('onMove', event);
    this.update();
    this.updateUrlWithLocationZoom();
  }

  onZoom(event: LeafletEvent): void {
    console.log('onZoom: level', this.map?.getZoom(), event);
    this.updateUrlWithLocationZoom();
  }

  private updateUrlWithLocationZoom(): void {
    if (!this.map) {
      return;
    }
    const center = this.map.getCenter();
    const zoom = this.map.getZoom();
    const url = new URL(window.location.href);
    url.searchParams.set('lat', center.lat.toFixed(6));
    url.searchParams.set('lon', center.lng.toFixed(6));
    url.searchParams.set('zoom', String(zoom));
    this.location.replaceState(url.pathname + url.search);
  }

  onMonthSelected(month: number): void {
    console.log('onMonthSelected', month);
    this.monthSelected = month;
    this.updateLayers();
  }

  trackByYearRange(index: number, yearRange: YearRange): string {
    return `${yearRange.value[0]}-${yearRange.value[1]}`;
  }
}
