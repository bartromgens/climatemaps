import { Injectable } from '@angular/core';
import { Map } from 'leaflet';
import { TooltipManagerService } from './tooltip-manager.service';
import { TemperatureUnitService } from '../../core/temperature-unit.service';
import { PrecipitationUnitService } from '../../core/precipitation-unit.service';
import { ClimateVarKey } from '../../utils/enum';
import { UnitUtils } from '../../utils/unit-utils';

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
    const { value: convertedValue, displayUnit } =
      UnitUtils.convertValueAndGetDisplayUnit(
        value,
        unit,
        variableType as ClimateVarKey,
        this.temperatureUnitService.getUnit(),
        this.precipitationUnitService.getUnit(),
      );
    value = convertedValue;

    // Tooltip disabled - service kept for debugging
    // const displayValue = `${value.toFixed(1)} ${displayUnit}`;
    // this.tooltipManager.createHoverTooltip(displayValue, e.latlng, map);
  }

  handleVectorLayerMouseOut(map: Map): void {
    this.tooltipManager.removeHoverTooltip(map);
  }
}
