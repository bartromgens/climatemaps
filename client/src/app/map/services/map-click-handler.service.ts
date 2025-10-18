import { Injectable } from '@angular/core';
import { Map } from 'leaflet';
import {
  ClimateMapService,
  ClimateValueResponse,
} from '../../core/climatemap.service';
import { TooltipManagerService } from './tooltip-manager.service';
import { TemperatureUnitService } from '../../core/temperature-unit.service';
import { TemperatureUtils } from '../../utils/temperature-utils';
import { ClimateVarKey } from '../../utils/enum';
import { CoordinateUtils } from '../../utils/coordinate-utils';

@Injectable({
  providedIn: 'root',
})
export class MapClickHandlerService {
  constructor(
    private climateMapService: ClimateMapService,
    private tooltipManager: TooltipManagerService,
    private temperatureUnitService: TemperatureUnitService,
  ) {}

  handleMapClick(
    event: any,
    map: Map,
    dataType: string,
    month: number,
    variableType: ClimateVarKey | string,
    onSuccess?: (response: ClimateValueResponse) => void,
  ): void {
    const lat = event.latlng.lat;
    const lon = CoordinateUtils.normalizeLongitude(event.latlng.lng);

    this.tooltipManager.createPersistentTooltip('...', event.latlng, map);

    this.climateMapService
      .getClimateValue(dataType, month, lat, lon)
      .subscribe({
        next: (response: ClimateValueResponse) => {
          this.displayClickValue(event.latlng, response, map, variableType);
          onSuccess?.(response);
        },
        error: (error) => {
          console.error('Error fetching climate value:', error);
          const errorMessage = error.error?.detail || 'Error loading value';
          this.tooltipManager.createPersistentTooltip(
            errorMessage,
            event.latlng,
            map,
          );
        },
      });
  }

  private displayClickValue(
    latlng: any,
    response: ClimateValueResponse,
    map: Map,
    variableType: ClimateVarKey | string,
  ): void {
    const isTemperature = TemperatureUtils.isTemperatureVariable(
      variableType as ClimateVarKey,
    );

    let value = response.value;
    let unit = response.unit;

    if (isTemperature && unit === '°C') {
      const currentUnit = this.temperatureUnitService.getUnit();
      if (currentUnit === '°F') {
        value = TemperatureUtils.celsiusToFahrenheit(value);
        unit = '°F';
      }
    }

    const displayValue = `${value.toFixed(1)} ${unit}`;
    this.tooltipManager.createPersistentTooltip(displayValue, latlng, map);
  }
}
