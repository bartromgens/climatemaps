import { ClimateVarKey } from './enum';

export class TemperatureUtils {
  static isTemperatureVariable(variable: ClimateVarKey): boolean {
    return (
      variable === ClimateVarKey.T_MAX ||
      variable === ClimateVarKey.T_MIN ||
      variable === ClimateVarKey.DIURNAL_TEMP_RANGE
    );
  }

  static celsiusToFahrenheit(celsius: number): number {
    return (celsius * 9) / 5 + 32;
  }

  static fahrenheitToCelsius(fahrenheit: number): number {
    return ((fahrenheit - 32) * 5) / 9;
  }
}
