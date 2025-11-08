import { Directive, OnInit } from '@angular/core';
import { Location } from '@angular/common';
import { ActivatedRoute, ParamMap } from '@angular/router';
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
  CLIMATE_SCENARIO_DISPLAY_NAMES,
} from '../utils/enum';
import {
  LayerBuilderService,
  LayerOption,
} from './services/layer-builder.service';
import { LayerFilterService } from './services/layer-filter.service';
import { URLUtils } from '../utils/url-utils';
import {
  MapControlsData,
  MapControlsOptions,
} from './controls/map-controls.component';
import { MapSyncService, MapViewState } from './services/map-sync.service';
import { ToastService } from '../core/toast.service';

@Directive()
export abstract class BaseMapComponent implements OnInit {
  layerOptions: LayerOption[] = [];
  climateMaps: ClimateMap[] = [];

  controlsData: MapControlsData = {
    selectedVariableType: ClimateVarKey.T_MAX,
    selectedYearRange: null,
    selectedResolution: SpatialResolution.MIN10,
    selectedClimateScenario: null,
    selectedClimateModel: null,
    showDifferenceMap: true,
    showContourLines: true,
    selectedMonth: new Date().getMonth() + 1,
  };

  controlsOptions: MapControlsOptions | undefined;

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
    protected route: ActivatedRoute,
    protected location: Location,
    protected climateMapService: ClimateMapService,
    protected metadataService: MetadataService,
    protected layerBuilder: LayerBuilderService,
    protected layerFilter: LayerFilterService,
    protected toastService: ToastService,
    protected mapSyncService?: MapSyncService,
  ) {
    this.isHistoricalYearRange =
      this.metadataService.isHistoricalYearRange.bind(this.metadataService);
  }

  ngOnInit(): void {
    this.checkMobile();
    this.setupResizeListener();

    this.route.queryParamMap.subscribe((params) => {
      if (this.mapSyncService) {
        this.mapSyncService.updateFromURLParams(params);
      }
      if (this.climateMaps.length > 0) {
        this.updateControlsFromURL(params);
      }
    });

    if (this.mapSyncService) {
      this.mapSyncService.viewState$.subscribe((state) => {
        this.updateUrlWithLocationZoom(state);
      });
    }

    this.climateMapService.getClimateMapList().subscribe({
      next: (climateMaps) => {
        this.climateMaps = climateMaps;
        this.populateMetadataFromAPI(climateMaps);
        this.layerOptions = this.layerBuilder.buildLayerOptions(climateMaps);
        this.resetInvalidSelections();

        this.route.queryParamMap.subscribe((params) => {
          this.updateControlsFromURL(params);
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

  protected abstract onDataLoaded(): void;

  protected populateMetadataFromAPI(climateMaps: ClimateMap[]): void {
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

    this.initializeDefaultSelections();

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

  protected abstract initializeDefaultSelections(): void;

  onControlsChange(newControlsData: MapControlsData): void {
    this.controlsData = { ...newControlsData };
    this.handleControlsChange();
  }

  protected handleControlsChange(): void {
    this.setDefaultFutureSelections();
    this.resetInvalidSelections();
    this.onControlsUpdated();
    this.updateUrlWithControls();
  }

  protected abstract onControlsUpdated(): void;

  protected setDefaultFutureSelections(): void {
    if (
      this.controlsData.selectedYearRange &&
      !this.isHistoricalYearRange(this.controlsData.selectedYearRange.value)
    ) {
      if (!this.controlsData.selectedClimateScenario) {
        this.controlsData.selectedClimateScenario = ClimateScenario.SSP370;
      }
      if (!this.controlsData.selectedClimateModel) {
        this.controlsData.selectedClimateModel = ClimateModel.ENSEMBLE_MEAN;
      }
    }
  }

  protected getAvailableVariableTypes(): ClimateVarKey[] {
    return this.layerFilter.getAvailableVariableTypes(
      this.climateMaps,
      this.variableTypes,
      this.climateVariables,
    );
  }

  protected getAvailableYearRanges(): YearRange[] {
    return this.layerFilter.getAvailableYearRanges(
      this.climateMaps,
      this.yearRanges,
      this.controlsData,
      this.climateVariables,
    );
  }

  protected getAvailableResolutions(): SpatialResolution[] {
    return this.layerFilter.getAvailableResolutions(
      this.climateMaps,
      this.resolutions,
      this.controlsData,
      this.climateVariables,
      this.isHistoricalYearRange,
    );
  }

  protected getAvailableClimateScenarios(): ClimateScenario[] {
    return this.layerFilter.getAvailableClimateScenarios(
      this.climateMaps,
      this.climateScenarios,
      this.controlsData,
      this.climateVariables,
      this.isHistoricalYearRange,
    );
  }

  protected getAvailableClimateModels(): ClimateModel[] {
    return this.layerFilter.getAvailableClimateModels(
      this.climateMaps,
      this.climateModels,
      this.controlsData,
      this.climateVariables,
      this.isHistoricalYearRange,
    );
  }

  protected isYearRangeAvailable(
    selectedYearRange: YearRange,
    availableYearRanges: YearRange[],
  ): boolean {
    return availableYearRanges.some((availableRange) => {
      const matchesPrimary =
        availableRange.value[0] === selectedYearRange.value[0] &&
        availableRange.value[1] === selectedYearRange.value[1];

      const matchesAdditional = selectedYearRange.additionalValues?.some(
        (additionalValue) =>
          availableRange.value[0] === additionalValue[0] &&
          availableRange.value[1] === additionalValue[1],
      );

      return matchesPrimary || matchesAdditional;
    });
  }

  protected abstract resetInvalidSelections(): void;

  protected updateControlsOptions(): void {
    if (!this.controlsOptions) {
      return;
    }
    this.controlsOptions = {
      ...this.controlsOptions,
      availableVariableTypes: this.getAvailableVariableTypes(),
      availableYearRanges: this.getAvailableYearRanges(),
      availableResolutions: this.getAvailableResolutions(),
      availableClimateScenarios: this.getAvailableClimateScenarios(),
      availableClimateModels: this.getAvailableClimateModels(),
    };
  }

  protected findMatchingLayerOption(filters?: {
    yearRange?: YearRange;
    scenario?: ClimateScenario;
  }): LayerOption | undefined {
    const yearRange = filters?.yearRange || this.controlsData.selectedYearRange;
    const scenario =
      filters?.scenario !== undefined
        ? filters.scenario
        : this.controlsData.selectedClimateScenario;

    if (!yearRange) {
      return undefined;
    }

    return this.layerOptions.find((option) => {
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

      if (!this.isHistoricalYearRange(yearRange.value)) {
        if (metadata.isDifferenceMap !== this.controlsData.showDifferenceMap) {
          return false;
        }

        if (scenario && metadata.climateScenario !== scenario) {
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
        if (metadata.isDifferenceMap) {
          return false;
        }
      }

      return true;
    });
  }

  protected updateControlsFromURL(params: ParamMap): void {
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

    if (
      decoded.yearRange &&
      decoded.yearRange !== this.controlsData.selectedYearRange
    ) {
      this.controlsData.selectedYearRange = decoded.yearRange;
      hasChanges = true;
    }

    if (hasChanges) {
      this.handleControlsChange();
    }
  }

  protected abstract updateUrlWithControls(): void;

  protected updateUrlWithLocationZoom(state: MapViewState): void {
    const url = new URL(window.location.href);
    url.searchParams.set('lat', state.center.lat.toFixed(6));
    url.searchParams.set('lon', state.center.lng.toFixed(6));
    url.searchParams.set('zoom', String(state.zoom));
    this.location.replaceState(url.pathname + url.search);
  }

  protected checkMobile(): void {
    this.isMobile = window.innerWidth <= 768;
    if (this.isMobile) {
      this.sidebarOpened = false;
    }
  }

  protected setupResizeListener(): void {
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

  onVariableChange(variableType: ClimateVarKey): void {
    this.controlsData.selectedVariableType = variableType;
    this.onControlsChange(this.controlsData);
  }

  shouldShowFutureControls(): boolean {
    return !!(
      this.controlsData?.selectedYearRange &&
      this.controlsOptions?.isHistoricalYearRange &&
      this.controlsData.selectedYearRange.value &&
      !this.controlsOptions.isHistoricalYearRange(
        this.controlsData.selectedYearRange.value,
      )
    );
  }

  onClimateScenarioChangeOverlay(scenario: ClimateScenario | null): void {
    this.controlsData.selectedClimateScenario = scenario;
    this.onControlsChange(this.controlsData);
  }

  protected getYearRangeLabel(yearRange: YearRange): string {
    const start = yearRange.value[0];
    const end = yearRange.value[1];
    return `${start}-${end}`;
  }

  protected getScenarioLabel(scenario: ClimateScenario): string {
    return CLIMATE_SCENARIO_DISPLAY_NAMES[scenario] || scenario;
  }
}
