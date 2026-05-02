import { ClimateVarKey } from './enum';

export const CLIMATE_VARIABLE_DESCRIPTIONS: Record<ClimateVarKey, string> = {
  [ClimateVarKey.T_MAX]:
    'Average daily maximum (daytime) temperature for the selected month. Useful for understanding warm-season heat and growing conditions.',
  [ClimateVarKey.T_MIN]:
    'Average daily minimum (nighttime) temperature for the selected month. A key indicator of frost risk and cold-season conditions.',
  [ClimateVarKey.PRECIPITATION]:
    'Total monthly precipitation (rain and snow) for the selected month. Reflects the amount of water delivered to the surface.',
  [ClimateVarKey.CLOUD_COVER]:
    'Average fraction of the sky covered by clouds during the selected month. High values indicate overcast conditions; low values indicate clear skies.',
  [ClimateVarKey.RADIATION]:
    'Average monthly solar radiation reaching the surface. Determines the energy available for heating and plant growth.',
  [ClimateVarKey.WIND_SPEED]:
    'Average wind speed at 10 m above the surface for the selected month. Higher values indicate windier conditions.',
  [ClimateVarKey.DIURNAL_TEMP_RANGE]:
    'Difference between the average daily maximum and minimum temperature. Large values indicate big swings between day and night temperatures.',
  [ClimateVarKey.VAPOUR_PRESSURE]:
    'Average atmospheric water vapour pressure for the selected month. A direct measure of the amount of moisture in the air.',
  [ClimateVarKey.VAPOUR_PRESSURE_DEFICIT]:
    'Difference between how much water vapour the air can hold and how much it actually holds. High values indicate dry, evaporative conditions.',
  [ClimateVarKey.RELATIVE_HUMIDITY]:
    'Average relative humidity for the selected month. Expressed as a percentage of the maximum moisture the air can hold at that temperature.',
  [ClimateVarKey.POTENTIAL_EVAPOTRANSPIRATION]:
    'The maximum amount of water that could evaporate from the surface and transpire from plants, given enough water supply, computed with the Penman–Monteith method. A measure of atmospheric drying power.',
  [ClimateVarKey.MOISTURE_INDEX]:
    'Balance between precipitation and potential evapotranspiration. Positive values indicate wet conditions; negative values indicate dry conditions.',
};

const assertAllVariablesHaveDescriptions = (): void => {
  const enumValues = Object.values(ClimateVarKey);
  const missing = enumValues.filter(
    (key) => !(key in CLIMATE_VARIABLE_DESCRIPTIONS),
  );
  if (missing.length > 0) {
    throw new Error(
      `Missing descriptions for climate variables: ${missing.join(', ')}. ` +
        `Please add entries to CLIMATE_VARIABLE_DESCRIPTIONS.`,
    );
  }
};

assertAllVariablesHaveDescriptions();
