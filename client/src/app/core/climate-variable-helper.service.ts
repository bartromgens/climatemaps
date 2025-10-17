import { Injectable } from '@angular/core';
import { ClimateVarKey } from '../utils/enum';

@Injectable({
  providedIn: 'root',
})
export class ClimateVariableHelperService {
  private readonly VARIABLES_WITH_FUTURE_PREDICTIONS: ClimateVarKey[] = [
    ClimateVarKey.T_MAX,
    ClimateVarKey.T_MIN,
    ClimateVarKey.PRECIPITATION,
  ];

  hasFuturePredictions(variableType: ClimateVarKey): boolean {
    return this.VARIABLES_WITH_FUTURE_PREDICTIONS.includes(variableType);
  }

  getVariablesWithFuturePredictions(): ClimateVarKey[] {
    return [...this.VARIABLES_WITH_FUTURE_PREDICTIONS];
  }
}
