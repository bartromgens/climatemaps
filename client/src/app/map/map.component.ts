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
import { TooltipManagerService } from './services/tooltip-manager.service';
import {
  LayerBuilderService,
  LayerOption,
} from './services/layer-builder.service';
import { LayerFilterService } from './services/layer-filter.service';

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
    return this.layerFilter.getAvailableVariableTypes(
      this.climateMaps,
      this.variableTypes,
      this.climateVariables,
    );
  }

  private getAvailableYearRanges(): YearRange[] {
    return this.layerFilter.getAvailableYearRanges(
      this.climateMaps,
      this.yearRanges,
      this.controlsData,
      this.climateVariables,
    );
  }

  private getAvailableResolutions(): SpatialResolution[] {
    return this.layerFilter.getAvailableResolutions(
      this.climateMaps,
      this.resolutions,
      this.controlsData,
      this.climateVariables,
      this.isHistoricalYearRange,
    );
  }

  private getAvailableClimateScenarios(): ClimateScenario[] {
    return this.layerFilter.getAvailableClimateScenarios(
      this.climateMaps,
      this.climateScenarios,
      this.controlsData,
      this.climateVariables,
      this.isHistoricalYearRange,
    );
  }

  private getAvailableClimateModels(): ClimateModel[] {
    return this.layerFilter.getAvailableClimateModels(
      this.climateMaps,
      this.climateModels,
      this.controlsData,
      this.climateVariables,
      this.isHistoricalYearRange,
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
  private rasterLayer: Layer | null = null;
  private vectorLayer: Layer | null = null;
  private isLoadingClickValue = false;

  constructor(
    private route: ActivatedRoute,
    private location: Location,
    private climateMapService: ClimateMapService,
    private metadataService: MetadataService,
    private tooltipManager: TooltipManagerService,
    private layerBuilder: LayerBuilderService,
    private layerFilter: LayerFilterService,
  ) {
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

      this.layerOptions = this.layerBuilder.buildLayerOptions(climateMaps);
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
    // Clean up tooltips
    if (this.map) {
      this.tooltipManager.removeAllTooltips(this.map);
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
    while (lon > 180) lon -= 360;
    while (lon < -180) lon += 360;
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

    // Show loading tooltip
    this.isLoadingClickValue = true;
    this.tooltipManager.createPersistentTooltip(
      '...',
      event.latlng,
      this.map!,
    );

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

          const errorMessage = error.error?.detail || 'Error loading value';
          this.tooltipManager.createPersistentTooltip(
            errorMessage,
            event.latlng,
            this.map!,
          );
        },
      });
  }

  private displayClickValue(latlng: any, response: ClimateValueResponse): void {
    const displayValue = `${response.value.toFixed(1)} ${response.unit}`;
    this.tooltipManager.createPersistentTooltip(
      displayValue,
      latlng,
      this.map!,
    );
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
    if (properties && properties['level-value'] !== undefined && this.map) {
      const value = properties['level-value'];
      const unit = this.getCurrentUnit();
      const displayValue = `${value.toFixed(1)} ${unit}`;
      this.tooltipManager.createHoverTooltip(displayValue, e.latlng, this.map);
    }
  }

  private onVectorLayerMouseOut(): void {
    if (this.map) {
      this.tooltipManager.removeHoverTooltip(this.map);
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
