import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { ClimateVarKey } from '../../utils/enum';

@Component({
  selector: 'app-variable-selector-overlay',
  standalone: true,
  imports: [CommonModule, MatButtonModule],
  templateUrl: './variable-selector-overlay.component.html',
  styleUrl: './variable-selector-overlay.component.scss',
})
export class VariableSelectorOverlayComponent {
  @Input() selectedVariableType: ClimateVarKey | undefined;
  @Input() availableVariableTypes: ClimateVarKey[] = [];
  @Input() climateVariables?: Record<ClimateVarKey, any>;
  @Output() variableChange = new EventEmitter<ClimateVarKey>();

  variables: {
    key: ClimateVarKey;
    icon: string;
    shortName: string;
    isSvg?: boolean;
  }[] = [
    {
      key: ClimateVarKey.T_MAX,
      icon: 'assets/thermometer-hot.svg',
      shortName: 'Temp. Max',
      isSvg: true,
    },
    {
      key: ClimateVarKey.T_MIN,
      icon: 'assets/thermometer-cold.svg',
      shortName: 'Temp. Min',
      isSvg: true,
    },
    {
      key: ClimateVarKey.PRECIPITATION,
      icon: 'assets/precipitation.svg',
      shortName: 'Precipitation',
      isSvg: true,
    },
    {
      key: ClimateVarKey.CLOUD_COVER,
      icon: 'assets/cloud-cover.svg',
      shortName: 'Cloud Cover',
      isSvg: true,
    },
    {
      key: ClimateVarKey.WET_DAYS,
      icon: 'assets/wet-days.svg',
      shortName: 'Wet Days',
      isSvg: true,
    },
  ];

  onVariableClick(variableType: ClimateVarKey): void {
    if (this.isAvailable(variableType)) {
      this.variableChange.emit(variableType);
    }
  }

  isAvailable(variableType: ClimateVarKey): boolean {
    return this.availableVariableTypes.includes(variableType);
  }

  isSelected(variableType: ClimateVarKey): boolean {
    return this.selectedVariableType === variableType;
  }
}
