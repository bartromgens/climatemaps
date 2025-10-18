import { Component } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import { SmallMapComponent } from '../controls/small-map.component';
import { ColorbarComponent } from '../colorbar.component';
import { MapControlsComponent } from '../controls/map-controls.component';
import { ClimateMapService } from '../../core/climatemap.service';
import { MetadataService } from '../../core/metadata.service';
import {
  ClimateScenario,
  ClimateModel,
  SpatialResolution,
  CLIMATE_SCENARIO_DISPLAY_NAMES,
} from '../../utils/enum';
import {
  LayerBuilderService,
  LayerOption,
} from '../services/layer-builder.service';
import { LayerFilterService } from '../services/layer-filter.service';
import { URLUtils } from '../../utils/url-utils';
import { MapSyncService } from '../services/map-sync.service';
import { BaseMapComponent } from '../base-map.component';
import { SeoService } from '../../core/seo.service';
import { ToastService } from '../../core/toast.service';

interface ScenarioOption {
  scenario: ClimateScenario;
  label: string;
  option: LayerOption | undefined;
}

@Component({
  selector: 'app-scenario-grid',
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
  templateUrl: './scenario-grid.component.html',
  styleUrl: './scenario-grid.component.scss',
})
export class ScenarioGridComponent extends BaseMapComponent {
  private readonly DEFAULT_RESOLUTION = SpatialResolution.MIN10;
  private readonly DEFAULT_MODEL = ClimateModel.ENSEMBLE_MEAN;

  scenarios: ScenarioOption[] = [];

  constructor(
    route: ActivatedRoute,
    location: Location,
    climateMapService: ClimateMapService,
    metadataService: MetadataService,
    layerBuilder: LayerBuilderService,
    layerFilter: LayerFilterService,
    toastService: ToastService,
    mapSyncService: MapSyncService,
    private seoService: SeoService,
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
    this.seoService.updateMetaTags({
      title:
        'Climate Scenarios Comparison - SSP126 SSP245 SSP370 SSP585 Projections',
      description:
        'Compare different CMIP6 climate scenarios (SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5) side by side. Visualize future temperature and precipitation changes under different emission pathways.',
      keywords:
        'climate scenarios, SSP scenarios, climate projections, CMIP6, emission scenarios, climate change comparison, SSP126, SSP245, SSP370, SSP585',
      url: '/climate-scenarios',
    });
  }

  protected onDataLoaded(): void {
    this.findMatchingLayers();
  }

  protected initializeDefaultSelections(): void {
    if (!this.controlsData.selectedYearRange && this.yearRanges.length > 0) {
      const futureYearRanges = this.yearRanges.filter(
        (range) => !this.isHistoricalYearRange(range.value),
      );

      if (futureYearRanges.length > 0) {
        const farthestFutureRange = futureYearRanges.reduce(
          (latest, current) =>
            current.value[1] > latest.value[1] ? current : latest,
        );
        this.controlsData.selectedYearRange = farthestFutureRange;
      } else {
        this.controlsData.selectedYearRange = this.yearRanges[0];
      }
    }

    if (!this.controlsData.selectedClimateModel) {
      this.controlsData.selectedClimateModel = this.DEFAULT_MODEL;
    }
  }

  protected onControlsUpdated(): void {
    this.findMatchingLayers();
  }

  protected override setDefaultFutureSelections(): void {
    if (
      this.controlsData.selectedYearRange &&
      !this.isHistoricalYearRange(this.controlsData.selectedYearRange.value)
    ) {
      if (!this.controlsData.selectedClimateModel) {
        this.controlsData.selectedClimateModel = this.DEFAULT_MODEL;
      }
    }
  }

  protected resetInvalidSelections(): void {
    const availableYearRanges = this.getAvailableYearRanges();
    const availableResolutions = this.getAvailableResolutions();
    const availableClimateModels = this.getAvailableClimateModels();

    if (
      this.controlsData.selectedYearRange &&
      !this.isYearRangeAvailable(
        this.controlsData.selectedYearRange,
        availableYearRanges,
      )
    ) {
      const futureYearRanges = availableYearRanges.filter(
        (range) => !this.isHistoricalYearRange(range.value),
      );

      if (futureYearRanges.length > 0) {
        const farthestFutureRange = futureYearRanges.reduce(
          (latest, current) =>
            current.value[1] > latest.value[1] ? current : latest,
        );
        this.controlsData.selectedYearRange = farthestFutureRange;
      } else {
        this.controlsData.selectedYearRange = availableYearRanges[0] || null;
      }
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
        this.controlsData.selectedClimateModel &&
        !availableClimateModels.includes(this.controlsData.selectedClimateModel)
      ) {
        this.controlsData.selectedClimateModel =
          availableClimateModels[0] || null;
      }
    }

    this.updateControlsOptions();
  }

  private getScenarioLabel(scenario: ClimateScenario): string {
    return CLIMATE_SCENARIO_DISPLAY_NAMES[scenario] || scenario;
  }

  private findMatchingLayers(): void {
    if (
      !this.controlsData.selectedYearRange ||
      this.isHistoricalYearRange(this.controlsData.selectedYearRange.value)
    ) {
      this.scenarios = [];
      return;
    }

    const availableScenarios = this.getAvailableClimateScenarios();

    this.scenarios = availableScenarios.map((scenario) => {
      const matchingLayer = this.findLayerForScenario(scenario);
      return {
        scenario,
        label: this.getScenarioLabel(scenario),
        option: matchingLayer,
      };
    });
  }

  private findLayerForScenario(
    scenario: ClimateScenario,
  ): LayerOption | undefined {
    return this.findMatchingLayerOption({ scenario });
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
      : {
          ...this.controlsData,
          selectedClimateScenario: null,
        };

    const urlData = URLUtils.encodeControls(controlsForUrl);
    URLUtils.updateURLParams(urlData);
  }

  get colormapUrl(): string | null {
    return this.scenarios[0]?.option?.climateMap?.colormapUrl || null;
  }

  get displayName(): string | null {
    return this.scenarios[0]?.option?.climateMap?.getDisplayName() || null;
  }
}
