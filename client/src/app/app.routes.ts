import { Routes } from '@angular/router';
import { AboutComponent } from './about.component';
import { MapComponent } from './map';

export const routes: Routes = [
  { path: '', component: MapComponent },
  { path: 'about', component: AboutComponent },
];
