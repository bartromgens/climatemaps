import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

export interface MapViewState {
  center: { lat: number; lng: number };
  zoom: number;
}

@Injectable({
  providedIn: 'root',
})
export class MapSyncService {
  private viewStateSubject = new Subject<MapViewState>();
  viewState$ = this.viewStateSubject.asObservable();

  updateViewState(state: MapViewState): void {
    this.viewStateSubject.next(state);
  }
}
