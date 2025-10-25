import { Component, inject, OnInit, ViewChild } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatSnackBarModule } from '@angular/material/snack-bar';

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
import 'leaflet.vectorgrid';

import { environment } from '../../environments/environment';
import { MapControlsComponent } from './controls/map-controls.component';
import { VariableSelectorOverlayComponent } from './controls/variable-selector-overlay.component';
import { MobileDateControlOverlayComponent } from './controls/mobile-date-control-overlay.component';
import { ColorbarComponent } from './colorbar.component';
import { MobileHamburgerMenuComponent } from './controls/mobile-hamburger-menu.component';
import { ShowChangeToggleOverlayComponent } from './controls/show-change-toggle-overlay.component';
import { ContourToggleOverlayComponent } from './controls/contour-toggle-overlay.component';
import { ClimateMapService } from '../core/climatemap.service';
import { MetadataService, YearRange } from '../core/metadata.service';
import { SpatialResolution, ClimateVarKey } from '../utils/enum';
import { TooltipManagerService } from './services/tooltip-manager.service';
import { VectorLayerTooltipService } from './services/vector-layer-tooltip.service';
import { MapClickHandlerService } from './services/map-click-handler.service';
import {
  LayerBuilderService,
  LayerOption,
} from './services/layer-builder.service';
import { LayerFilterService } from './services/layer-filter.service';
import { URLUtils } from '../utils/url-utils';
import { ClimatePlotsComponent } from './plot/climate-plots.component';
import { MapNavigationService } from '../core/map-navigation.service';
import { MapSyncService } from './services/map-sync.service';
import { BaseMapComponent } from './base-map.component';
import { TemperatureUnitService } from '../core/temperature-unit.service';
import { SeoService } from '../core/seo.service';
import { ToastService } from '../core/toast.service';
import { ClimateVariableHelperService } from '../core/climate-variable-helper.service';
import { CoordinateUtils } from '../utils/coordinate-utils';
import { MatomoTracker } from 'ngx-matomo-client';
import {
  ColorExtractionService,
  ColorInfo,
} from './services/color-extraction.service';
import { ColorExtractionTestComponent } from './components/color-extraction-test.component';

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
    MatSnackBarModule,
    MapControlsComponent,
    VariableSelectorOverlayComponent,
    MobileDateControlOverlayComponent,
    ColorbarComponent,
    ClimatePlotsComponent,
    MobileHamburgerMenuComponent,
    ShowChangeToggleOverlayComponent,
    ContourToggleOverlayComponent,
    ColorExtractionTestComponent,
  ],
  templateUrl: './map.component.html',
  styleUrl: './map.component.scss',
})
export class MapComponent extends BaseMapComponent implements OnInit {
  @ViewChild('climatePlots') climatePlots!: ClimatePlotsComponent;

  private readonly tracker = inject(MatomoTracker);
  private readonly DEFAULT_RESOLUTION = SpatialResolution.MIN10;

  environment = environment;

  selectedOption: LayerOption | undefined;
  private previousVariableType: ClimateVarKey | null = null;

  get monthSelected(): number {
    return this.controlsData.selectedMonth;
  }

  protected initializeDefaultSelections(): void {
    if (!this.controlsData.selectedYearRange && this.yearRanges.length > 0) {
      this.controlsData.selectedYearRange = this.yearRanges[0];
    }
  }

  protected onControlsUpdated(): void {
    this.findMatchingLayer();
    this.updateLayers();
    this.climatePlots?.clearMobileState();
  }

  private checkAndShowFuturePredictionWarning(): void {
    const currentVariableType = this.controlsData.selectedVariableType;

    // Only show warning if variable has actually changed
    if (
      this.previousVariableType !== null &&
      this.previousVariableType !== currentVariableType
    ) {
      if (
        !this.climateVariableHelper.hasFuturePredictions(currentVariableType)
      ) {
        const variableDisplayName =
          this.climateVariables[currentVariableType]?.displayName ||
          currentVariableType;

        this.toastService.showInfo(
          `No future predictions available for ${variableDisplayName}`,
          6000,
        );
      }
    }

    // Update the previous variable type for next comparison
    this.previousVariableType = currentVariableType;
  }

