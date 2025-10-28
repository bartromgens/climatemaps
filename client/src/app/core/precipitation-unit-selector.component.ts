import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { FormsModule } from '@angular/forms';
import {
  PrecipitationUnitService,
  PrecipitationUnit,
} from './precipitation-unit.service';

@Component({
  selector: 'app-precipitation-unit-selector',
  standalone: true,
  imports: [CommonModule, MatButtonToggleModule, FormsModule],
  template: `
    <mat-button-toggle-group
      [value]="currentUnit"
      (change)="onUnitChange($event.value)"
      class="precipitation-unit-toggle"
    >
      <mat-button-toggle [value]="PrecipitationUnit.MM"> mm </mat-button-toggle>
      <mat-button-toggle [value]="PrecipitationUnit.INCHES">
        in
      </mat-button-toggle>
    </mat-button-toggle-group>
  `,
  styles: [
    `
      .precipitation-unit-toggle {
        height: 32px;
        font-size: 14px;
      }

      ::ng-deep .precipitation-unit-toggle .mat-button-toggle-button {
        height: 32px;
        line-height: 32px;
        padding: 0 12px;
      }

      ::ng-deep .precipitation-unit-toggle .mat-button-toggle-label-content {
        line-height: 32px;
      }
    `,
  ],
})
export class PrecipitationUnitSelectorComponent {
  PrecipitationUnit = PrecipitationUnit;
  currentUnit: PrecipitationUnit;

  constructor(private precipitationUnitService: PrecipitationUnitService) {
    this.currentUnit = this.precipitationUnitService.getUnit();
    this.precipitationUnitService.unit$.subscribe((unit) => {
      this.currentUnit = unit;
    });
  }

  onUnitChange(unit: PrecipitationUnit): void {
    this.precipitationUnitService.setUnit(unit);
  }
}
