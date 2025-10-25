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
  { path: string; title: string }
> = {
  [ClimateVarKey.T_MAX]: { path: 'temperature', title: 'Temperature Map' },
  [ClimateVarKey.T_MIN]: {
    path: 'temperature-min',
    title: 'Minimum Temperature Map',
  },
  [ClimateVarKey.PRECIPITATION]: {
    path: 'precipitation',
    title: 'Precipitation Map',
  },
  [ClimateVarKey.CLOUD_COVER]: {
    path: 'cloud-cover',
    title: 'Cloud Cover Map',
  },
  [ClimateVarKey.WET_DAYS]: { path: 'wet-days', title: 'Wet Days Map' },
  [ClimateVarKey.FROST_DAYS]: { path: 'frost-days', title: 'Frost Days Map' },
  [ClimateVarKey.RADIATION]: {
    path: 'radiation',
    title: 'Solar Radiation Map',
  },
  [ClimateVarKey.DIURNAL_TEMP_RANGE]: {
    path: 'diurnal-temperature-range',
    title: 'Diurnal Temperature Range Map',
  },
  [ClimateVarKey.VAPOUR_PRESSURE]: {
    path: 'vapour-pressure',
    title: 'Vapour Pressure Map',
  },
  [ClimateVarKey.WIND_SPEED]: { path: 'wind-speed', title: 'Wind Speed Map' },
  [ClimateVarKey.RELATIVE_HUMIDITY]: {
    path: 'relative-humidity',
    title: 'Relative Humidity Map',
  },
  [ClimateVarKey.MOISTURE_INDEX]: {
    path: 'moisture-index',
    title: 'Moisture Index Map',
  },
  [ClimateVarKey.VAPOUR_PRESSURE_DEFICIT]: {
    path: 'vapour-pressure-deficit',
    title: 'Vapour Pressure Deficit Map',
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
    data: { variable, title: config.title },
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
