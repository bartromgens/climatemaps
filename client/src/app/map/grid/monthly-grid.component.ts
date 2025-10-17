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
import { SpatialResolution } from '../../utils/enum';
import {
  LayerBuilderService,
  LayerOption,
} from '../services/layer-builder.service';
import { LayerFilterService } from '../services/layer-filter.service';
import { URLUtils } from '../../utils/url-utils';
import { MapSyncService } from '../services/map-sync.service';
import { BaseMapComponent } from '../base-map.component';
import { SeoService } from '../../core/seo.service';

interface MonthOption {
  month: number;
  label: string;
}

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
export class MonthlyGridComponent extends BaseMapComponent {
  private readonly DEFAULT_RESOLUTION = SpatialResolution.MIN10;

  constructor(
    route: ActivatedRoute,
    location: Location,
    climateMapService: ClimateMapService,
    metadataService: MetadataService,
    layerBuilder: LayerBuilderService,
    layerFilter: LayerFilterService,
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
      mapSyncService,
    );
    this.seoService.updateMetaTags({
      title:
        'Seasonal Climate Maps - Monthly Temperature & Precipitation Patterns',
      description:
        'View seasonal climate maps showing monthly temperature and precipitation patterns across the globe. Compare climate data by month for different time periods and scenarios.',
      keywords:
        'seasonal climate map, monthly climate, temperature by month, precipitation by season, seasonal weather patterns',
      url: '/seasons',
    });
  }

  months: MonthOption[] = [
    { month: 12, label: 'December' },
    { month: 1, label: 'January' },
    { month: 2, label: 'February' },
    { month: 3, label: 'March' },
    { month: 4, label: 'April' },
    { month: 5, label: 'May' },
    { month: 6, label: 'June' },
    { month: 7, label: 'July' },
    { month: 8, label: 'August' },
    { month: 9, label: 'September' },
    { month: 10, label: 'October' },
    { month: 11, label: 'November' },
  ];
  selectedOption: LayerOption | undefined;

  protected onDataLoaded(): void {
    this.findMatchingLayer();
  }

  protected initializeDefaultSelections(): void {
    if (!this.controlsData.selectedYearRange && this.yearRanges.length > 0) {
      this.controlsData.selectedYearRange = this.yearRanges[0];
    }
  }

  protected onControlsUpdated(): void {
    this.findMatchingLayer();
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
    this.selectedOption = this.findMatchingLayerOption();
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
}
