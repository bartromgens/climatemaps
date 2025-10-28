import { Injectable } from '@angular/core';
import { Map } from 'leaflet';
import { TooltipManagerService } from './tooltip-manager.service';
import { TemperatureUnitService } from '../../core/temperature-unit.service';
import { TemperatureUtils } from '../../utils/temperature-utils';
import { PrecipitationUnitService } from '../../core/precipitation-unit.service';
import { PrecipitationUtils } from '../../utils/precipitation-utils';
import { ClimateVarKey } from '../../utils/enum';

@Injectable({
  providedIn: 'root',
})
export class VectorLayerTooltipService {
  constructor(
    private tooltipManager: TooltipManagerService,
    private temperatureUnitService: TemperatureUnitService,
    private precipitationUnitService: PrecipitationUnitService,
  ) {}

  handleVectorLayerHover(
    e: any,
    map: Map,
    variableType: ClimateVarKey | string,
    unit: string,
  ): void {
    const properties = e.layer?.properties;
    if (!properties || properties['level-value'] === undefined) {
      return;
    }

    let value = properties['level-value'];
    let displayUnit = unit;

    const isTemperature = TemperatureUtils.isTemperatureVariable(
      variableType as ClimateVarKey,
    );

    if (isTemperature && displayUnit === '°C') {
      const currentUnit = this.temperatureUnitService.getUnit();
      if (currentUnit === '°F') {
        value = TemperatureUtils.celsiusToFahrenheit(value);
        displayUnit = '°F';
      }
    }

    const isPrecipitation = PrecipitationUtils.isPrecipitationVariable(
      variableType as ClimateVarKey,
    );

    if (isPrecipitation && displayUnit === 'mm/month') {
      const currentUnit = this.precipitationUnitService.getUnit();
      if (currentUnit === 'in') {
        value = PrecipitationUtils.mmToInches(value);
        displayUnit = 'in/month';
      }
    }

    const displayValue = `${value.toFixed(1)} ${displayUnit}`;
    this.tooltipManager.createHoverTooltip(displayValue, e.latlng, map);
  }

  handleVectorLayerMouseOut(map: Map): void {
    this.tooltipManager.removeHoverTooltip(map);
  }
}
