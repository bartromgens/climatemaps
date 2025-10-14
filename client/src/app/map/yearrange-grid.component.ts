import { Component, OnInit } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import { SmallMapComponent } from './small-map.component';
import { ColorbarComponent } from './colorbar.component';
import {
  MapControlsComponent,
  MapControlsData,
  MapControlsOptions,
} from './map-controls.component';
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
import {
  LayerBuilderService,
  LayerOption,
} from './services/layer-builder.service';
import { LayerFilterService } from './services/layer-filter.service';
import { URLUtils } from '../utils/url-utils';
import { MapSyncService, MapViewState } from './services/map-sync.service';

interface YearRangeOption {
  yearRange: YearRange;
  label: string;
  option: LayerOption | undefined;
}

@Component({
  selector: 'app-yearrange-grid',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatSidenavModule,
    MatButtonModule,
    SmallMapComponent,
    ColorbarComponent,
    MapControlsComponent,
  ],
  templateUrl: './yearrange-grid.component.html',
  styleUrl: './yearrange-grid.component.scss',
})
export class YearRangeGridComponent implements OnInit {
  yearRangeOptions: YearRangeOption[] = [];
  layerOptions: LayerOption[] = [];

  climateMaps: ClimateMap[] = [];

  controlsData: MapControlsData = {
    selectedVariableType: ClimateVarKey.T_MAX,
    selectedYearRange: null,
    selectedResolution: SpatialResolution.MIN10,
    selectedClimateScenario: null,
    selectedClimateModel: null,
    showDifferenceMap: false,
    selectedMonth: 1,
  };

  controlsOptions!: MapControlsOptions;

  variableTypes: ClimateVarKey[] = [];
  yearRanges: YearRange[] = [];
  resolutions: SpatialResolution[] = [];
  climateScenarios: ClimateScenario[] = [];
  climateModels: ClimateModel[] = [];

  climateVariables: Record<ClimateVarKey, ClimateVariableConfig> = {} as Record<
    ClimateVarKey,
    ClimateVariableConfig
  >;
  isHistoricalYearRange!: (yearRange: readonly [number, number]) => boolean;

  sidebarOpened = false;
  isMobile = false;

  constructor(
    private route: ActivatedRoute,
    private location: Location,
    private climateMapService: ClimateMapService,
    private metadataService: MetadataService,
    private layerBuilder: LayerBuilderService,
    private layerFilter: LayerFilterService,
    private mapSyncService: MapSyncService,
  ) {
    this.isHistoricalYearRange =
      this.metadataService.isHistoricalYearRange.bind(this.metadataService);
  }

  ngOnInit(): void {
    this.checkMobile();
    this.setupResizeListener();

    this.route.queryParamMap.subscribe((params) => {
      this.mapSyncService.updateFromURLParams(params);
      if (this.climateMaps.length > 0) {
        this.updateControlsFromURL(params);
      }
    });

    this.mapSyncService.viewState$.subscribe((state) => {
      this.updateUrlWithLocationZoom(state);
    });

    this.climateMapService.getClimateMapList().subscribe((climateMaps) => {
      this.climateMaps = climateMaps;
      this.populateMetadataFromAPI(climateMaps);
      this.layerOptions = this.layerBuilder.buildLayerOptions(climateMaps);
      this.resetInvalidSelections();

      this.route.queryParamMap.subscribe((params) => {
        this.updateControlsFromURL(params);
      });

      this.findMatchingLayers();
    });
  }

