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
  ClimateValueResponse,
} from '../../core/climatemap.service';
import {
  ClimateVarKey,
  CLIMATE_VAR_KEY_TO_NAME,
  CLIMATE_VAR_DISPLAY_NAMES,
  CLIMATE_VAR_UNITS,
  ClimateScenario,
  ClimateModel,
} from '../../utils/enum';
import {
  TemperatureUnitService,
  TemperatureUnit,
} from '../../core/temperature-unit.service';
import { TemperatureUtils } from '../../utils/temperature-utils';

Chart.register(...registerables);

interface PlotData {
  lat: number;
  lon: number;
  month: number;
}

interface TimeRangeData {
  yearRange: [number, number];
  label: string;
  tmax: number;
  tmin: number;
  precipitation: number;
}

@Component({
  selector: 'app-climate-timerange-plot',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule, MatButtonModule],
  templateUrl: './climate-timerange-plot.component.html',
  styleUrl: './climate-timerange-plot.component.scss',
})
export class ClimateTimerangePlotComponent
  implements OnChanges, AfterViewInit, OnDestroy
{
  @Input() plotData: PlotData | null = null;

  @ViewChild('chartCanvas', { static: false })
  chartCanvas!: ElementRef<HTMLCanvasElement>;

  chart: Chart | null = null;
  isLoading = false;
  error: string | null = null;
  isVisible = true;
  timeRangeData: TimeRangeData[] = [];
  cityInfo: NearestCityResponse | null = null;
  private currentUnit: TemperatureUnit = TemperatureUnit.CELSIUS;

  private readonly HISTORICAL_RANGE: [number, number] = [1970, 2000];
  private readonly FUTURE_RANGES: [number, number][] = [
    [2021, 2040],
    [2041, 2060],
    [2061, 2080],
    [2081, 2100],
  ];
  private readonly DEFAULT_SCENARIO = ClimateScenario.SSP370;
  private readonly DEFAULT_MODEL = ClimateModel.ENSEMBLE_MEAN;

  constructor(
    private climateMapService: ClimateMapService,
    private cdr: ChangeDetectorRef,
    private temperatureUnitService: TemperatureUnitService,
  ) {
    this.temperatureUnitService.unit$.subscribe((unit) => {
      this.currentUnit = unit;
      if (this.chart && this.timeRangeData.length > 0) {
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

    const allRanges = [this.HISTORICAL_RANGE, ...this.FUTURE_RANGES];
    const requests: Record<
      string,
      | ReturnType<typeof this.climateMapService.getClimateValue>
      | ReturnType<typeof this.climateMapService.getNearestCity>
    > = {};

    allRanges.forEach((yearRange) => {
      const key = `${yearRange[0]}_${yearRange[1]}`;
      const isFuture = yearRange[0] >= 2000;

      const tmaxDataType = this.getDataType(
        ClimateVarKey.T_MAX,
        yearRange,
        isFuture,
      );
      const tminDataType = this.getDataType(
        ClimateVarKey.T_MIN,
        yearRange,
        isFuture,
      );
      const precipDataType = this.getDataType(
        ClimateVarKey.PRECIPITATION,
        yearRange,
        isFuture,
      );

      requests[`${key}_tmax`] = this.climateMapService.getClimateValue(
        tmaxDataType,
        this.plotData!.month,
        this.plotData!.lat,
        this.plotData!.lon,
      );
      requests[`${key}_tmin`] = this.climateMapService.getClimateValue(
        tminDataType,
        this.plotData!.month,
        this.plotData!.lat,
        this.plotData!.lon,
      );
      requests[`${key}_precip`] = this.climateMapService.getClimateValue(
        precipDataType,
        this.plotData!.month,
        this.plotData!.lat,
        this.plotData!.lon,
      );
    });

    requests['city'] = this.climateMapService.getNearestCity(
      this.plotData.lat,
      this.plotData.lon,
    );

    forkJoin(requests).subscribe({
      next: (
        results: Record<string, ClimateValueResponse | NearestCityResponse>,
      ) => {
        const historicalKey = `${this.HISTORICAL_RANGE[0]}_${this.HISTORICAL_RANGE[1]}`;
        const historicalTmax = (
          results[`${historicalKey}_tmax`] as ClimateValueResponse
        ).value;
        const historicalTmin = (
          results[`${historicalKey}_tmin`] as ClimateValueResponse
        ).value;
        const historicalPrecip = (
          results[`${historicalKey}_precip`] as ClimateValueResponse
        ).value;

        this.timeRangeData = allRanges.map((yearRange) => {
          const key = `${yearRange[0]}_${yearRange[1]}`;
          const tmax = (results[`${key}_tmax`] as ClimateValueResponse).value;
          const tmin = (results[`${key}_tmin`] as ClimateValueResponse).value;
          const precipitation = (
            results[`${key}_precip`] as ClimateValueResponse
          ).value;

          return {
            yearRange,
            label: `${yearRange[0]}-${yearRange[1]}`,
            tmax: tmax - historicalTmax,
            tmin: tmin - historicalTmin,
            precipitation: precipitation - historicalPrecip,
          };
        });

        this.cityInfo = results['city'] as NearestCityResponse;
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

  private getDataType(
    variable: ClimateVarKey,
    yearRange: [number, number],
    isFuture: boolean,
  ): string {
    const variableName = CLIMATE_VAR_KEY_TO_NAME[variable];
    const resolution = '10m';

    if (isFuture) {
      const scenario = this.DEFAULT_SCENARIO.toLowerCase();
      const model = this.DEFAULT_MODEL.toLowerCase();
      return `${variableName}_${yearRange[0]}_${yearRange[1]}_${resolution}_${scenario}_${model}`;
    } else {
      return `${variableName}_${yearRange[0]}_${yearRange[1]}_${resolution}`;
    }
  }

  private renderChart(): void {
    if (!this.chartCanvas?.nativeElement) {
      console.warn('Canvas not available for rendering chart');
      return;
    }

    this.destroyChart();

    const labels = this.timeRangeData.map((d) => d.label);

    const convertedTmax = this.timeRangeData.map((d) =>
      this.currentUnit === TemperatureUnit.FAHRENHEIT
        ? TemperatureUtils.celsiusToFahrenheit(d.tmax)
        : d.tmax,
    );
    const convertedTmin = this.timeRangeData.map((d) =>
      this.currentUnit === TemperatureUnit.FAHRENHEIT
        ? TemperatureUtils.celsiusToFahrenheit(d.tmin)
        : d.tmin,
    );

    const tempUnit = this.currentUnit;
    const tmaxLabel = `${CLIMATE_VAR_DISPLAY_NAMES[ClimateVarKey.T_MAX]} Change (${tempUnit})`;
    const tminLabel = `${CLIMATE_VAR_DISPLAY_NAMES[ClimateVarKey.T_MIN]} Change (${tempUnit})`;
    const precipLabel = `${CLIMATE_VAR_DISPLAY_NAMES[ClimateVarKey.PRECIPITATION]} Change (${CLIMATE_VAR_UNITS[ClimateVarKey.PRECIPITATION]})`;

    const config: ChartConfiguration = {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: tmaxLabel,
            data: convertedTmax,
            borderColor: 'rgb(255, 99, 132)',
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            tension: 0.4,
            fill: false,
            yAxisID: 'y',
          },
          {
            label: tminLabel,
            data: convertedTmin,
            borderColor: 'rgb(255, 159, 64)',
            backgroundColor: 'rgba(255, 159, 64, 0.2)',
            tension: 0.4,
            fill: false,
            yAxisID: 'y',
          },
          {
            label: precipLabel,
            data: this.timeRangeData.map((d) => d.precipitation),
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
            text: `Climate Change Over Time (${this.getMonthName(this.plotData?.month || 1)})`,
          },
        },
        scales: {
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            title: {
              display: true,
              text: `Temperature Change (${tempUnit})`,
            },
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            title: {
              display: true,
              text: `Precipitation Change (${CLIMATE_VAR_UNITS[ClimateVarKey.PRECIPITATION]})`,
            },
            grid: {
              drawOnChartArea: false,
            },
          },
          x: {
            title: {
              display: true,
              text: 'Time Period',
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

  private getMonthName(month: number): string {
    const monthNames = [
      'January',
      'February',
      'March',
      'April',
      'May',
      'June',
      'July',
      'August',
      'September',
      'October',
      'November',
      'December',
    ];
    return monthNames[month - 1] || '';
  }
}
