import { Component, inject, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { SpatialResolution } from '../../utils/enum';
import { MatomoTracker } from 'ngx-matomo-client';

@Component({
  selector: 'app-resolution-overlay',
  standalone: true,
  imports: [CommonModule, FormsModule, MatFormFieldModule, MatSelectModule],
  templateUrl: './resolution-overlay.component.html',
  styleUrl: './resolution-overlay.component.scss',
})
export class ResolutionOverlayComponent {
  private readonly tracker = inject(MatomoTracker);

  @Input() selectedResolution: SpatialResolution | undefined;
  @Input() resolutions: SpatialResolution[] = [];
  @Input() availableResolutions: SpatialResolution[] = [];
  @Input() show = true;
  @Output() resolutionChange = new EventEmitter<SpatialResolution>();

  onResolutionChange(event: any): void {
    const resolution = event.value as SpatialResolution;
    this.resolutionChange.emit(resolution);

    const resolutionName = this.getResolutionDisplayName(resolution);
    this.tracker.trackEvent(
      'Control Selection',
      'Resolution Change (Overlay)',
      resolutionName,
    );
  }

  getResolutionDisplayName(resolution: SpatialResolution): string {
    switch (resolution) {
      case SpatialResolution.MIN30:
        return 'Low';
      case SpatialResolution.MIN10:
        return 'Medium';
      case SpatialResolution.MIN5:
        return 'High';
      case SpatialResolution.MIN2_5:
        return 'Very High';
      default:
        return resolution;
    }
  }
}

