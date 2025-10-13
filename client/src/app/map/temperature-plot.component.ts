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

import { ClimateMapService } from '../core/climatemap.service';

Chart.register(...registerables);

interface PlotData {
  lat: number;
  lon: number;
  dataType: string;
}

@Component({
  selector: 'app-temperature-plot',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule, MatButtonModule],
  templateUrl: './temperature-plot.component.html',
  styleUrl: './temperature-plot.component.scss',
})
export class TemperaturePlotComponent
  implements OnChanges, AfterViewInit, OnDestroy
{
  @Input() plotData: PlotData | null = null;
  @Input() variableName: string = 'Temperature';
  @Input() unit: string = '°C';

  @ViewChild('chartCanvas', { static: false })
  chartCanvas!: ElementRef<HTMLCanvasElement>;

  chart: Chart | null = null;
  isLoading: boolean = false;
  error: string | null = null;
  temperatures: number[] = [];

  constructor(
    private climateMapService: ClimateMapService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngAfterViewInit(): void {
    if (this.plotData) {
      this.loadData();
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['plotData'] && !changes['plotData'].firstChange) {
      if (this.plotData) {
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

    const requests = [];
    for (let month = 1; month <= 12; month++) {
      requests.push(
        this.climateMapService.getClimateValue(
          this.plotData.dataType,
          month,
          this.plotData.lat,
          this.plotData.lon,
        ),
      );
    }

    forkJoin(requests).subscribe({
      next: (responses) => {
        this.temperatures = responses.map((r) => r.value);
        if (responses.length > 0) {
          this.variableName = responses[0].variable_name;
          this.unit = responses[0].unit;
        }
        this.isLoading = false;
        this.cdr.detectChanges();
        setTimeout(() => this.renderChart(), 0);
      },
      error: (error) => {
        this.isLoading = false;
        this.error = error.error?.detail || 'Error loading temperature data';
        console.error('Error loading temperature data:', error);
      },
    });
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

    const config: ChartConfiguration = {
      type: 'line',
      data: {
        labels: monthLabels,
        datasets: [
          {
            label: `${this.variableName} (${this.unit})`,
            data: this.temperatures,
            borderColor: 'rgb(75, 192, 192)',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            tension: 0.4,
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top',
          },
          title: {
            display: true,
            text: `${this.variableName} by Month`,
          },
        },
        scales: {
          y: {
            title: {
              display: true,
              text: `${this.variableName} (${this.unit})`,
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

  get displayCoordinates(): string {
    if (!this.plotData) return '';
    return `${this.plotData.lat.toFixed(4)}°, ${this.plotData.lon.toFixed(4)}°`;
  }
}
