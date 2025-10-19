import { Component, inject, OnInit } from '@angular/core';
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
import { ClimateMonthlyPlotComponent } from './plot/climate-monthly-plot.component';
import { ClimateTimerangePlotComponent } from './plot/climate-timerange-plot.component';
import { MapNavigationService } from '../core/map-navigation.service';
import { MapSyncService } from './services/map-sync.service';
import { BaseMapComponent } from './base-map.component';
import { TemperatureUnitService } from '../core/temperature-unit.service';
import { SeoService } from '../core/seo.service';
import { ToastService } from '../core/toast.service';
import { ClimateVariableHelperService } from '../core/climate-variable-helper.service';
import { CoordinateUtils } from '../utils/coordinate-utils';
import { MatomoTracker } from 'ngx-matomo-client';

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
    ClimateMonthlyPlotComponent,
    ClimateTimerangePlotComponent,
    MobileHamburgerMenuComponent,
  ],
  templateUrl: './map.component.html',
  styleUrl: './map.component.scss',
})
export class MapComponent extends BaseMapComponent implements OnInit {
  private readonly tracker = inject(MatomoTracker);
  private readonly DEFAULT_RESOLUTION = SpatialResolution.MIN10;

  selectedOption: LayerOption | undefined;

  get monthSelected(): number {
    return this.controlsData.selectedMonth;
  }

  protected initializeDefaultSelections(): void {
    if (!this.controlsData.selectedYearRange && this.yearRanges.length > 0) {
      this.controlsData.selectedYearRange = this.yearRanges[0];
    }
  }

  protected onControlsUpdated(): void {
    this.checkAndShowFuturePredictionWarning();
    this.findMatchingLayer();
    this.updateLayers();
  }

  private checkAndShowFuturePredictionWarning(): void {
    if (
      !this.climateVariableHelper.hasFuturePredictions(
        this.controlsData.selectedVariableType,
      )
    ) {
      const variableDisplayName =
        this.climateVariables[this.controlsData.selectedVariableType]
          ?.displayName || this.controlsData.selectedVariableType;

      this.toastService.showInfo(
        `No future predictions available for ${variableDisplayName}. Only historical data is available for this variable.`,
        6000,
      );
    }
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

  private map: Map | null = null;
  private rasterLayer: Layer | null = null;
  private vectorLayer: Layer | null = null;
  plotData: { lat: number; lon: number; dataType: string } | null = null;
  timerangePlotData: { lat: number; lon: number; month: number } | null = null;

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
    this.seoService.setDefaultMetaTags();
    this.checkMobile();
    this.setupResizeListener();
    this.setupNavigationListener();

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

    this.plotData = {
      lat,
      lon,
      dataType: this.selectedOption.metadata.dataType,
    };

    this.timerangePlotData = {
      lat,
      lon,
      month: this.monthSelected,
    };

    this.mapClickHandler.handleMapClick(
      event,
      this.map,
      this.selectedOption.metadata.dataType,
      this.monthSelected,
      this.controlsData.selectedVariableType,
    );
  }

  onMapReady(map: Map): void {
    this.map = map;
    this.initializeMap();
    setTimeout(() => {
      this.map?.invalidateSize();
    }, 0);
  }

  onMove(event: LeafletEvent): void {
    console.log('onMove', event);
    this.update();
    this.updateUrlFromMapState();
  }

  onZoom(event: LeafletEvent): void {
    console.log('onZoom: level', this.map?.getZoom(), event);
    this.updateUrlFromMapState();
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
          this.plotData = {
            lat: request.lat,
            lon: CoordinateUtils.normalizeLongitude(request.lon),
            dataType: this.selectedOption.metadata.dataType,
          };

          this.timerangePlotData = {
            lat: request.lat,
            lon: CoordinateUtils.normalizeLongitude(request.lon),
            month: this.monthSelected,
          };
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
}