  protected onDataLoaded(): void {
    this.checkAndShowFuturePredictionWarning();
    this.findMatchingLayer();
    this.updateLayers();
  }

  Object = Object;
  private baseLayer = tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    {
      maxZoom: 20,
      attribution: '...',
    },
  );
  options: any;
  debug = !environment.production;

  map: Map | null = null;
  private rasterLayer: Layer | null = null;
  private vectorLayer: Layer | null = null;
  plotData: { lat: number; lon: number; dataType: string } | null = null;
  timerangePlotData: { lat: number; lon: number; month: number } | null = null;
  showColorExtractionTest = false; // Set to true to enable color extraction testing

  constructor(
    route: ActivatedRoute,
    location: Location,
    climateMapService: ClimateMapService,
    metadataService: MetadataService,
    layerBuilder: LayerBuilderService,
    layerFilter: LayerFilterService,
    toastService: ToastService,
    mapSyncService: MapSyncService,
    private tooltipManager: TooltipManagerService,
    private vectorLayerTooltip: VectorLayerTooltipService,
    private mapClickHandler: MapClickHandlerService,
    private mapNavigationService: MapNavigationService,
    private temperatureUnitService: TemperatureUnitService,
    private seoService: SeoService,
    private climateVariableHelper: ClimateVariableHelperService,
    private colorExtractionService: ColorExtractionService,
  ) {
    super(
      route,
      location,
      climateMapService,
      metadataService,
      layerBuilder,
      layerFilter,
      toastService,
      mapSyncService,
    );

    const initialState = mapSyncService.getInitialViewState();
    this.options = {
      layers: [this.baseLayer],
      zoom: initialState.zoom,
      center: latLng(initialState.center.lat, initialState.center.lng),
      zoomControl: false,
    };
  }

  override ngOnInit(): void {
    this.checkMobile();
    this.setupResizeListener();
    this.setupNavigationListener();

    // Handle route data for variable-specific routes
    this.route.data.subscribe((data) => {
      if (data['variable'] && data['title']) {
        this.setVariableSpecificSEO(data['variable'], data['title']);
      } else {
        this.seoService.setDefaultMetaTags();
      }
    });

    this.route.queryParamMap.subscribe((params) => {
      if (params.has('lat') && params.has('lon') && params.has('zoom')) {
        this.updateLocationZoomFromURL(params);
      }
      if (this.climateMaps.length > 0) {
        this.updateControlsFromURL(params);
      }
    });

    this.climateMapService.getClimateMapList().subscribe({
      next: (climateMaps) => {
        console.log('Loaded climate maps:', climateMaps.length);
        this.climateMaps = climateMaps;

        this.populateMetadataFromAPI(climateMaps);
        this.layerOptions = this.layerBuilder.buildLayerOptions(climateMaps);
        console.log('Built layer options:', this.layerOptions.length);

        this.resetInvalidSelections();

        this.route.queryParamMap.subscribe((params) => {
          this.updateControlsFromURL(params);
        });

        // Handle route data for variable-specific routes
        this.route.data.subscribe((data) => {
          if (data['variable']) {
            const variableKey = data['variable'] as ClimateVarKey;
            if (this.variableTypes.includes(variableKey)) {
              this.controlsData.selectedVariableType = variableKey;
              this.onLayerChange();
            }
          }
        });

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
        this.onDataLoaded();
      },
      error: (error) => {
        console.error('Failed to load climate maps:', error);
        this.toastService.showError(
          'Failed to load climate data from backend. Please check your connection and try again.',
          10000,
        );
      },
    });
  }

  onLayerChange(): void {
    this.updateLayers();
  }

  protected resetInvalidSelections(): void {
    const availableYearRanges = this.getAvailableYearRanges();
    const availableResolutions = this.getAvailableResolutions();
    const availableClimateScenarios = this.getAvailableClimateScenarios();
    const availableClimateModels = this.getAvailableClimateModels();

    if (
      this.controlsData.selectedYearRange &&
      !this.isYearRangeAvailable(
        this.controlsData.selectedYearRange,
        availableYearRanges,
      )
    ) {
      this.controlsData.selectedYearRange = availableYearRanges[0] || null;
    }

    if (!availableResolutions.includes(this.controlsData.selectedResolution)) {
      this.controlsData.selectedResolution =
        availableResolutions[0] || this.DEFAULT_RESOLUTION;
    }

    const isFutureData =
      this.controlsData.selectedYearRange &&
      !this.isHistoricalYearRange(this.controlsData.selectedYearRange.value);

    if (isFutureData) {
      if (
        this.controlsData.selectedClimateScenario &&
        !availableClimateScenarios.includes(
          this.controlsData.selectedClimateScenario,
        )
      ) {
        this.controlsData.selectedClimateScenario =
          availableClimateScenarios[0] || null;
      }

      if (
        this.controlsData.selectedClimateModel &&
        !availableClimateModels.includes(this.controlsData.selectedClimateModel)
      ) {
        this.controlsData.selectedClimateModel =
          availableClimateModels[0] || null;
      }
    }

    this.updateControlsOptions();
  }

  private findMatchingLayer(): void {
    console.log('Finding matching layer for:', {
      variableType: this.controlsData.selectedVariableType,
      yearRange: this.controlsData.selectedYearRange,
      resolution: this.controlsData.selectedResolution,
    });

    const matchingLayer = this.findMatchingLayerOption();

    if (matchingLayer) {
      this.selectedOption = matchingLayer;
      console.log(
        'Found matching layer:',
        matchingLayer.name,
        matchingLayer.metadata,
      );
    } else {
      this.selectedOption = undefined;
      console.log(
        'No exact match found for current selections - clearing current layer',
      );
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
          minZoom: 0,
          maxNativeZoom: this.selectedOption.rasterMaxZoom,
          maxZoom: 12,
          tileSize: 256,
          opacity: 0.8,
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
      if (this.vectorLayer && this.controlsData.showContourLines) {
        this.map?.addLayer(this.vectorLayer);
      }

      setTimeout(() => {
        this.map?.invalidateSize();
      }, 0);
    } else {
      console.log('No layer selected - not adding any layers to map');
    }
  }

  private addControls() {
    if (!this.map) {
      console.assert(false, 'map is not defined');
      return;
    }

    const isMobile = window.innerWidth <= 768;

    if (!isMobile) {
      new Control.Zoom({ position: 'topleft' }).addTo(this.map);
      new Control.Scale().addTo(this.map);
    }
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

    if (!this.selectedOption?.metadata?.dataType || !this.map) {
      console.log('No layer selected, skipping click handler');
      return;
    }

    const lat = event.latlng.lat;
    const lon = CoordinateUtils.normalizeLongitude(event.latlng.lng);

    // Track map click with Matomo
    this.tracker.trackEvent(
      'Map Interaction',
      'Map Click',
      `${lat.toFixed(4)},${lon.toFixed(4)}`,
    );

    // Always handle tooltip display (works on both mobile and desktop)
    this.mapClickHandler.handleMapClick(
      event,
      this.map,
      this.selectedOption.metadata.dataType,
      this.monthSelected,
      this.controlsData.selectedVariableType,
    );

    const plotData = {
      lat,
      lon,
      dataType: this.selectedOption.metadata.dataType,
    };

    const timerangePlotData = {
      lat,
      lon,
      month: this.monthSelected,
    };

    if (this.isMobile) {
      // On mobile, delegate to ClimatePlotsComponent
      this.climatePlots.onMapClick(plotData, timerangePlotData);
    } else {
      // On desktop, show plots directly as before
      this.plotData = plotData;
      this.timerangePlotData = timerangePlotData;
    }
  }

  onMapReady(map: Map): void {
    this.map = map;
    this.initializeMap();
    setTimeout(() => {
      this.map?.invalidateSize();
      // Set initial resolution based on zoom level
      this.handleZoomBasedResolutionChange();
    }, 0);
  }

  onMove(event: LeafletEvent): void {
    console.log('onMove', event);
    this.update();
    this.updateUrlFromMapState();
    this.clearTooltips();
  }

  onZoom(event: LeafletEvent): void {
    console.log('onZoom: level', this.map?.getZoom(), event);
    this.updateUrlFromMapState();
    this.clearTooltips();
    this.handleZoomBasedResolutionChange();

    const zoomLevel = this.map?.getZoom();
    if (zoomLevel !== undefined) {
      this.tracker.trackEvent(
        'Map Interaction',
        'Zoom',
        `Level ${zoomLevel}`,
        zoomLevel,
      );
    }
  }

  onMouseMove(event: LeafletMouseEvent): void {
    if (!this.map) {
      return;
    }

    // Try to extract color from the raster layer first
    let colorInfo: ColorInfo | null = null;

    if (this.rasterLayer) {
      console.log('Extracting color from raster layer');
      colorInfo = this.colorExtractionService.getColorFromTileLayer(
        this.map,
        event.latlng,
        this.rasterLayer as any,
      );
    }

    // // Fallback to general color extraction if raster layer extraction fails
    // if (!colorInfo) {
    //   console.log('Falling back to general color extraction');
    //   colorInfo = this.colorExtractionService.getColorAtPosition(
    //     this.map,
    //     event.latlng,
    //   );
    // }

    if (colorInfo) {
      console.log('Color at mouse position:', {
        position: { lat: event.latlng.lat, lng: event.latlng.lng },
        color: colorInfo,
        source: this.rasterLayer ? 'raster layer' : 'general extraction',
      });

      // You can use the color information here
      // For example, update a color display component or tooltip
      this.displayColorInfo(colorInfo, event.latlng);
    }
  }

  private displayColorInfo(colorInfo: ColorInfo, latlng: L.LatLng): void {
    // Create a tooltip showing the color information
    const colorText = `Color: ${colorInfo.hex} (${colorInfo.rgba})`;
    this.tooltipManager.createHoverTooltip(colorText, latlng, this.map!);
  }

  /**
   * Get color from the raster layer at the specified position
   * @param latlng LatLng position to sample
   * @returns ColorInfo object with color data or null if extraction fails
   */
  getColorFromRasterLayer(latlng: L.LatLng): ColorInfo | null {
    if (!this.map || !this.rasterLayer) {
      console.warn('Map or raster layer not available');
      return null;
    }

    try {
      return this.colorExtractionService.getColorFromTileLayer(
        this.map,
        latlng,
        this.rasterLayer as any,
      );
    } catch (error) {
      console.error('Error extracting color from raster layer:', error);
      return null;
    }
  }

  /**
   * Get color from the raster layer at the current mouse position
   * @param event Mouse event from the map
   * @returns ColorInfo object with color data or null if extraction fails
   */
  getColorFromRasterLayerAtMouse(event: LeafletMouseEvent): ColorInfo | null {
    return this.getColorFromRasterLayer(event.latlng);
  }

  /**
   * Get the maximum zoom level for the raster layer
   * @returns Maximum zoom level or null if not available
   */
  getRasterLayerMaxZoom(): number | null {
    if (!this.rasterLayer) {
      return null;
    }

    try {
      const options = (this.rasterLayer as any).options;
      return options?.maxNativeZoom || options?.maxZoom || null;
    } catch (error) {
      console.error('Error getting raster layer max zoom:', error);
      return null;
    }
  }

  private updateUrlFromMapState(): void {
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

  protected updateUrlWithControls(): void {
    const isHistorical =
      this.controlsData.selectedYearRange &&
      this.isHistoricalYearRange(this.controlsData.selectedYearRange.value);

    const controlsForUrl = isHistorical
      ? {
          ...this.controlsData,
          selectedClimateScenario: null,
          selectedClimateModel: null,
        }
      : this.controlsData;

    const urlData = URLUtils.encodeControls(controlsForUrl);
    URLUtils.updateURLParams(urlData);
  }

  private onVectorLayerHover(e: any): void {
    if (!this.map) {
      return;
    }

    const unit = this.getCurrentUnit();
    this.vectorLayerTooltip.handleVectorLayerHover(
      e,
      this.map,
      this.controlsData.selectedVariableType,
      unit,
    );
  }

  private onVectorLayerMouseOut(): void {
    if (this.map) {
      this.vectorLayerTooltip.handleVectorLayerMouseOut(this.map);
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

  private setupNavigationListener(): void {
    this.mapNavigationService.navigation$.subscribe((request) => {
      if (this.map) {
        this.map.setView([request.lat, request.lon], request.zoom, {
          animate: true,
          duration: 1.0,
        });
        this.updateUrlFromMapState();

        if (request.generateCharts && this.selectedOption?.metadata?.dataType) {
          // Wait for map animation to complete before generating plots
          setTimeout(() => {
            const plotData = {
              lat: request.lat,
              lon: CoordinateUtils.normalizeLongitude(request.lon),
              dataType: this.selectedOption!.metadata!.dataType,
            };

            const timerangePlotData = {
              lat: request.lat,
              lon: CoordinateUtils.normalizeLongitude(request.lon),
              month: this.monthSelected,
            };

            if (this.isMobile) {
              // On mobile, delegate to ClimatePlotsComponent
              this.climatePlots.onMapClick(plotData, timerangePlotData);
            } else {
              // On desktop, show plots directly
              this.plotData = plotData;
              this.timerangePlotData = timerangePlotData;
            }
          }, 1200); // Wait for map animation to complete (1.0s duration + buffer)
        }
      }
    });
  }

  getMonthName(month: number): string {
    const monthNames = [
      'January',
      'February',
      'March',
      'April',
      'May',
      'June',
      'July',
      'August',
      'September',
      'October',
      'November',
      'December',
    ];
    return monthNames[month - 1] || '';
  }

  formatYearRange(yearRange: readonly [number, number]): string {
    return `${yearRange[0]}-${yearRange[1]}`;
  }

  onVariableChange(variableType: ClimateVarKey): void {
    this.controlsData.selectedVariableType = variableType;
    this.checkAndShowFuturePredictionWarning();
    this.onControlsChange(this.controlsData);

    const variableName =
      this.climateVariables[variableType]?.displayName || variableType;
    this.tracker.trackEvent(
      'Variable Selection',
      'Variable Change (Map)',
      variableName,
    );
  }

  onMonthChange(month: number): void {
    this.controlsData.selectedMonth = month;
    this.onControlsChange(this.controlsData);
  }

  onYearRangeChange(yearRange: YearRange): void {
    this.controlsData.selectedYearRange = yearRange;
    this.onControlsChange(this.controlsData);
  }

  onPlotDataRequested(event: { plotData: any; timerangePlotData: any }): void {
    this.plotData = event.plotData;
    this.timerangePlotData = event.timerangePlotData;
  }

  private clearTooltips(): void {
    if (this.map) {
      this.tooltipManager.removeAllTooltips(this.map);
    }
    // Clear both mobile and desktop plots when map moves
    this.climatePlots?.clearMobileState();
    this.clearDesktopPlots();
  }

  private clearDesktopPlots(): void {
    this.plotData = null;
    this.timerangePlotData = null;
  }

  private handleZoomBasedResolutionChange(): void {
    if (!this.map) {
      return;
    }

    const currentZoom = this.map.getZoom();
    const targetResolution = this.getResolutionForZoom(currentZoom);

    // Only switch resolution if we have a different resolution available and it's different from current
    if (
      targetResolution &&
      targetResolution !== this.controlsData.selectedResolution
    ) {
      const availableResolutions = this.getAvailableResolutions();

      if (availableResolutions.includes(targetResolution)) {
        console.log(
          `Switching to ${targetResolution} resolution for zoom level ${currentZoom}`,
        );
        this.controlsData.selectedResolution = targetResolution;
        this.findMatchingLayer();
        this.updateLayers();
        this.updateUrlWithControls();
      }
    }
  }

  private getResolutionForZoom(zoom: number): SpatialResolution | null {
    // Switch to high resolution when zoom >= 6
    if (zoom >= 6) {
      // Try to find the highest available resolution
      const availableResolutions = this.getAvailableResolutions();

      // Order resolutions from highest to lowest resolution
      const resolutionOrder = [
        SpatialResolution.MIN2_5,
        SpatialResolution.MIN5,
        SpatialResolution.MIN10,
        SpatialResolution.MIN30,
      ];

      // Find the highest available resolution
      for (const resolution of resolutionOrder) {
        if (availableResolutions.includes(resolution)) {
          return resolution;
        }
      }
    } else {
      // For zoom < 6, use the default resolution (10m)
      return SpatialResolution.MIN10;
    }

    return null;
  }

  shouldDisableYearSlider(): boolean {
    if (!this.controlsData?.selectedVariableType) {
      return false;
    }
    return !this.climateVariableHelper.hasFuturePredictions(
      this.controlsData.selectedVariableType,
    );
  }

  isPredictionYearRange(): boolean {
    if (!this.controlsData?.selectedYearRange) {
      return false;
    }
    return !this.isHistoricalYearRange(
      this.controlsData.selectedYearRange.value,
    );
  }

  shouldShowDifferenceCheckbox(): boolean {
    return !!(
      this.controlsData?.selectedYearRange &&
      this.controlsOptions?.isHistoricalYearRange &&
      this.controlsData.selectedYearRange.value &&
      !this.controlsOptions.isHistoricalYearRange(
        this.controlsData.selectedYearRange.value,
      )
    );
  }

  onContourToggle(showContour: boolean): void {
    this.controlsData.showContourLines = showContour;
    this.updateVectorLayerVisibility();

    // Show toast message
    if (showContour) {
      this.toastService.showInfo('Contour lines are now visible', 3000);
    } else {
      this.toastService.showInfo('Contour lines are now hidden', 3000);
    }

    this.tracker.trackEvent(
      'Control Selection',
      'Contour Lines Toggle',
      showContour ? 'Enabled' : 'Disabled',
      showContour ? 1 : 0,
    );
  }

  private updateVectorLayerVisibility(): void {
    if (!this.map || !this.vectorLayer) {
      return;
    }

    if (this.controlsData.showContourLines) {
      if (!this.map.hasLayer(this.vectorLayer)) {
        this.map.addLayer(this.vectorLayer);
      }
    } else {
      if (this.map.hasLayer(this.vectorLayer)) {
        this.map.removeLayer(this.vectorLayer);
      }
    }
  }

  onShowChangeToggle(showChange: boolean): void {
    this.controlsData.showDifferenceMap = showChange;
    this.onControlsChange(this.controlsData);

    // Show toast message
    if (showChange) {
      this.toastService.showInfo(
        'Map now shows the predicted change between historical and future climate data',
        4000,
      );
    } else {
      this.toastService.showInfo(
        'Map now shows the predicted absolute values',
        4000,
      );
    }

    this.tracker.trackEvent(
      'Control Selection',
      'Difference Map Toggle (Mobile)',
      showChange ? 'Enabled' : 'Disabled',
      showChange ? 1 : 0,
    );
  }

  private setVariableSpecificSEO(variable: string, title: string): void {
    const variableKey = variable as ClimateVarKey;
    const variableName =
      this.climateVariables?.[variableKey]?.displayName ||
      variable.toLowerCase();

    const seoTitle = `${title} - OpenClimateMap`;
    const description = `Explore interactive ${title.toLowerCase()} showing ${variableName.toLowerCase()} data. View historical and future climate projections with detailed temperature and precipitation maps.`;
    const keywords = `${title.toLowerCase()}, ${variableName.toLowerCase()}, climate map, temperature map, precipitation map, climate data, climate change, CMIP6, climate visualization`;

    this.seoService.updateMetaTags({
      title: seoTitle,
      description: description,
      keywords: keywords,
      url: `/${variable.toLowerCase()}`,
    });
  }
}
