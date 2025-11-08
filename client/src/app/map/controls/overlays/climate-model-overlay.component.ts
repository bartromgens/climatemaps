import { Component, Input, Output, EventEmitter } from '@angular/core';
import { ClimateModel, getClimateModelDisplayName } from '../../../utils/enum';
import { BaseOverlaySelectComponent } from './base-overlay-select.component';

@Component({
  selector: 'app-climate-model-overlay',
  standalone: true,
  imports: [BaseOverlaySelectComponent],
  template: `
    <app-base-overlay-select
      [label]="'Climate Model'"
      [selectedValue]="selectedClimateModel"
      [options]="climateModels"
      [availableOptions]="availableClimateModels"
      [show]="show"
      [trackingCategory]="'Control Selection'"
      [trackingAction]="'Climate Model Change (Overlay)'"
      [getDisplayName]="getClimateModelDisplayName"
      [bottomPosition]="20"
      (valueChange)="onValueChange($event)"
    ></app-base-overlay-select>
  `,
})
export class ClimateModelOverlayComponent {
  @Input() selectedClimateModel: ClimateModel | null = null;
  @Input() climateModels: ClimateModel[] = [];
  @Input() availableClimateModels: ClimateModel[] = [];
  @Input() show = false;
  @Output() climateModelChange = new EventEmitter<ClimateModel | null>();

  getClimateModelDisplayName = getClimateModelDisplayName;

  onValueChange(value: ClimateModel | null): void {
    this.climateModelChange.emit(value);
  }
}
