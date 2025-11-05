import {
  Component,
  Input,
  OnInit,
  OnChanges,
  SimpleChanges,
  ViewChild,
  ElementRef,
  AfterViewInit,
  OnDestroy,
  ChangeDetectorRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription, combineLatest } from 'rxjs';
import {
  ClimateMapService,
  ColorbarConfigResponse,
} from '../core/climatemap.service';
import {
  TemperatureUnitService,
  TemperatureUnit,
} from '../core/temperature-unit.service';
import {
  PrecipitationUnitService,
  PrecipitationUnit,
} from '../core/precipitation-unit.service';
import { TemperatureUtils } from '../utils/temperature-utils';
import { PrecipitationUtils } from '../utils/precipitation-utils';
import { getClimateVarKeyFromDataType } from '../utils/enum';

@Component({
  selector: 'app-colorbar-json',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="colorbar-container" *ngIf="colorbarConfig">
      <div class="colorbar-wrapper">
        <canvas
          #colorbarCanvas
          class="colorbar-canvas"
          [width]="width"
          [height]="height"
          [style.width.px]="width"
          [style.height.px]="height"
        ></canvas>
        <div class="colorbar-ticks" [style.height.px]="height">
          <div
            *ngFor="let tick of ticks"
            class="colorbar-tick"
            [style.top.px]="tick.position"
          >
            <div class="colorbar-tick-line-wrapper">
              <div class="colorbar-tick-line"></div>
            </div>
            <div class="colorbar-tick-label">
              {{ getDisplayValue(tick.value) | number: '1.0-1' }}
            </div>
          </div>
        </div>
        <div
          *ngIf="showLabel"
          class="colorbar-label"
          [style.height.px]="height"
        >
          {{ colorbarConfig.title }} [{{ getDisplayUnit() }}]
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      :host {
        position: fixed;
        bottom: 130px;
        left: 6px;
        background: rgba(255, 255, 255, 0.4);
        border-radius: 8px;
        padding: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        z-index: 1000;
        display: inline-flex;
        align-items: flex-start;
        width: 56px;
        max-width: none;
        overflow: visible;
      }

      @media (max-width: 768px) {
        :host {
          bottom: 105px;
          left: 5px;
          background: rgba(255, 255, 255, 0);
          box-shadow: 0 2px 10px rgba(0, 0, 0, 0);
        }
      }

      .colorbar-container {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        overflow: visible;
      }

      .colorbar-wrapper {
        display: flex;
        flex-direction: row;
        align-items: flex-start;
        position: relative;
        overflow: visible;
      }

      .colorbar-canvas {
        display: block;
        border: 1px solid rgba(0, 0, 0, 0.1);
        box-sizing: border-box;
      }

      .colorbar-ticks {
        position: relative;
        margin-left: 0;
      }

      .colorbar-tick {
        position: absolute;
        display: flex;
        align-items: center;
        transform: translateY(-50%);
        left: -1px;
      }

      .colorbar-tick-line-wrapper {
        position: relative;
        width: 6px;
        height: 1px;
        margin-right: 4px;
      }

      .colorbar-tick-line {
        position: absolute;
        left: 0;
        width: 6px;
        height: 1px;
        background-color: #333;
      }

      .colorbar-tick-label {
        font-size: 11px;
        color: #333;
        white-space: nowrap;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
          'Helvetica Neue', Arial, sans-serif;
      }

      .colorbar-label {
        position: absolute;
        left: 52px;
        top: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        color: #333;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
          'Helvetica Neue', Arial, sans-serif;
        white-space: nowrap;
        transform: rotate(-90deg);
        transform-origin: left center;
      }
    `,
  ],
})
export class ColorbarJsonComponent
  implements OnInit, OnChanges, AfterViewInit, OnDestroy
{
  @Input() dataType: string | null = null;
  @Input() numTicks = 11;
  @Input() height = 200;
  @Input() width = 14;
  @Input() showLabel = true;

  @ViewChild('colorbarCanvas') canvasRef?: ElementRef<HTMLCanvasElement>;

  colorbarConfig: ColorbarConfigResponse | null = null;
  ticks: { value: number; position: number }[] = [];

  private unitSubscription?: Subscription;
  private isTemperatureVariable = false;
  private isPrecipitationVariable = false;
  private currentTemperatureUnit: TemperatureUnit = TemperatureUnit.CELSIUS;
  private currentPrecipitationUnit: PrecipitationUnit = PrecipitationUnit.MM;
  private drawRetryCount = 0;
  private readonly MAX_DRAW_RETRIES = 10;

  constructor(
    private climateMapService: ClimateMapService,
    private temperatureUnitService: TemperatureUnitService,
    private precipitationUnitService: PrecipitationUnitService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.subscribeToUnitChanges();
    if (this.dataType) {
      this.updateVariableType();
      this.fetchColorbarConfig();
    }
  }

  ngOnDestroy(): void {
    if (this.unitSubscription) {
      this.unitSubscription.unsubscribe();
    }
  }

  private subscribeToUnitChanges(): void {
    this.unitSubscription = combineLatest([
      this.temperatureUnitService.unit$,
      this.precipitationUnitService.unit$,
    ]).subscribe(([tempUnit, precipUnit]) => {
      this.currentTemperatureUnit = tempUnit;
      this.currentPrecipitationUnit = precipUnit;
      if (this.colorbarConfig) {
        this.calculateTicks();
        this.cdr.markForCheck();
      }
    });
  }

  private updateVariableType(): void {
    if (!this.dataType) {
      this.isTemperatureVariable = false;
      this.isPrecipitationVariable = false;
      return;
    }

    const variableKey = getClimateVarKeyFromDataType(this.dataType);
    this.isTemperatureVariable = variableKey
      ? TemperatureUtils.isTemperatureVariable(variableKey)
      : false;
    this.isPrecipitationVariable = variableKey
      ? PrecipitationUtils.isPrecipitationVariable(variableKey)
      : false;
  }

  ngAfterViewInit(): void {
    this.drawColorbarOnNextTick();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['dataType']) {
      this.drawRetryCount = 0;
      if (this.dataType) {
        this.updateVariableType();
        this.fetchColorbarConfig();
      } else {
        this.colorbarConfig = null;
        this.ticks = [];
      }
    }
    if (changes['numTicks'] && this.colorbarConfig) {
      this.calculateTicks();
      this.drawColorbarOnNextTick();
    }
    if (changes['height']) {
      this.calculateTicks();
      this.drawColorbarOnNextTick();
    }
    if (changes['width']) {
      this.drawColorbarOnNextTick();
    }
  }

  private fetchColorbarConfig(): void {
    if (!this.dataType) {
      return;
    }

    this.climateMapService.getColorbarConfig(this.dataType).subscribe({
      next: (config: ColorbarConfigResponse) => {
        this.colorbarConfig = config;
        this.cdr.detectChanges();
        this.calculateTicks();
        this.drawColorbarOnNextTick();
      },
      error: (error: any) => {
        console.warn('Failed to load colorbar config:', error);
        this.colorbarConfig = null;
        this.ticks = [];
      },
    });
  }

  private drawColorbarOnNextTick(): void {
    this.drawRetryCount = 0;
    this.attemptDrawColorbar();
  }

  private attemptDrawColorbar(): void {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (this.canvasRef?.nativeElement && this.colorbarConfig) {
          const canvas = this.canvasRef.nativeElement;
          if (canvas.width > 0 && canvas.height > 0) {
            this.drawColorbar();
            this.drawRetryCount = 0;
          } else if (this.drawRetryCount < this.MAX_DRAW_RETRIES) {
            this.drawRetryCount++;
            setTimeout(() => this.attemptDrawColorbar(), 10);
          }
        }
      });
    });
  }

  private drawColorbar(): void {
    if (!this.canvasRef || !this.colorbarConfig) {
      return;
    }

    const canvas = this.canvasRef.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      return;
    }

    const { levels, colors } = this.colorbarConfig;
    const numLevels = levels.length;

    ctx.clearRect(0, 0, this.width, this.height);

    const gradient = ctx.createLinearGradient(0, this.height, 0, 0);

    for (let i = 0; i < numLevels; i++) {
      const position = i / (numLevels - 1);
      const color = colors[i];
      const r = Math.round(color[0] * 255);
      const g = Math.round(color[1] * 255);
      const b = Math.round(color[2] * 255);
      const a = color[3];
      gradient.addColorStop(position, `rgba(${r}, ${g}, ${b}, ${a})`);
    }

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, this.width, this.height);

    ctx.strokeStyle = 'rgba(0, 0, 0, 0.3)';
    ctx.lineWidth = 1;
    ctx.strokeRect(0, 0, this.width, this.height);
  }

  private calculateTicks(): void {
    if (!this.colorbarConfig || this.numTicks < 2) {
      this.ticks = [];
      return;
    }

    const { level_lower, level_upper, log_scale } = this.colorbarConfig;
    this.ticks = [];

    for (let i = 0; i < this.numTicks; i++) {
      const position = i / (this.numTicks - 1);
      let value: number;

      if (log_scale) {
        const logLower = Math.log10(level_lower);
        const logUpper = Math.log10(level_upper);
        const logValue = logLower + position * (logUpper - logLower);
        value = Math.pow(10, logValue);
      } else {
        value = level_lower + position * (level_upper - level_lower);
      }

      // Position calculation accounts for canvas border and tick centering:
      // - Subtracts 4px: 1px top border + 1px bottom border + 2px for tick centering at edges
      // - Adds 2px: offset for top border (1px) + half-tick-height offset (1px)
      // This ensures ticks align with the gradient fill area, not the border
      const pixelPosition = (1 - position) * (this.height - 4) + 2;
      this.ticks.push({ value, position: pixelPosition });
    }
  }

  getDisplayValue(rawValue: number): number {
    if (this.isTemperatureVariable) {
      return this.temperatureUnitService.convertTemperature(rawValue);
    }
    if (this.isPrecipitationVariable) {
      return this.precipitationUnitService.convertPrecipitation(rawValue);
    }
    return rawValue;
  }

  getDisplayUnit(): string {
    if (!this.colorbarConfig) {
      return '';
    }

    if (this.isTemperatureVariable) {
      return this.currentTemperatureUnit;
    }
    if (this.isPrecipitationVariable) {
      return this.currentPrecipitationUnit;
    }
    return this.colorbarConfig.unit;
  }
}
