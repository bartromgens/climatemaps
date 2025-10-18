import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ClimateVarKey } from '../../utils/enum';

@Component({
  selector: 'app-variable-selector-overlay',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatTooltipModule],
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
  }[] = [
    {
      key: ClimateVarKey.T_MAX,
      icon: '🌡️',
      shortName: 'Tmax',
    },
    {
      key: ClimateVarKey.T_MIN,
      icon: '❄️',
      shortName: 'Tmin',
    },
    {
      key: ClimateVarKey.PRECIPITATION,
      icon: '💧',
      shortName: 'Precip.',
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

  getTooltip(variableType: ClimateVarKey): string {
    const variable = this.climateVariables?.[variableType];
    if (variable) {
      return `${variable.displayName} (${variable.unit})`;
    }
    return '';
  }
}
