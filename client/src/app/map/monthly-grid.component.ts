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

@Component({
  selector: 'app-monthly-grid',
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
  templateUrl: './monthly-grid.component.html',
  styleUrl: './monthly-grid.component.scss',
})
export class MonthlyGridComponent implements OnInit {
  months: number[] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
  layerOptions: LayerOption[] = [];
  selectedOption: LayerOption | undefined;

  climateMaps: ClimateMap[] = [];

  controlsData: MapControlsData = {
    selectedVariableType: ClimateVarKey.T_MAX,
    selectedYearRange: null,
    selectedResolution: SpatialResolution.MIN10,
    selectedClimateScenario: null,
    selectedClimateModel: null,
    showDifferenceMap: true,
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
  ) {
    this.isHistoricalYearRange =
      this.metadataService.isHistoricalYearRange.bind(this.metadataService);
  }

  ngOnInit(): void {
    this.checkMobile();
    this.setupResizeListener();

    this.route.queryParamMap.subscribe((params) => {
      if (this.climateMaps.length > 0) {
        this.updateControlsFromURL(params);
      }
    });

    this.climateMapService.getClimateMapList().subscribe((climateMaps) => {
      this.climateMaps = climateMaps;
      this.populateMetadataFromAPI(climateMaps);
      this.layerOptions = this.layerBuilder.buildLayerOptions(climateMaps);
      this.resetInvalidSelections();

      this.route.queryParamMap.subscribe((params) => {
        this.updateControlsFromURL(params);
      });

      this.findMatchingLayer();
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

    if (!this.controlsData.selectedYearRange && this.yearRanges.length > 0) {
      this.controlsData.selectedYearRange = this.yearRanges[0];
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

    this.resetInvalidSelections();
    this.findMatchingLayer();
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

  private isYearRangeAvailable(
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

  private resetInvalidSelections(): void {
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
        availableResolutions[0] || SpatialResolution.MIN10;
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

  private findMatchingLayer(): void {
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
        metadata.yearRange[0] ===
          this.controlsData.selectedYearRange!.value[0] &&
        metadata.yearRange[1] === this.controlsData.selectedYearRange!.value[1];

      const matchesAdditionalRange =
        this.controlsData.selectedYearRange!.additionalValues?.some(
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

      if (
        !this.isHistoricalYearRange(this.controlsData.selectedYearRange!.value)
      ) {
        if (metadata.isDifferenceMap !== this.controlsData.showDifferenceMap) {
          return false;
        }
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
        if (metadata.isDifferenceMap) {
          return false;
        }
      }

      return true;
    });

    if (matchingLayer) {
      this.selectedOption = matchingLayer;
    } else {
      this.selectedOption = undefined;
    }
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

  private updateUrlWithControls(): void {
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
}
