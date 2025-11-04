import { Component, Input, Output, EventEmitter } from '@angular/core';
import {
  ClimateScenario,
  CLIMATE_SCENARIO_DISPLAY_NAMES,
} from '../../../utils/enum';
import { BaseOverlaySelectComponent } from './base-overlay-select.component';

@Component({
  selector: 'app-climate-scenario-overlay',
  standalone: true,
  imports: [BaseOverlaySelectComponent],
  template: `
    <app-base-overlay-select
      [label]="'Climate Scenario'"
      [selectedValue]="selectedClimateScenario"
      [options]="climateScenarios"
      [availableOptions]="availableClimateScenarios"
      [show]="show"
      [trackingCategory]="'Control Selection'"
      [trackingAction]="'Climate Scenario Change (Overlay)'"
      [getDisplayName]="getClimateScenarioDisplayName"
      [bottomPosition]="80"
      (valueChange)="onValueChange($event)"
    ></app-base-overlay-select>
  `,
})
export class ClimateScenarioOverlayComponent {
  @Input() selectedClimateScenario: ClimateScenario | null = null;
  @Input() climateScenarios: ClimateScenario[] = [];
  @Input() availableClimateScenarios: ClimateScenario[] = [];
  @Input() show = false;
  @Output() climateScenarioChange = new EventEmitter<ClimateScenario | null>();

  getClimateScenarioDisplayName = (scenario: ClimateScenario): string => {
    return CLIMATE_SCENARIO_DISPLAY_NAMES[scenario] || scenario;
  };

  onValueChange(value: ClimateScenario | null): void {
    this.climateScenarioChange.emit(value);
  }
}
