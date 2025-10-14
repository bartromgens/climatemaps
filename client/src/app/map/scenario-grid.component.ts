import { Component } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import { SmallMapComponent } from './small-map.component';
import { ColorbarComponent } from './colorbar.component';
import { MapControlsComponent } from './map-controls.component';
import { ClimateMapService } from '../core/climatemap.service';
import { MetadataService } from '../core/metadata.service';
import {
  ClimateScenario,
  ClimateModel,
  SpatialResolution,
} from '../utils/enum';
import {
  LayerBuilderService,
  LayerOption,
} from './services/layer-builder.service';
import { LayerFilterService } from './services/layer-filter.service';
import { URLUtils } from '../utils/url-utils';
import { MapSyncService } from './services/map-sync.service';
import { BaseMapComponent } from './base-map.component';

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
    mapSyncService: MapSyncService,
  ) {
    super(
      route,
      location,
      climateMapService,
      metadataService,
      layerBuilder,
      layerFilter,
      mapSyncService,
    );
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
    const labels: Record<ClimateScenario, string> = {
      [ClimateScenario.SSP126]: 'SSP1-2.6 (Low)',
      [ClimateScenario.SSP245]: 'SSP2-4.5 (Medium)',
      [ClimateScenario.SSP370]: 'SSP3-7.0 (High)',
      [ClimateScenario.SSP585]: 'SSP5-8.5 (Very High)',
    };
    return labels[scenario] || scenario;
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
