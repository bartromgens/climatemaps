import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

export interface NavigationRequest {
  lat: number;
  lon: number;
  zoom: number;
  generateCharts?: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class MapNavigationService {
  private navigationSubject = new Subject<NavigationRequest>();
  navigation$ = this.navigationSubject.asObservable();

  navigateToLocation(
    lat: number,
    lon: number,
    zoom: number,
    generateCharts: boolean = false,
  ): void {
    this.navigationSubject.next({ lat, lon, zoom, generateCharts });
  }
}
