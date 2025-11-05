import {
  Component,
  Input,
  OnInit,
  OnChanges,
  SimpleChanges,
} from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-colorbar',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="colorbar-container" *ngIf="colorbarUrl">
      <img
        [src]="colorbarUrl"
        [alt]="colorbarAlt"
        class="colorbar-image"
        (error)="onImageError($event)"
      />
    </div>
  `,
  styles: [
    `
      .colorbar-container {
        max-width: 60px;
      }

      .colorbar-image {
        max-width: 100%;
        height: auto;
        display: block;
      }

      @media (max-width: 768px) {
        .colorbar-container {
          bottom: 105px;
          right: auto;
          left: 5px;
          max-width: 50px;
          background: rgba(255, 255, 255, 0);
          box-shadow: 0 2px 10px rgba(0, 0, 0, 0);
        }
      }
    `,
  ],
})
export class ColorbarComponent implements OnInit, OnChanges {
  @Input() colormapUrl: string | null = null;
  @Input() displayName: string | null = null;
  @Input() selectedMonth = 1;

  colorbarUrl: string | null = null;
  colorbarAlt = '';

  ngOnInit(): void {
    this.updateColorbar();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (
      changes['colormapUrl'] ||
      changes['displayName'] ||
      changes['selectedMonth']
    ) {
      this.updateColorbar();
    }
  }

  private updateColorbar(): void {
    if (this.colormapUrl && this.displayName) {
      this.colorbarUrl = `${this.colormapUrl}/${this.selectedMonth}`;
      this.colorbarAlt = `Colorbar for ${this.displayName} - Month ${this.selectedMonth}`;
    } else {
      this.colorbarUrl = null;
      this.colorbarAlt = '';
    }
  }

  onImageError(event: any): void {
    console.warn('Failed to load colorbar image:', event);
    this.colorbarUrl = null;
  }
}
