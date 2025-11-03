import { Component } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import { SmallMapComponent } from '../controls/small-map.component';
import { ColorbarComponent } from '../colorbar.component';
import { MapControlsComponent } from '../controls/map-controls.component';
import { MobileHamburgerMenuComponent } from '../controls/mobile-hamburger-menu.component';
import { VariableSelectorOverlayComponent } from '../controls/variable-selector-overlay.component';
import { ClimateMapService } from '../../core/climatemap.service';
import { MetadataService, YearRange } from '../../core/metadata.service';
import {
  ClimateScenario,
  ClimateModel,
  SpatialResolution,
  ClimateVarKey,
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

interface GridCell {
  scenario: ClimateScenario;
  yearRange: YearRange;
  option: LayerOption | undefined;
}

@Component({
  selector: 'app-scenario-yearrange-grid',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatSidenavModule,
    MatButtonModule,
    SmallMapComponent,
    ColorbarComponent,
    MapControlsComponent,
    MobileHamburgerMenuComponent,
    VariableSelectorOverlayComponent,
  ],
  templateUrl: './scenario-yearrange-grid.component.html',
  styleUrl: './scenario-yearrange-grid.component.scss',
})
export class ScenarioYearRangeGridComponent extends BaseMapComponent {
  private readonly DEFAULT_RESOLUTION = SpatialResolution.MIN10;
  private readonly DEFAULT_MODEL = ClimateModel.ENSEMBLE_MEAN;

  scenarios: ClimateScenario[] = [
    ClimateScenario.SSP126,
    ClimateScenario.SSP245,
    ClimateScenario.SSP370,
    ClimateScenario.SSP585,
  ];

  futureYearRanges: YearRange[] = [];
  gridCells: GridCell[] = [];

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
        'Climate Scenarios & Time Periods Maps - Compare Future Projections on a Map Grid',
      description:
        'Compare climate projections across different scenarios (SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5) and time periods. View how temperature and precipitation changes vary by scenario and decade.',
      keywords:
        'climate scenarios matrix, future projections, SSP scenarios timeline, climate change comparison, CMIP6 scenarios, temperature projections, precipitation projections',
      url: '/climate-matrix',
    });
  }

  protected onDataLoaded(): void {
    this.updateFutureYearRanges();
    this.findMatchingLayers();
  }

  protected initializeDefaultSelections(): void {
    if (!this.controlsData.selectedClimateModel) {
      this.controlsData.selectedClimateModel = this.DEFAULT_MODEL;
    }
  }

  protected onControlsUpdated(): void {
    this.findMatchingLayers();
  }

  protected resetInvalidSelections(): void {
    const availableResolutions = this.getAvailableResolutions();
    const availableClimateModels = this.getAvailableClimateModels();

    if (!availableResolutions.includes(this.controlsData.selectedResolution)) {
      this.controlsData.selectedResolution =
        availableResolutions[0] || this.DEFAULT_RESOLUTION;
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

  private updateFutureYearRanges(): void {
    const availableYearRanges = this.getAvailableYearRanges();
    this.futureYearRanges = availableYearRanges.filter(
      (range) => !this.isHistoricalYearRange(range.value),
    );
  }

  private findMatchingLayers(): void {
    this.gridCells = [];

    for (const scenario of this.scenarios) {
      for (const yearRange of this.futureYearRanges) {
        const matchingLayer = this.findLayerForCell(scenario, yearRange);
        this.gridCells.push({
          scenario,
          yearRange,
          option: matchingLayer,
        });
      }
    }
  }

  private findLayerForCell(
    scenario: ClimateScenario,
    yearRange: YearRange,
  ): LayerOption | undefined {
    return this.findMatchingLayerOption({ scenario, yearRange });
  }

  protected updateUrlWithControls(): void {
    const controlsForUrl = {
      ...this.controlsData,
      selectedClimateScenario: null,
      selectedYearRange: null,
    };

    const urlData = URLUtils.encodeControls(controlsForUrl);
    URLUtils.updateURLParams(urlData);
  }


  getCellsForScenario(scenario: ClimateScenario): GridCell[] {
    return this.gridCells.filter((cell) => cell.scenario === scenario);
  }

  get colormapUrl(): string | null {
    return this.gridCells[0]?.option?.climateMap?.colormapUrl || null;
  }

  get displayName(): string | null {
    return this.gridCells[0]?.option?.climateMap?.getDisplayName() || null;
  }

}
