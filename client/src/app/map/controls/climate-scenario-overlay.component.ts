import { Component, inject, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import {
  ClimateScenario,
  CLIMATE_SCENARIO_DISPLAY_NAMES,
} from '../../utils/enum';
import { MatomoTracker } from 'ngx-matomo-client';

@Component({
  selector: 'app-climate-scenario-overlay',
  standalone: true,
  imports: [CommonModule, FormsModule, MatFormFieldModule, MatSelectModule],
  templateUrl: './climate-scenario-overlay.component.html',
  styleUrl: './climate-scenario-overlay.component.scss',
})
export class ClimateScenarioOverlayComponent {
  private readonly tracker = inject(MatomoTracker);

  @Input() selectedClimateScenario: ClimateScenario | null = null;
  @Input() climateScenarios: ClimateScenario[] = [];
  @Input() availableClimateScenarios: ClimateScenario[] = [];
  @Input() show = false;
  @Output() climateScenarioChange = new EventEmitter<ClimateScenario | null>();

  onClimateScenarioChange(event: any): void {
    const scenario = event.value as ClimateScenario | null;
    this.climateScenarioChange.emit(scenario);

    if (scenario) {
      const scenarioName = this.getClimateScenarioDisplayName(scenario);
      this.tracker.trackEvent(
        'Control Selection',
        'Climate Scenario Change (Overlay)',
        scenarioName,
      );
    }
  }

  getClimateScenarioDisplayName(scenario: ClimateScenario): string {
    return CLIMATE_SCENARIO_DISPLAY_NAMES[scenario] || scenario;
  }
}
