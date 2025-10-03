import { Component, OnInit } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { FormsModule } from '@angular/forms';
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
  Tooltip,
} from 'leaflet';
import 'leaflet.vectorgrid'; // bring in the vectorgrid plugin

import { environment } from '../../environments/environment';
import { MonthSliderComponent } from './month-slider.component';
import { YearSliderComponent } from './year-slider.component';
import {
  MapControlsComponent,
  MapControlsData,
  MapControlsOptions,
} from './map-controls.component';
import { ColorbarComponent } from './colorbar.component';
import {
  ClimateMapService,
  ClimateValueResponse,
} from '../core/climatemap.service';
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
    isDifferenceMap: boolean;
  };
  climateMap?: ClimateMap;
}

@Component({
  selector: 'app-map',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    LeafletModule,
    MatIconModule,
    MatSidenavModule,
    MatButtonModule,
    MatCardModule,
    MonthSliderComponent,
    YearSliderComponent,
    MapControlsComponent,
    ColorbarComponent,
  ],
  templateUrl: './map.component.html',
  styleUrl: './map.component.scss',
})
export class MapComponent implements OnInit {
  private readonly ZOOM_DEFAULT: number = 5;
  layerOptions: LayerOption[] = [];
  selectedOption: LayerOption | undefined;
  monthSelected = 1;

  // Climate maps data from backend
  climateMaps: ClimateMap[] = [];

  // Controls data for the MapControlsComponent
  controlsData: MapControlsData = {
    selectedVariableType: ClimateVarKey.T_MAX,
    selectedYearRange: null,
    selectedResolution: SpatialResolution.MIN10,
    selectedClimateScenario: null,
    selectedClimateModel: null,
    showDifferenceMap: false,
  };

  // Controls options for the MapControlsComponent
  controlsOptions!: MapControlsOptions;

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
    if (!this.controlsData.selectedYearRange && this.yearRanges.length > 0) {
      this.controlsData.selectedYearRange = this.yearRanges[0];
    }

