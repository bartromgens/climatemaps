import { Injectable } from '@angular/core';
import { LeafletMouseEvent, Map } from 'leaflet';
import {
  ClimateMapService,
  ColorbarConfigResponse,
} from '../../core/climatemap.service';
import {
  RasterColorExtractorService,
  RasterColor,
} from './raster-color-extractor.service';
import { TooltipManagerService } from './tooltip-manager.service';
import {
  TemperatureUnitService,
  TemperatureUnit,
} from '../../core/temperature-unit.service';
import {
  PrecipitationUnitService,
  PrecipitationUnit,
} from '../../core/precipitation-unit.service';
import { TemperatureUtils } from '../../utils/temperature-utils';
import { PrecipitationUtils } from '../../utils/precipitation-utils';
import { ClimateVarKey } from '../../utils/enum';
import { UnitUtils } from '../../utils/unit-utils';
import { LayerOption } from './layer-builder.service';

@Injectable({
  providedIn: 'root',
})
export class RasterTooltipService {
  private colorbarConfigCache: Record<string, ColorbarConfigResponse> = {};

  constructor(
    private rasterColorExtractor: RasterColorExtractorService,
    private tooltipManager: TooltipManagerService,
    private climateMapService: ClimateMapService,
    private temperatureUnitService: TemperatureUnitService,
    private precipitationUnitService: PrecipitationUnitService,
  ) {}

  handleMouseMove(
    event: LeafletMouseEvent,
    map: Map,
    rasterLayer: any,
    selectedOption: LayerOption | undefined,
    monthSelected: number,
    variableType: ClimateVarKey,
  ): void {
    if (!selectedOption?.metadata?.dataType) {
      this.tooltipManager.removeHoverTooltip(map);
      return;
    }

    const color = this.rasterColorExtractor.extractColorFromRasterLayer(
      event,
      map,
      rasterLayer,
      selectedOption,
      monthSelected,
    );

    if (!color || this.isBlackColor(color)) {
      this.tooltipManager.removeHoverTooltip(map);
      return;
    }

    const dataType = selectedOption.metadata.dataType;
    const cachedConfig = this.colorbarConfigCache[dataType];

    if (cachedConfig) {
      this.showTooltip(event, color, cachedConfig, map, variableType, false);
    } else {
      this.climateMapService.getColorbarConfig(dataType).subscribe({
        next: (colorbarConfig: ColorbarConfigResponse) => {
          this.colorbarConfigCache[dataType] = colorbarConfig;
          this.showTooltip(
            event,
            color,
            colorbarConfig,
            map,
            variableType,
            false,
          );
        },
        error: (error) => {
          console.warn('Failed to load colorbar config:', error);
          this.tooltipManager.removeHoverTooltip(map);
        },
      });
    }
  }

  handleMapClick(
    event: LeafletMouseEvent | { latlng: { lat: number; lng: number } },
    map: Map,
    rasterLayer: any,
    selectedOption: LayerOption | undefined,
    monthSelected: number,
    variableType: ClimateVarKey,
  ): void {
    if (!selectedOption?.metadata?.dataType) {
      return;
    }

    const color = this.rasterColorExtractor.extractColorFromRasterLayer(
      event,
      map,
      rasterLayer,
      selectedOption,
      monthSelected,
    );

    if (!color || this.isBlackColor(color)) {
      return;
    }

    const dataType = selectedOption.metadata.dataType;
    const cachedConfig = this.colorbarConfigCache[dataType];

    if (cachedConfig) {
      this.showTooltip(event, color, cachedConfig, map, variableType, true);
    } else {
      this.tooltipManager.createPersistentTooltip('...', event.latlng, map);

      this.climateMapService.getColorbarConfig(dataType).subscribe({
        next: (colorbarConfig: ColorbarConfigResponse) => {
          this.colorbarConfigCache[dataType] = colorbarConfig;
          this.showTooltip(
            event,
            color,
            colorbarConfig,
            map,
            variableType,
            true,
          );
        },
        error: (error) => {
          console.error('Failed to load colorbar config:', error);
          const errorMessage = error.error?.detail || 'Error loading value';
          this.tooltipManager.createPersistentTooltip(
            errorMessage,
            event.latlng,
            map,
          );
        },
      });
    }
  }

  private showTooltip(
    event: LeafletMouseEvent | { latlng: { lat: number; lng: number } },
    color: RasterColor,
    colorbarConfig: ColorbarConfigResponse,
    map: Map,
    variableType: ClimateVarKey,
    isPersistent: boolean,
  ): void {
    const value = this.rasterColorExtractor.getValueFromColor(
      color,
      colorbarConfig,
    );

    if (value === null) {
      if (isPersistent) {
        this.tooltipManager.createPersistentTooltip(
          'No data available',
          event.latlng,
          map,
        );
      } else {
        this.tooltipManager.removeHoverTooltip(map);
      }
      return;
    }

    const { convertedValue, unit } = this.convertValueAndUnit(
      value,
      colorbarConfig.unit,
      variableType,
    );

    let tooltipContent: string;
    const unitSpan = `<span class="tooltip-unit">${unit}</span>`;
    if (value >= colorbarConfig.level_upper) {
      tooltipContent = `>${convertedValue.toFixed(1)} ${unitSpan}`;
    } else if (value <= colorbarConfig.level_lower) {
      tooltipContent = `<${convertedValue.toFixed(1)} ${unitSpan}`;
    } else {
      tooltipContent = `${convertedValue.toFixed(1)} ${unitSpan}`;
    }

    if (isPersistent) {
      this.tooltipManager.createPersistentTooltip(
        tooltipContent,
        event.latlng,
        map,
      );
    } else {
      this.tooltipManager.createHoverTooltip(tooltipContent, event.latlng, map);
    }
  }

  private convertValueAndUnit(
    value: number,
    originalUnit: string,
    variableType: ClimateVarKey,
  ): { convertedValue: number; unit: string } {
    let convertedValue = value;
    let unit = UnitUtils.normalizeUnit(originalUnit, variableType);

    const isTemperature = TemperatureUtils.isTemperatureVariable(variableType);

    if (isTemperature && unit === TemperatureUnit.CELSIUS) {
      const currentUnit = this.temperatureUnitService.getUnit();
      if (currentUnit === TemperatureUnit.FAHRENHEIT) {
        convertedValue = TemperatureUtils.celsiusToFahrenheit(value);
        unit = TemperatureUnit.FAHRENHEIT;
      }
    }

    const isPrecipitation =
      PrecipitationUtils.isPrecipitationVariable(variableType);

    if (isPrecipitation && unit.startsWith(PrecipitationUnit.MM)) {
      const currentUnit = this.precipitationUnitService.getUnit();
      if (currentUnit === PrecipitationUnit.INCHES) {
        convertedValue = PrecipitationUtils.mmToInches(value);
        unit = unit.replace(PrecipitationUnit.MM, PrecipitationUnit.INCHES);
      }
    }

    return { convertedValue, unit };
  }

  private isBlackColor(color: RasterColor): boolean {
    return color.r === 0 && color.g === 0 && color.b === 0;
  }

  clearCache(): void {
    this.colorbarConfigCache = {};
  }
}
