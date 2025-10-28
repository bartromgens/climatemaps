import { ClimateVarKey } from '../utils/enum';

export class PrecipitationUtils {
  static isPrecipitationVariable(variable: ClimateVarKey): boolean {
    return variable === ClimateVarKey.PRECIPITATION;
  }

  static mmToInches(mm: number): number {
    return mm / 25.4;
  }

  static inchesToMm(inches: number): number {
    return inches * 25.4;
  }
}
