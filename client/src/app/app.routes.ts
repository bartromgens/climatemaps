import { Routes } from '@angular/router';
import { AboutComponent } from './about.component';
import { MapComponent } from './map';
import { MonthlyGridComponent } from './map/monthly-grid.component';
import { ScenarioGridComponent } from './map/scenario-grid.component';

export const routes: Routes = [
  { path: '', component: MapComponent },
  { path: 'monthly', component: MonthlyGridComponent },
  { path: 'scenarios', component: ScenarioGridComponent },
  { path: 'about', component: AboutComponent },
];
