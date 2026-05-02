import { Routes } from '@angular/router';
import { AboutComponent } from './about.component';
import { MapComponent } from './map';
import { MonthlyGridComponent } from './map/grid/monthly-grid.component';
import { ScenarioGridComponent } from './map/grid/scenario-grid.component';
import { YearRangeGridComponent } from './map/grid/yearrange-grid.component';
import { ScenarioYearRangeGridComponent } from './map/grid/scenario-yearrange-grid.component';
import { ClimateVarKey } from './utils/enum';

/**
 * Mapping of climate variables to their SEO-friendly titles and URL paths.
 *
 * To add a new climate variable route:
 * 1. Add the new ClimateVarKey to the enum in utils/enum.ts
 * 2. Add an entry here with the desired path and title
 * 3. The route will be automatically generated
 *
 * Example:
 * [ClimateVarKey.NEW_VARIABLE]: { path: 'new-variable', title: 'New Variable Map' }
 */
const CLIMATE_VARIABLE_ROUTES: Record<
  ClimateVarKey,
  { path: string; title: string; description: string }
> = {
  [ClimateVarKey.T_MAX]: {
    path: 'temperature',
    title: 'World Temperature Map by Month – Average Monthly Temperatures',
    description:
      'Interactive world temperature map showing average monthly temperatures. Explore historical and future temperature projections by month for any location on earth.',
  },
  [ClimateVarKey.T_MIN]: {
    path: 'temperature-min',
    title: 'Minimum Temperature Map – World Monthly Minimum Temperatures',
    description:
      'Interactive minimum temperature map of the world. View average monthly minimum temperatures by location with historical data and CMIP6 climate projections.',
  },
  [ClimateVarKey.PRECIPITATION]: {
    path: 'precipitation',
    title: 'World Precipitation Map – Monthly Rainfall & Snowfall by Month',
    description:
      'Interactive world precipitation map showing monthly rainfall and snowfall. Explore average precipitation data and future projections based on CMIP6 climate scenarios.',
  },
  [ClimateVarKey.CLOUD_COVER]: {
    path: 'cloud-cover',
    title: 'Cloud Cover Map – World Monthly Cloud Cover',
    description:
      'Interactive world cloud cover map showing average monthly cloud cover by location. Explore historical data and future climate projections.',
  },
  [ClimateVarKey.RADIATION]: {
    path: 'radiation',
    title: 'Solar Radiation Map – Global Monthly Solar Radiation',
    description:
      'Interactive global solar radiation map showing average monthly solar radiation. Explore historical and projected solar radiation data worldwide.',
  },
  [ClimateVarKey.DIURNAL_TEMP_RANGE]: {
    path: 'diurnal-temperature-range',
    title: 'Diurnal Temperature Range Map – Daily Temperature Variation',
    description:
      'Interactive map of diurnal temperature range showing the difference between monthly average maximum and minimum temperatures worldwide.',
  },
  [ClimateVarKey.VAPOUR_PRESSURE]: {
    path: 'vapour-pressure',
    title: 'Vapour Pressure Map – World Monthly Atmospheric Humidity',
    description:
      'Interactive world vapour pressure map showing average monthly atmospheric water vapour by location. Explore historical and projected humidity data.',
  },
  [ClimateVarKey.WIND_SPEED]: {
    path: 'wind-speed',
    title: 'Wind Speed Map – World Monthly Average Wind Speed',
    description:
      'Interactive world wind speed map showing average monthly wind speed by location. Explore historical wind data and future climate projections.',
  },
  [ClimateVarKey.RELATIVE_HUMIDITY]: {
    path: 'relative-humidity',
    title: 'Relative Humidity Map – World Monthly Humidity Levels',
    description:
      'Interactive world relative humidity map showing average monthly humidity levels by location. Explore historical data and CMIP6 climate projections.',
  },
  [ClimateVarKey.POTENTIAL_EVAPOTRANSPIRATION]: {
    path: 'potential-evapotranspiration',
    title: 'Potential Evapotranspiration Map – Global Monthly PET',
    description:
      'Interactive global potential evapotranspiration map showing monthly PET values by location. Explore historical data and future climate projections.',
  },
  [ClimateVarKey.MOISTURE_INDEX]: {
    path: 'moisture-index',
    title: 'Moisture Index Map – World Monthly Climate Moisture',
    description:
      'Interactive world moisture index map showing the balance between precipitation and evapotranspiration by month. Explore historical data and CMIP6 projections.',
  },
  [ClimateVarKey.VAPOUR_PRESSURE_DEFICIT]: {
    path: 'vapour-pressure-deficit',
    title: 'Vapour Pressure Deficit Map – Global Monthly VPD',
    description:
      'Interactive global vapour pressure deficit map showing monthly atmospheric dryness by location. Explore historical data and future climate projections.',
  },
};

/**
 * Runtime assertion to ensure all ClimateVarKey enum values have corresponding routes.
 * This provides additional safety beyond TypeScript's compile-time checking.
 *
 * @throws Error if any ClimateVarKey values are missing from CLIMATE_VARIABLE_ROUTES
 */
const assertAllClimateVariablesHaveRoutes = (): void => {
  const enumValues = Object.values(ClimateVarKey);
  const routeKeys = Object.keys(CLIMATE_VARIABLE_ROUTES);

  const missingVariables = enumValues.filter(
    (enumValue) => !routeKeys.includes(enumValue),
  );

  if (missingVariables.length > 0) {
    throw new Error(
      `Missing routes for climate variables: ${missingVariables.join(', ')}. ` +
        `Please add entries to CLIMATE_VARIABLE_ROUTES for these variables.`,
    );
  }
};

// Generate climate variable routes dynamically
const generateClimateVariableRoutes = (): Routes => {
  // Assert all climate variables have routes before generating
  assertAllClimateVariablesHaveRoutes();

  return Object.entries(CLIMATE_VARIABLE_ROUTES).map(([variable, config]) => ({
    path: config.path,
    component: MapComponent,
    data: { variable, title: config.title, description: config.description },
  }));
};

/**
 * Utility function to get route information for a climate variable
 * @param variable The climate variable key
 * @returns Route configuration or undefined if not found
 */
export const getClimateVariableRoute = (variable: ClimateVarKey) => {
  return CLIMATE_VARIABLE_ROUTES[variable];
};

export const routes: Routes = [
  { path: '', component: MapComponent },
  { path: 'seasons', component: MonthlyGridComponent },
  { path: 'climate-scenarios', component: ScenarioGridComponent },
  { path: 'climate-predictions', component: YearRangeGridComponent },
  { path: 'climate-matrix', component: ScenarioYearRangeGridComponent },
  { path: 'about', component: AboutComponent },
  // Climate variable routes for SEO - generated dynamically
  ...generateClimateVariableRoutes(),
];
