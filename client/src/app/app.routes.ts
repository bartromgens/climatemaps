import { Routes } from '@angular/router';
import { AboutComponent } from './about.component';
import { MapComponent } from './map';
import { MonthlyGridComponent } from './map/monthly-grid.component';
import { ScenarioGridComponent } from './map/scenario-grid.component';
import { YearRangeGridComponent } from './map/yearrange-grid.component';

export const routes: Routes = [
  { path: '', component: MapComponent },
  { path: 'seasons', component: MonthlyGridComponent },
  { path: 'climate-scenarios', component: ScenarioGridComponent },
  { path: 'climate-predictions', component: YearRangeGridComponent },
  { path: 'about', component: AboutComponent },
];
