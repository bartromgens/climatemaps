import { Component, inject, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { ClimateVarKey } from '../../../utils/enum';
import { MatomoTracker } from 'ngx-matomo-client';

@Component({
  selector: 'app-variable-selector-overlay',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule],
  templateUrl: './variable-selector-overlay.component.html',
  styleUrl: './variable-selector-overlay.component.scss',
})
export class VariableSelectorOverlayComponent {
  private readonly tracker = inject(MatomoTracker);

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
      shortName: 'Temp. (Day)',
      isSvg: true,
    },
    {
      key: ClimateVarKey.T_MIN,
      icon: 'assets/thermometer-cold.svg',
      shortName: 'Temp. (Night)',
      isSvg: true,
    },
    {
      key: ClimateVarKey.APPARENT_TEMPERATURE,
      icon: 'assets/apparent-temperature.svg',
      shortName: 'Feels Like',
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
      key: ClimateVarKey.WIND_SPEED,
      icon: 'air',
      shortName: 'Wind Speed',
      isSvg: false,
    },
    {
      key: ClimateVarKey.RELATIVE_HUMIDITY,
      icon: 'assets/relative-humidity.svg',
      shortName: 'Humidity',
      isSvg: true,
    },
    {
      key: ClimateVarKey.RADIATION,
      icon: 'assets/radiation.svg',
      shortName: 'Radiation',
      isSvg: true,
    },
    {
      key: ClimateVarKey.MOISTURE_INDEX,
      icon: 'assets/moisture-index.svg',
      shortName: 'Moisture Index',
      isSvg: true,
    },
    {
      key: ClimateVarKey.POTENTIAL_EVAPOTRANSPIRATION,
      icon: 'assets/potential-evapotranspiration.svg',
      shortName: 'Evapotranspiration',
      isSvg: true,
    },
    {
      key: ClimateVarKey.VAPOUR_PRESSURE_DEFICIT,
      icon: 'assets/vapour-pressure-deficit.svg',
      shortName: 'Vapour Pressure Deficit',
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
