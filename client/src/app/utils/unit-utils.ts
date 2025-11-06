import { ClimateVarKey } from './enum';
import { TemperatureUnit } from '../core/temperature-unit.service';
import { PrecipitationUnit } from '../core/precipitation-unit.service';
import { TemperatureUtils } from './temperature-utils';
import { PrecipitationUtils } from './precipitation-utils';

export class UnitUtils {
  static normalizeUnit(unit: string, variableType: ClimateVarKey): string {
    const isTemperature = TemperatureUtils.isTemperatureVariable(variableType);
    const isPrecipitation =
      PrecipitationUtils.isPrecipitationVariable(variableType);

    if (isTemperature) {
      if (unit === 'C' || unit === TemperatureUnit.CELSIUS) {
        return TemperatureUnit.CELSIUS;
      }
      if (unit === 'F' || unit === TemperatureUnit.FAHRENHEIT) {
        return TemperatureUnit.FAHRENHEIT;
      }
    }

    if (isPrecipitation) {
      if (unit.startsWith('mm') || unit.startsWith(PrecipitationUnit.MM)) {
        return unit.replace(/^mm/, PrecipitationUnit.MM);
      }
      if (unit.startsWith('in') || unit.startsWith(PrecipitationUnit.INCHES)) {
        return unit.replace(/^in/, PrecipitationUnit.INCHES);
      }
    }

    return unit;
  }

  static getDisplayUnit(
    unit: string,
    variableType: ClimateVarKey,
    currentTemperatureUnit: TemperatureUnit,
    currentPrecipitationUnit: PrecipitationUnit,
  ): string {
    const isTemperature = TemperatureUtils.isTemperatureVariable(variableType);
    if (isTemperature && unit === TemperatureUnit.CELSIUS) {
      return currentTemperatureUnit;
    }

    const isPrecipitation =
      PrecipitationUtils.isPrecipitationVariable(variableType);
    if (isPrecipitation && unit === 'mm/month') {
      return currentPrecipitationUnit === PrecipitationUnit.INCHES
        ? 'in/month'
        : 'mm/month';
    }

    return unit;
  }

  static convertValueAndGetDisplayUnit(
    value: number,
    unit: string,
    variableType: ClimateVarKey,
    currentTemperatureUnit: TemperatureUnit,
    currentPrecipitationUnit: PrecipitationUnit,
  ): { value: number; displayUnit: string } {
    const isTemperature = TemperatureUtils.isTemperatureVariable(variableType);
    let displayUnit = unit;

    if (isTemperature && unit === TemperatureUnit.CELSIUS) {
      if (currentTemperatureUnit === TemperatureUnit.FAHRENHEIT) {
        value = TemperatureUtils.celsiusToFahrenheit(value);
        displayUnit = TemperatureUnit.FAHRENHEIT;
      }
    }

    const isPrecipitation =
      PrecipitationUtils.isPrecipitationVariable(variableType);
    if (isPrecipitation && unit === 'mm/month') {
      if (currentPrecipitationUnit === PrecipitationUnit.INCHES) {
        value = PrecipitationUtils.mmToInches(value);
        displayUnit = 'in/month';
      }
    }

    return { value, displayUnit };
  }
}
