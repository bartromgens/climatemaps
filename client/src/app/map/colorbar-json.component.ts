import {
  Component,
  Input,
  OnInit,
  OnChanges,
  SimpleChanges,
  ViewChild,
  ElementRef,
  AfterViewInit,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  ClimateMapService,
  ColorbarConfigResponse,
} from '../core/climatemap.service';

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
          [width]="canvasWidth"
          [height]="canvasHeight"
        ></canvas>
        <div class="colorbar-ticks">
          <div
            *ngFor="let tick of ticks"
            class="colorbar-tick"
            [style.top.px]="tick.position"
          >
            <div class="colorbar-tick-line-wrapper">
              <div class="colorbar-tick-line"></div>
            </div>
            <div class="colorbar-tick-label">
              {{ tick.value | number: '1.1-1' }}
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .colorbar-container {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
      }

      .colorbar-wrapper {
        display: flex;
        flex-direction: row;
        align-items: flex-start;
        position: relative;
      }

      .colorbar-canvas {
        width: 20px;
        height: 300px;
        display: block;
        border: 1px solid rgba(0, 0, 0, 0.1);
        box-sizing: border-box;
      }

      .colorbar-ticks {
        position: relative;
        height: 300px;
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

      @media (max-width: 768px) {
        .colorbar-canvas {
          width: 50px;
        }
      }
    `,
  ],
})
export class ColorbarJsonComponent implements OnInit, OnChanges, AfterViewInit {
  @Input() dataType: string | null = null;
  @Input() numTicks = 11;

  @ViewChild('colorbarCanvas') canvasRef?: ElementRef<HTMLCanvasElement>;

  colorbarConfig: ColorbarConfigResponse | null = null;
  canvasWidth = 20;
  canvasHeight = 300;
  ticks: { value: number; position: number }[] = [];

  constructor(private climateMapService: ClimateMapService) {}

  ngOnInit(): void {
    if (this.dataType) {
      this.fetchColorbarConfig();
    }
  }

  ngAfterViewInit(): void {
    this.drawColorbarOnNextTick();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['dataType']) {
      if (this.dataType) {
        this.fetchColorbarConfig();
      } else {
        this.colorbarConfig = null;
        this.ticks = [];
      }
    }
    if (changes['numTicks'] && this.colorbarConfig) {
      this.calculateTicks();
    }
  }

  private fetchColorbarConfig(): void {
    if (!this.dataType) {
      return;
    }

    this.climateMapService.getColorbarConfig(this.dataType).subscribe({
      next: (config: ColorbarConfigResponse) => {
        this.colorbarConfig = config;
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
    setTimeout(() => {
      if (this.canvasRef && this.colorbarConfig) {
        this.drawColorbar();
      }
    }, 0);
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
    const barWidth = this.canvasWidth;
    const barHeight = this.canvasHeight;

    ctx.clearRect(0, 0, barWidth, barHeight);

    const gradient = ctx.createLinearGradient(0, barHeight, 0, 0);

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
    ctx.fillRect(0, 0, barWidth, barHeight);

    ctx.strokeStyle = 'rgba(0, 0, 0, 0.3)';
    ctx.lineWidth = 1;
    ctx.strokeRect(0, 0, barWidth, barHeight);
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
      const pixelPosition = (1 - position) * (this.canvasHeight - 4) + 2;
      this.ticks.push({ value, position: pixelPosition });
    }
  }
}