    // Initialize controls options
    this.controlsOptions = {
      variableTypes: this.variableTypes,
      yearRanges: this.yearRanges,
      resolutions: this.resolutions,
      climateScenarios: this.climateScenarios,
      climateModels: this.climateModels,
      climateVariables: this.climateVariables,
      availableVariableTypes: this.getAvailableVariableTypes(),
      availableYearRanges: this.getAvailableYearRanges(),
      availableResolutions: this.getAvailableResolutions(),
      availableClimateScenarios: this.getAvailableClimateScenarios(),
      availableClimateModels: this.getAvailableClimateModels(),
      isHistoricalYearRange: this.isHistoricalYearRange,
    };
  }

  // Method to handle controls changes from MapControlsComponent
  onControlsChange(newControlsData: MapControlsData): void {
    this.controlsData = { ...newControlsData };
    this.handleControlsChange();
  }

  private handleControlsChange(): void {
    // Reset climate scenario and model for historical data
    if (
      this.controlsData.selectedYearRange &&
      this.isHistoricalYearRange(this.controlsData.selectedYearRange.value)
    ) {
      this.controlsData.selectedClimateScenario = null;
      this.controlsData.selectedClimateModel = null;
    } else {
      // Set default values for future data if not already set
      if (!this.controlsData.selectedClimateScenario) {
        this.controlsData.selectedClimateScenario = ClimateScenario.SSP126;
      }
      if (!this.controlsData.selectedClimateModel) {
        this.controlsData.selectedClimateModel = ClimateModel.EC_EARTH3_VEG;
      }
    }

    this.resetInvalidSelections();
    this.findMatchingLayer();
    this.updateLayers();
  }

  // Computed properties for filtering available options based on actual data
  private getAvailableVariableTypes(): ClimateVarKey[] {
    return this.variableTypes.filter((variableType) => {
      return this.climateMaps.some(
        (map) =>
          map.variable.name === this.climateVariables[variableType]?.name,
      );
    });
  }

  private getAvailableYearRanges(): YearRange[] {
    return this.yearRanges.filter((yearRange) => {
      return this.climateMaps.some(
        (map) =>
          map.yearRange[0] === yearRange.value[0] &&
          map.yearRange[1] === yearRange.value[1] &&
          map.variable.name ===
            this.climateVariables[this.controlsData.selectedVariableType]
              ?.name &&
          map.isDifferenceMap === this.controlsData.showDifferenceMap,
      );
    });
  }

  private getAvailableResolutions(): SpatialResolution[] {
    if (!this.controlsData.selectedYearRange) return [];

    // First, get all maps that match the current variable type and year range
    const matchingMaps = this.climateMaps.filter(
      (map) =>
        map.variable.name ===
          this.climateVariables[this.controlsData.selectedVariableType]?.name &&
        map.yearRange[0] === this.controlsData.selectedYearRange!.value[0] &&
        map.yearRange[1] === this.controlsData.selectedYearRange!.value[1] &&
        map.isDifferenceMap === this.controlsData.showDifferenceMap,
    );

    // For future data, further filter by climate scenario and model if selected
    let filteredMaps = matchingMaps;
    if (
      !this.isHistoricalYearRange(this.controlsData.selectedYearRange!.value)
    ) {
      if (this.controlsData.selectedClimateScenario) {
        filteredMaps = filteredMaps.filter(
          (map) =>
            map.climateScenario === this.controlsData.selectedClimateScenario,
        );
      }
      if (this.controlsData.selectedClimateModel) {
        filteredMaps = filteredMaps.filter(
          (map) => map.climateModel === this.controlsData.selectedClimateModel,
        );
      }
    }

    // Get unique resolutions from the filtered maps
    const availableResolutions = this.resolutions.filter((resolution) =>
      filteredMaps.some((map) => map.resolution === resolution),
    );

    return availableResolutions;
  }

  private getAvailableClimateScenarios(): ClimateScenario[] {
    // Only show climate scenarios for future data or difference maps
    if (
      !this.controlsData.selectedYearRange ||
      (this.isHistoricalYearRange(this.controlsData.selectedYearRange.value) &&
        !this.controlsData.showDifferenceMap)
    ) {
      return [];
    }

    // Get all maps that match the current variable type and year range
    const matchingMaps = this.climateMaps.filter(
      (map) =>
        map.variable.name ===
          this.climateVariables[this.controlsData.selectedVariableType]?.name &&
        map.yearRange[0] === this.controlsData.selectedYearRange!.value[0] &&
        map.yearRange[1] === this.controlsData.selectedYearRange!.value[1] &&
        map.isDifferenceMap === this.controlsData.showDifferenceMap,
    );

    // Get unique climate scenarios from the matching maps
    const availableScenarios = this.climateScenarios.filter((scenario) =>
      matchingMaps.some((map) => map.climateScenario === scenario),
    );

    return availableScenarios;
  }

  private getAvailableClimateModels(): ClimateModel[] {
    // Only show climate models for future data or difference maps
    if (
      !this.controlsData.selectedYearRange ||
      (this.isHistoricalYearRange(this.controlsData.selectedYearRange.value) &&
        !this.controlsData.showDifferenceMap)
    ) {
      return [];
    }

    // Get all maps that match the current variable type and year range
    const matchingMaps = this.climateMaps.filter(
      (map) =>
        map.variable.name ===
          this.climateVariables[this.controlsData.selectedVariableType]?.name &&
        map.yearRange[0] === this.controlsData.selectedYearRange!.value[0] &&
        map.yearRange[1] === this.controlsData.selectedYearRange!.value[1] &&
        map.isDifferenceMap === this.controlsData.showDifferenceMap,
    );

    // Further filter by climate scenario if selected
    let filteredMaps = matchingMaps;
    if (this.controlsData.selectedClimateScenario) {
      filteredMaps = filteredMaps.filter(
        (map) =>
          map.climateScenario === this.controlsData.selectedClimateScenario,
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
  private hoverTooltip: Tooltip | null = null;
  private clickTooltip: Tooltip | null = null;
  private isLoadingClickValue = false;

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
        variableType: this.controlsData.selectedVariableType,
        yearRange: this.controlsData.selectedYearRange?.value,
        resolution: this.controlsData.selectedResolution,
        climateScenario: this.controlsData.selectedClimateScenario,
        climateModel: this.controlsData.selectedClimateModel,
        isHistorical: this.controlsData.selectedYearRange
          ? this.isHistoricalYearRange(
              this.controlsData.selectedYearRange.value,
            )
          : false,
      });
      this.findMatchingLayer();
      this.updateLayers();
    });
  }

  onLayerChange() {
    this.updateLayers();
  }

  private resetInvalidSelections() {
    const availableYearRanges = this.getAvailableYearRanges();
    const availableResolutions = this.getAvailableResolutions();
    const availableClimateScenarios = this.getAvailableClimateScenarios();
    const availableClimateModels = this.getAvailableClimateModels();

    // Reset year range if not available for current selections
    if (
      this.controlsData.selectedYearRange &&
      !availableYearRanges.includes(this.controlsData.selectedYearRange)
    ) {
      this.controlsData.selectedYearRange = availableYearRanges[0] || null;
    }

    // Reset resolution if not available for current selections
    if (!availableResolutions.includes(this.controlsData.selectedResolution)) {
      this.controlsData.selectedResolution =
        availableResolutions[0] || SpatialResolution.MIN10;
    }

    // Reset climate scenario if not available for current selections
    if (
      this.controlsData.selectedClimateScenario &&
      !availableClimateScenarios.includes(
        this.controlsData.selectedClimateScenario,
      )
    ) {
      this.controlsData.selectedClimateScenario =
        availableClimateScenarios[0] || null;
    }

    // Reset climate model if not available for current selections
    if (
      this.controlsData.selectedClimateModel &&
      !availableClimateModels.includes(this.controlsData.selectedClimateModel)
    ) {
      this.controlsData.selectedClimateModel =
        availableClimateModels[0] || null;
    }

    // Update controls options with fresh data
    this.updateControlsOptions();
  }

  private updateControlsOptions(): void {
    this.controlsOptions = {
      ...this.controlsOptions,
      availableVariableTypes: this.getAvailableVariableTypes(),
      availableYearRanges: this.getAvailableYearRanges(),
      availableResolutions: this.getAvailableResolutions(),
      availableClimateScenarios: this.getAvailableClimateScenarios(),
      availableClimateModels: this.getAvailableClimateModels(),
    };
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
          isDifferenceMap: climateMap.isDifferenceMap,
        },
        // Store the full ClimateMap object for colorbar access
        climateMap: climateMap,
      });
    }
    return layerOptions;
  }

  private findMatchingLayer() {
    console.log('Finding matching layer for:', {
      variableType: this.controlsData.selectedVariableType,
      yearRange: this.controlsData.selectedYearRange,
      resolution: this.controlsData.selectedResolution,
    });

    // Find the layer that matches the current selections
    const matchingLayer = this.layerOptions.find((option) => {
      if (!option.metadata) {
        return false;
      }

      const metadata = option.metadata;

      // Check if the variable type matches
      const expectedVariableName =
        this.climateVariables[this.controlsData.selectedVariableType]?.name;
      if (metadata.variableType !== expectedVariableName) {
        return false;
      }

      // Check if the year range matches
      if (
        metadata.yearRange[0] !==
          this.controlsData.selectedYearRange!.value[0] ||
        metadata.yearRange[1] !== this.controlsData.selectedYearRange!.value[1]
      ) {
        return false;
      }

      // Check if the resolution matches
      if (metadata.resolution !== this.controlsData.selectedResolution) {
        return false;
      }

      // Check if difference map status matches
      if (metadata.isDifferenceMap !== this.controlsData.showDifferenceMap) {
        return false;
      }

      // For future data, check climate scenario and model
      if (
        !this.isHistoricalYearRange(this.controlsData.selectedYearRange!.value)
      ) {
        if (
          this.controlsData.selectedClimateScenario &&
          metadata.climateScenario !== this.controlsData.selectedClimateScenario
        ) {
          return false;
        }
        if (
          this.controlsData.selectedClimateModel &&
          metadata.climateModel !== this.controlsData.selectedClimateModel
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
    // Clean up hover tooltip
    if (this.hoverTooltip) {
      this.map?.removeLayer(this.hoverTooltip);
      this.hoverTooltip = null;
    }
    // Clean up click tooltip
    if (this.clickTooltip) {
      this.map?.removeLayer(this.clickTooltip);
      this.clickTooltip = null;
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

      // Add hover event listeners
      this.vectorLayer?.on('mouseover', (e: any) => {
        this.onVectorLayerHover(e);
      });

      this.vectorLayer?.on('mouseout', () => {
        this.onVectorLayerMouseOut();
      });

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

  private normalizeLongitude(lon: number): number {
    // Normalize longitude to -180 to 180 range
    while (lon > 180) {
      lon -= 360;
    }
    while (lon < -180) {
      lon += 360;
    }
    return lon;
  }

  onMapClick(event: LeafletMouseEvent): void {
    console.log('mapClick', event);

    if (!this.selectedOption?.metadata?.dataType) {
      console.log('No layer selected, skipping click handler');
      return;
    }

    const lat = event.latlng.lat;
    const lon = this.normalizeLongitude(event.latlng.lng);

    // Remove existing click tooltip
    if (this.clickTooltip) {
      this.map?.removeLayer(this.clickTooltip);
      this.clickTooltip = null;
    }

    // Show loading tooltip
    this.isLoadingClickValue = true;
    this.clickTooltip = new Tooltip({
      content: 'Loading...',
      className: 'click-value-tooltip',
      direction: 'top',
      offset: [0, -10],
      opacity: 0.95,
      permanent: true,
    });
    this.clickTooltip.setLatLng(event.latlng);
    this.clickTooltip.addTo(this.map!);

    // Fetch climate value from API
    this.climateMapService
      .getClimateValue(
        this.selectedOption.metadata.dataType,
        this.monthSelected,
        lat,
        lon,
      )
      .subscribe({
        next: (response: ClimateValueResponse) => {
          this.isLoadingClickValue = false;
          this.displayClickValue(event.latlng, response);
        },
        error: (error) => {
          this.isLoadingClickValue = false;
          console.error('Error fetching climate value:', error);

          // Show error message in tooltip
          if (this.clickTooltip) {
            this.map?.removeLayer(this.clickTooltip);
          }

          const errorMessage = error.error?.detail || 'Error loading value';
          this.clickTooltip = new Tooltip({
            content: `<div style="color: #ff5252;">${errorMessage}</div>`,
            className: 'click-value-tooltip error',
            direction: 'top',
            offset: [0, -10],
            opacity: 0.95,
            permanent: true,
          });
          this.clickTooltip.setLatLng(event.latlng);
          this.clickTooltip.addTo(this.map!);
        },
      });
  }

  private displayClickValue(latlng: any, response: ClimateValueResponse): void {
    // Remove existing click tooltip
    if (this.clickTooltip) {
      this.map?.removeLayer(this.clickTooltip);
    }

    // Format the value display
    const content = `
      <div class="climate-value-popup">
        <div class="value-main">${response.value.toFixed(2)} ${response.unit}</div>
        <div class="value-details">
          <div>Location: ${response.latitude.toFixed(4)}°, ${response.longitude.toFixed(4)}°</div>
        </div>
      </div>
    `;

    // Create persistent tooltip with the value
    this.clickTooltip = new Tooltip({
      content: content,
      className: 'click-value-tooltip',
      direction: 'top',
      offset: [0, -10],
      opacity: 0.95,
      permanent: true,
    });
    this.clickTooltip.setLatLng(latlng);
    this.clickTooltip.addTo(this.map!);
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

  private onVectorLayerHover(e: any): void {
    const properties = e.layer?.properties;
    if (properties && properties['level-value'] !== undefined) {
      const value = properties['level-value'];
      const unit = this.getCurrentUnit();
      const displayValue = `${value.toFixed(1)} ${unit}`;

      // Remove existing tooltip
      if (this.hoverTooltip) {
        this.map?.removeLayer(this.hoverTooltip);
      }

      // Create new tooltip
      this.hoverTooltip = new Tooltip({
        content: displayValue,
        className: 'contour-hover-tooltip',
        direction: 'top',
        offset: [0, -10],
        opacity: 0.9,
      });

      // Bind tooltip to the layer and open it
      this.hoverTooltip.setLatLng(e.latlng);
      this.hoverTooltip.addTo(this.map!);
    }
  }

  private onVectorLayerMouseOut(): void {
    if (this.hoverTooltip) {
      this.map?.removeLayer(this.hoverTooltip);
      this.hoverTooltip = null;
    }
  }

  private getCurrentUnit(): string {
    if (!this.selectedOption?.metadata) {
      return '';
    }

    const climateVariable =
      this.climateVariables[this.controlsData.selectedVariableType];

    if (climateVariable?.unit) {
      return climateVariable.unit;
    }
    return 'unknown';
  }
}
