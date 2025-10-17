import {
  Component,
  Input,
  OnChanges,
  SimpleChanges,
  ViewChild,
  ElementRef,
  AfterViewInit,
  OnDestroy,
  ChangeDetectorRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { Chart, ChartConfiguration, registerables } from 'chart.js';
import { forkJoin } from 'rxjs';

import {
  ClimateMapService,
  NearestCityResponse,
} from '../core/climatemap.service';
import {
  ClimateVarKey,
  CLIMATE_VAR_KEY_TO_NAME,
  CLIMATE_VAR_DISPLAY_NAMES,
  CLIMATE_VAR_UNITS,
} from '../utils/enum';
import {
  TemperatureUnitService,
  TemperatureUnit,
} from '../core/temperature-unit.service';
import { TemperatureUtils } from '../utils/temperature-utils';

Chart.register(...registerables);

interface PlotData {
  lat: number;
  lon: number;
  dataType: string;
}

interface MonthlyData {
  tmax: number[];
  tmin: number[];
  precipitation: number[];
}

@Component({
  selector: 'app-climate-monthly-plot',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule, MatButtonModule],
  templateUrl: './climate-monthly-plot.component.html',
  styleUrl: './climate-monthly-plot.component.scss',
})
export class ClimateMonthlyPlotComponent
  implements OnChanges, AfterViewInit, OnDestroy
{
  @Input() plotData: PlotData | null = null;

  @ViewChild('chartCanvas', { static: false })
  chartCanvas!: ElementRef<HTMLCanvasElement>;

  chart: Chart | null = null;
  isLoading = false;
  error: string | null = null;
  isVisible = true;
  monthlyData: MonthlyData = { tmax: [], tmin: [], precipitation: [] };
  cityInfo: NearestCityResponse | null = null;
  private currentUnit: TemperatureUnit = TemperatureUnit.CELSIUS;

  constructor(
    private climateMapService: ClimateMapService,
    private cdr: ChangeDetectorRef,
    private temperatureUnitService: TemperatureUnitService,
  ) {
    this.temperatureUnitService.unit$.subscribe((unit) => {
      this.currentUnit = unit;
      if (this.chart && this.monthlyData.tmax.length > 0) {
        this.renderChart();
      }
    });
  }

  ngAfterViewInit(): void {
    if (this.plotData) {
      this.loadData();
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['plotData'] && !changes['plotData'].firstChange) {
      if (this.plotData) {
        this.isVisible = true;
        this.loadData();
      }
    }
  }

  ngOnDestroy(): void {
    this.destroyChart();
  }

  private loadData(): void {
    if (!this.plotData) return;

    this.isLoading = true;
    this.error = null;

    const dataTypeTmax = this.getHistoricalDataType(ClimateVarKey.T_MAX);
    const dataTypeTmin = this.getHistoricalDataType(ClimateVarKey.T_MIN);
    const dataTypePrecipitation = this.getHistoricalDataType(
      ClimateVarKey.PRECIPITATION,
    );

    const tmaxRequests = [];
    const tminRequests = [];
    const precipRequests = [];

    for (let month = 1; month <= 12; month++) {
      tmaxRequests.push(
        this.climateMapService.getClimateValue(
          dataTypeTmax,
          month,
          this.plotData.lat,
          this.plotData.lon,
        ),
      );
      tminRequests.push(
        this.climateMapService.getClimateValue(
          dataTypeTmin,
          month,
          this.plotData.lat,
          this.plotData.lon,
        ),
      );
      precipRequests.push(
        this.climateMapService.getClimateValue(
          dataTypePrecipitation,
          month,
          this.plotData.lat,
          this.plotData.lon,
        ),
      );
    }

    forkJoin({
      tmax: forkJoin(tmaxRequests),
      tmin: forkJoin(tminRequests),
      precipitation: forkJoin(precipRequests),
      city: this.climateMapService.getNearestCity(
        this.plotData.lat,
        this.plotData.lon,
      ),
    }).subscribe({
      next: (results) => {
        this.monthlyData = {
          tmax: results.tmax.map((r) => r.value),
          tmin: results.tmin.map((r) => r.value),
          precipitation: results.precipitation.map((r) => r.value),
        };
        this.cityInfo = results.city;
        this.isLoading = false;
        this.cdr.detectChanges();
        setTimeout(() => this.renderChart(), 0);
      },
      error: (error) => {
        this.isLoading = false;
        this.error = error.error?.detail || 'Error loading climate data';
        console.error('Error loading climate data:', error);
      },
    });
  }

  private getHistoricalDataType(variable: ClimateVarKey): string {
    const variableName = CLIMATE_VAR_KEY_TO_NAME[variable];
    return `${variableName}_1970_2000_10m`;
  }

  private renderChart(): void {
    if (!this.chartCanvas?.nativeElement) {
      console.warn('Canvas not available for rendering chart');
      return;
    }

    this.destroyChart();

    const monthLabels = [
      'Jan',
      'Feb',
      'Mar',
      'Apr',
      'May',
      'Jun',
      'Jul',
      'Aug',
      'Sep',
      'Oct',
      'Nov',
      'Dec',
    ];

    const convertedTmax = this.monthlyData.tmax.map((temp) =>
      this.currentUnit === TemperatureUnit.FAHRENHEIT
        ? TemperatureUtils.celsiusToFahrenheit(temp)
        : temp,
    );
    const convertedTmin = this.monthlyData.tmin.map((temp) =>
      this.currentUnit === TemperatureUnit.FAHRENHEIT
        ? TemperatureUtils.celsiusToFahrenheit(temp)
        : temp,
    );

    const tempUnit = this.currentUnit;
    const tmaxLabel = `${CLIMATE_VAR_DISPLAY_NAMES[ClimateVarKey.T_MAX]} (${tempUnit})`;
    const tminLabel = `${CLIMATE_VAR_DISPLAY_NAMES[ClimateVarKey.T_MIN]} (${tempUnit})`;
    const precipLabel = `${CLIMATE_VAR_DISPLAY_NAMES[ClimateVarKey.PRECIPITATION]} (${CLIMATE_VAR_UNITS[ClimateVarKey.PRECIPITATION]})`;

    const config: ChartConfiguration = {
      type: 'line',
      data: {
        labels: monthLabels,
        datasets: [
          {
            label: tmaxLabel,
            data: convertedTmax,
            borderColor: 'rgb(255, 99, 132)',
            backgroundColor: 'rgba(255, 99, 132, 0.3)',
            tension: 0.4,
            fill: '+1',
            yAxisID: 'y',
          },
          {
            label: tminLabel,
            data: convertedTmin,
            borderColor: 'rgb(255, 99, 132)',
            backgroundColor: 'rgba(255, 99, 132, 0.3)',
            tension: 0.4,
            fill: false,
            yAxisID: 'y',
          },
          {
            label: precipLabel,
            data: this.monthlyData.precipitation,
            borderColor: 'rgb(54, 162, 235)',
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            tension: 0.4,
            fill: false,
            yAxisID: 'y1',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: {
            display: window.innerWidth >= 768,
            position: 'top',
          },
          title: {
            display: true,
            text: 'Climate Data by Month (10m resolution)',
          },
        },
        scales: {
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            title: {
              display: true,
              text: `Temperature (${tempUnit})`,
            },
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            min: 0,
            title: {
              display: true,
              text: precipLabel,
            },
            grid: {
              drawOnChartArea: false,
            },
          },
          x: {
            title: {
              display: true,
              text: 'Month',
            },
          },
        },
      },
    };

    this.chart = new Chart(this.chartCanvas.nativeElement, config);
  }

  private destroyChart(): void {
    if (this.chart) {
      this.chart.destroy();
      this.chart = null;
    }
  }

  onClose(): void {
    this.isVisible = false;
  }

  get displayCoordinates(): string {
    if (!this.plotData) return '';
    return `${this.plotData.lat.toFixed(4)}°, ${this.plotData.lon.toFixed(4)}°`;
  }

  get displayLocation(): string {
    if (!this.cityInfo) {
      return this.displayCoordinates;
    }
    const cityName = this.cityInfo.city_name
      .split(' ')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
    return `${cityName}, ${this.cityInfo.country_name}`;
  }
}
