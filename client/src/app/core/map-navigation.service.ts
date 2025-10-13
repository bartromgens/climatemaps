import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

export interface NavigationRequest {
  lat: number;
  lon: number;
  zoom: number;
}

@Injectable({
  providedIn: 'root',
})
export class MapNavigationService {
  private navigationSubject = new Subject<NavigationRequest>();
  navigation$ = this.navigationSubject.asObservable();

  navigateToLocation(lat: number, lon: number, zoom: number): void {
    this.navigationSubject.next({ lat, lon, zoom });
  }
}
