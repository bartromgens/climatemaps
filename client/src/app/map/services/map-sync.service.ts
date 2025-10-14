import { Injectable } from '@angular/core';
import { ParamMap } from '@angular/router';
import { BehaviorSubject } from 'rxjs';

export interface MapViewState {
  center: { lat: number; lng: number };
  zoom: number;
}

const DEFAULT_VIEW_STATE: MapViewState = {
  center: { lat: 52.1, lng: 5.58 },
  zoom: 5,
};

@Injectable({
  providedIn: 'root',
})
export class MapSyncService {
  private viewStateSubject = new BehaviorSubject<MapViewState>(
    DEFAULT_VIEW_STATE,
  );
  viewState$ = this.viewStateSubject.asObservable();

  updateViewState(state: MapViewState): void {
    this.viewStateSubject.next(state);
  }

  setInitialViewState(state: MapViewState): void {
    this.viewStateSubject.next(state);
  }

  getInitialViewState(): MapViewState {
    return this.viewStateSubject.getValue();
  }

  updateFromURLParams(params: ParamMap): void {
    const lat = params.get('lat');
    const lon = params.get('lon');
    const zoom = params.get('zoom');

    if (lat && lon && zoom) {
      const latNum = Number(lat);
      const lonNum = Number(lon);
      const zoomNum = Number(zoom);

      if (!isNaN(latNum) && !isNaN(lonNum) && !isNaN(zoomNum)) {
        this.setInitialViewState({
          center: { lat: latNum, lng: lonNum },
          zoom: zoomNum,
        });
      }
    }
  }
}
