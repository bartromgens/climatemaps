import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { ClimateMonthlyPlotComponent } from './climate-monthly-plot.component';
import { ClimateTimerangePlotComponent } from './climate-timerange-plot.component';
import { YearRange } from '../../core/metadata.service';
import { ClimateScenario, ClimateModel } from '../../utils/enum';
import { MatomoTracker } from 'ngx-matomo-client';

export interface PlotData {
  lat: number;
  lon: number;
  dataType: string;
}

export interface TimerangePlotData {
  lat: number;
  lon: number;
  month: number;
}

@Component({
  selector: 'app-climate-plots',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatIconModule,
    ClimateMonthlyPlotComponent,
    ClimateTimerangePlotComponent,
  ],
  templateUrl: './climate-plots.component.html',
  styleUrl: './climate-plots.component.scss',
})
export class ClimatePlotsComponent {
  private readonly tracker = inject(MatomoTracker);

  @Input() isMobile = false;
  @Input() plotData: PlotData | null = null;
  @Input() timerangePlotData: TimerangePlotData | null = null;
  @Input() yearRange: YearRange | null = null;
  @Input() climateScenario: ClimateScenario | null = null;
  @Input() climateModel: ClimateModel | null = null;

  // Internal mobile state management
  private mobilePlotData: PlotData | null = null;
  private mobileTimerangePlotData: TimerangePlotData | null = null;
  showMobilePlotButton = false;
  showMobilePlots = false;

  @Output() plotDataRequested = new EventEmitter<{
    plotData: PlotData;
    timerangePlotData: TimerangePlotData;
  }>();

  // Method to be called when user clicks on map (mobile only)
  onMapClick(plotData: PlotData, timerangePlotData: TimerangePlotData): void {
    if (this.isMobile) {
      this.mobilePlotData = plotData;
      this.mobileTimerangePlotData = timerangePlotData;
      this.showMobilePlotButton = true;
      this.showMobilePlots = false;
    }
  }

  // Method to clear mobile state (called when map moves)
  clearMobileState(): void {
    if (this.isMobile) {
      this.showMobilePlotButton = false;
      this.showMobilePlots = false;
      this.mobilePlotData = null;
      this.mobileTimerangePlotData = null;
    }
  }

  onShowMobilePlots(): void {
    if (this.mobilePlotData && this.mobileTimerangePlotData) {
      this.tracker.trackEvent(
        'Mobile Interface',
        'Show Climate Graphs',
        'Button Click',
        1,
      );

      this.plotDataRequested.emit({
        plotData: this.mobilePlotData,
        timerangePlotData: this.mobileTimerangePlotData,
      });
      this.showMobilePlots = true;
      this.showMobilePlotButton = false;
    }
  }

  onCloseMobilePlots(): void {
    this.showMobilePlots = false;
    this.showMobilePlotButton = false;
    this.mobilePlotData = null;
    this.mobileTimerangePlotData = null;
  }
}
