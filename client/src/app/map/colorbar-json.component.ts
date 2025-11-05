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
      <div class="colorbar-label">JSON</div>
      <canvas
        #colorbarCanvas
        class="colorbar-canvas"
        [width]="canvasWidth"
        [height]="canvasHeight"
      ></canvas>
    </div>
  `,
  styles: [
    `
      .colorbar-container {
        display: flex;
        flex-direction: column;
        align-items: center;
      }

      .colorbar-label {
        font-size: 10px;
        color: #666;
        margin-bottom: 4px;
        text-align: center;
      }

      .colorbar-canvas {
        max-width: 60px;
        height: auto;
        display: block;
        border: 1px solid rgba(0, 0, 0, 0.1);
      }

      @media (max-width: 768px) {
        .colorbar-canvas {
          max-width: 50px;
        }
      }
    `,
  ],
})
export class ColorbarJsonComponent implements OnInit, OnChanges, AfterViewInit {
  @Input() dataType: string | null = null;

  @ViewChild('colorbarCanvas') canvasRef?: ElementRef<HTMLCanvasElement>;

  colorbarConfig: ColorbarConfigResponse | null = null;
  canvasWidth = 60;
  canvasHeight = 300;

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
      }
    }
  }

  private fetchColorbarConfig(): void {
    if (!this.dataType) {
      return;
    }

    this.climateMapService.getColorbarConfig(this.dataType).subscribe({
      next: (config: ColorbarConfigResponse) => {
        this.colorbarConfig = config;
        this.drawColorbarOnNextTick();
      },
      error: (error: any) => {
        console.warn('Failed to load colorbar config:', error);
        this.colorbarConfig = null;
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
}
