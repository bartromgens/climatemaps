import { Routes } from '@angular/router';
import { AboutComponent } from './about.component';
import { MapComponent } from './map';
import { MonthlyGridComponent } from './map/monthly-grid.component';

export const routes: Routes = [
  { path: '', component: MapComponent },
  { path: 'monthly', component: MonthlyGridComponent },
  { path: 'about', component: AboutComponent },
];
