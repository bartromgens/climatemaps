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
import { MetadataService, YearRange } from '../core/metadata.service';
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
export class YearRangeGridComponent extends BaseMapComponent {
  private readonly DEFAULT_RESOLUTION = SpatialResolution.MIN10;
  private readonly DEFAULT_SCENARIO = ClimateScenario.SSP370;
  private readonly DEFAULT_MODEL = ClimateModel.ENSEMBLE_MEAN;

  yearRangeOptions: YearRangeOption[] = [];

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
    this.controlsData.showDifferenceMap = true;
  }

  protected onDataLoaded(): void {
    this.findMatchingLayers();
  }

  protected initializeDefaultSelections(): void {
    if (!this.controlsData.selectedClimateScenario) {
      this.controlsData.selectedClimateScenario = this.DEFAULT_SCENARIO;
    }

    if (!this.controlsData.selectedClimateModel) {
      this.controlsData.selectedClimateModel = this.DEFAULT_MODEL;
    }
  }

  protected onControlsUpdated(): void {
    this.findMatchingLayers();
  }

  protected resetInvalidSelections(): void {
    const availableResolutions = this.getAvailableResolutions();
    const availableClimateScenarios = this.getAvailableClimateScenarios();
    const availableClimateModels = this.getAvailableClimateModels();

    if (!availableResolutions.includes(this.controlsData.selectedResolution)) {
      this.controlsData.selectedResolution =
        availableResolutions[0] || this.DEFAULT_RESOLUTION;
    }

    if (
      this.controlsData.selectedClimateScenario &&
      !availableClimateScenarios.includes(
        this.controlsData.selectedClimateScenario,
      )
    ) {
      this.controlsData.selectedClimateScenario =
        availableClimateScenarios[0] || this.DEFAULT_SCENARIO;
    }

    if (
      this.controlsData.selectedClimateModel &&
      !availableClimateModels.includes(this.controlsData.selectedClimateModel)
    ) {
      this.controlsData.selectedClimateModel =
        availableClimateModels[0] || this.DEFAULT_MODEL;
    }

    this.updateControlsOptions();
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
    return this.findMatchingLayerOption({ yearRange });
  }

  protected updateUrlWithControls(): void {
    const urlData = URLUtils.encodeControls(this.controlsData);
    URLUtils.updateURLParams(urlData);
  }

  get colormapUrl(): string | null {
    return this.yearRangeOptions[0]?.option?.climateMap?.colormapUrl || null;
  }

  get displayName(): string | null {
    return (
      this.yearRangeOptions[0]?.option?.climateMap?.getDisplayName() || null
    );
  }
}