  private populateMetadataFromAPI(climateMaps: ClimateMap[]): void {
    this.climateVariables =
      this.metadataService.getClimateVariables(climateMaps);
    this.yearRanges = this.metadataService.getYearRanges(climateMaps);
    this.resolutions = this.metadataService.getResolutions(climateMaps);
    this.climateScenarios =
      this.metadataService.getClimateScenarios(climateMaps);
    this.climateModels = this.metadataService.getClimateModels(climateMaps);

    this.variableTypes = this.metadataService.getSortedVariableTypes(
      this.climateVariables,
    );

    if (!this.controlsData.selectedClimateScenario) {
      this.controlsData.selectedClimateScenario = ClimateScenario.SSP370;
    }

    if (!this.controlsData.selectedClimateModel) {
      this.controlsData.selectedClimateModel = ClimateModel.ENSEMBLE_MEAN;
    }

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

  onControlsChange(newControlsData: MapControlsData): void {
    this.controlsData = { ...newControlsData };
    this.handleControlsChange();
  }

  private handleControlsChange(): void {
    this.resetInvalidSelections();
    this.findMatchingLayers();
    this.updateUrlWithControls();
  }

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

  private resetInvalidSelections(): void {
    const availableResolutions = this.getAvailableResolutions();
    const availableClimateScenarios = this.getAvailableClimateScenarios();
    const availableClimateModels = this.getAvailableClimateModels();

    if (!availableResolutions.includes(this.controlsData.selectedResolution)) {
      this.controlsData.selectedResolution =
        availableResolutions[0] || SpatialResolution.MIN10;
    }

    if (
      this.controlsData.selectedClimateScenario &&
      !availableClimateScenarios.includes(
        this.controlsData.selectedClimateScenario,
      )
    ) {
      this.controlsData.selectedClimateScenario =
        availableClimateScenarios[0] || ClimateScenario.SSP370;
    }

    if (
      this.controlsData.selectedClimateModel &&
      !availableClimateModels.includes(this.controlsData.selectedClimateModel)
    ) {
      this.controlsData.selectedClimateModel =
        availableClimateModels[0] || ClimateModel.ENSEMBLE_MEAN;
    }

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

  private getYearRangeLabel(yearRange: YearRange): string {
    const start = yearRange.value[0];
    const end = yearRange.value[1];
    return `${start}-${end}`;
  }

  private findMatchingLayers(): void {
    const availableYearRanges = this.getAvailableYearRanges();

    this.yearRangeOptions = availableYearRanges.map((yearRange) => {
      const matchingLayer = this.findLayerForYearRange(yearRange);
      return {
        yearRange,
        label: this.getYearRangeLabel(yearRange),
        option: matchingLayer,
      };
    });
  }

  private findLayerForYearRange(yearRange: YearRange): LayerOption | undefined {
    const matchingLayer = this.layerOptions.find((option) => {
      if (!option.metadata) {
        return false;
      }

      const metadata = option.metadata;
      const expectedVariableName =
        this.climateVariables[this.controlsData.selectedVariableType]?.name;

      if (metadata.variableType !== expectedVariableName) {
        return false;
      }

      const matchesPrimaryRange =
        metadata.yearRange[0] === yearRange.value[0] &&
        metadata.yearRange[1] === yearRange.value[1];

      const matchesAdditionalRange = yearRange.additionalValues?.some(
        (additionalValue) =>
          metadata.yearRange[0] === additionalValue[0] &&
          metadata.yearRange[1] === additionalValue[1],
      );

      if (!matchesPrimaryRange && !matchesAdditionalRange) {
        return false;
      }

      if (metadata.resolution !== this.controlsData.selectedResolution) {
        return false;
      }

      if (metadata.isDifferenceMap !== this.controlsData.showDifferenceMap) {
        return false;
      }

      if (!this.isHistoricalYearRange(yearRange.value)) {
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
        if (metadata.climateScenario || metadata.climateModel) {
          return false;
        }
      }

      return true;
    });

    return matchingLayer;
  }

  private updateControlsFromURL(params: ParamMap): void {
    if (this.climateMaps.length === 0) {
      return;
    }

    const urlData = {
      variable: params.get('variable') as ClimateVarKey,
      resolution: params.get('resolution') as SpatialResolution,
      scenario: params.get('scenario') as ClimateScenario,
      model: params.get('model') as ClimateModel,
      difference: params.has('difference')
        ? params.get('difference') === 'true'
        : undefined,
      month: params.get('month')
        ? parseInt(params.get('month')!, 10)
        : undefined,
      yearRange: params.get('yearRange') || undefined,
    };

    const decoded = URLUtils.decodeControls(urlData, this.yearRanges);
    let hasChanges = false;

    if (
      decoded.variable &&
      decoded.variable !== this.controlsData.selectedVariableType
    ) {
      this.controlsData.selectedVariableType = decoded.variable;
      hasChanges = true;
    }

    if (
      decoded.resolution &&
      decoded.resolution !== this.controlsData.selectedResolution
    ) {
      this.controlsData.selectedResolution = decoded.resolution;
      hasChanges = true;
    }

    if (
      decoded.scenario !== undefined &&
      decoded.scenario !== this.controlsData.selectedClimateScenario
    ) {
      this.controlsData.selectedClimateScenario = decoded.scenario;
      hasChanges = true;
    }

    if (
      decoded.model !== undefined &&
      decoded.model !== this.controlsData.selectedClimateModel
    ) {
      this.controlsData.selectedClimateModel = decoded.model;
      hasChanges = true;
    }

    if (
      decoded.difference !== undefined &&
      decoded.difference !== this.controlsData.showDifferenceMap
    ) {
      this.controlsData.showDifferenceMap = decoded.difference;
      hasChanges = true;
    }

    if (decoded.month && decoded.month !== this.controlsData.selectedMonth) {
      this.controlsData.selectedMonth = decoded.month;
      hasChanges = true;
    }

    if (hasChanges) {
      this.handleControlsChange();
    }
  }

  private updateUrlWithControls(): void {
    const urlData = URLUtils.encodeControls(this.controlsData);
    URLUtils.updateURLParams(urlData);
  }

  private checkMobile(): void {
    this.isMobile = window.innerWidth <= 768;
    if (this.isMobile) {
      this.sidebarOpened = false;
    }
  }

  private setupResizeListener(): void {
    window.addEventListener('resize', () => {
      const wasMobile = this.isMobile;
      this.checkMobile();

      if (wasMobile && !this.isMobile) {
        this.sidebarOpened = false;
      }
    });
  }

  toggleSidebar(): void {
    this.sidebarOpened = !this.sidebarOpened;
  }

  get colormapUrl(): string | null {
    return this.yearRangeOptions[0]?.option?.climateMap?.colormapUrl || null;
  }

  get displayName(): string | null {
    return (
      this.yearRangeOptions[0]?.option?.climateMap?.getDisplayName() || null
    );
  }

  private updateUrlWithLocationZoom(state: MapViewState): void {
    const url = new URL(window.location.href);
    url.searchParams.set('lat', state.center.lat.toFixed(6));
    url.searchParams.set('lon', state.center.lng.toFixed(6));
    url.searchParams.set('zoom', String(state.zoom));
    this.location.replaceState(url.pathname + url.search);
  }
}
