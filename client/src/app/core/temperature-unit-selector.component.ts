import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { FormsModule } from '@angular/forms';
import {
  TemperatureUnitService,
  TemperatureUnit,
} from './temperature-unit.service';

@Component({
  selector: 'app-temperature-unit-selector',
  standalone: true,
  imports: [CommonModule, MatButtonToggleModule, FormsModule],
  template: `
    <mat-button-toggle-group
      [value]="currentUnit"
      (change)="onUnitChange($event.value)"
      class="temperature-unit-toggle"
    >
      <mat-button-toggle [value]="TemperatureUnit.CELSIUS">
        °C
      </mat-button-toggle>
      <mat-button-toggle [value]="TemperatureUnit.FAHRENHEIT">
        °F
      </mat-button-toggle>
    </mat-button-toggle-group>
  `,
  styles: [
    `
      .temperature-unit-toggle {
        height: 32px;
        font-size: 14px;
      }

      ::ng-deep .temperature-unit-toggle .mat-button-toggle-button {
        height: 32px;
        line-height: 32px;
        padding: 0 12px;
      }

      ::ng-deep .temperature-unit-toggle .mat-button-toggle-label-content {
        line-height: 32px;
      }
    `,
  ],
})
export class TemperatureUnitSelectorComponent {
  TemperatureUnit = TemperatureUnit;
  currentUnit: TemperatureUnit;

  constructor(private temperatureUnitService: TemperatureUnitService) {
    this.currentUnit = this.temperatureUnitService.getUnit();
    this.temperatureUnitService.unit$.subscribe((unit) => {
      this.currentUnit = unit;
    });
  }

  onUnitChange(unit: TemperatureUnit): void {
    this.temperatureUnitService.setUnit(unit);
  }
}
