import { Component, Input, Output, EventEmitter } from '@angular/core';
import { SpatialResolution } from '../../utils/enum';
import { BaseOverlaySelectComponent } from './base-overlay-select.component';

@Component({
  selector: 'app-resolution-overlay',
  standalone: true,
  imports: [BaseOverlaySelectComponent],
  template: `
    <app-base-overlay-select
      [label]="'Resolution'"
      [selectedValue]="selectedResolution"
      [options]="resolutions"
      [availableOptions]="availableResolutions"
      [show]="show"
      [trackingCategory]="'Control Selection'"
      [trackingAction]="'Resolution Change (Overlay)'"
      [getDisplayName]="getResolutionDisplayName"
      [bottomPosition]="140"
      (valueChange)="onValueChange($event)"
    ></app-base-overlay-select>
  `,
})
export class ResolutionOverlayComponent {
  @Input() selectedResolution: SpatialResolution | undefined;
  @Input() resolutions: SpatialResolution[] = [];
  @Input() availableResolutions: SpatialResolution[] = [];
  @Input() show = true;
  @Output() resolutionChange = new EventEmitter<SpatialResolution>();

  getResolutionDisplayName = (resolution: SpatialResolution): string => {
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
  };

  onValueChange(value: SpatialResolution | null): void {
    if (value !== null) {
      this.resolutionChange.emit(value);
    }
  }
}

