import { Injectable } from '@angular/core';
import { ParamMap } from '@angular/router';
import { BehaviorSubject } from 'rxjs';

export interface MapViewState {
  center: { lat: number; lng: number };
  zoom: number;
}

const DEFAULT_CENTER = { lat: 20, lng: 5 };
const DEFAULT_ZOOM_LOW_RES = 3;
const DEFAULT_ZOOM_HIGH_RES = 4;
const LARGE_SCREEN_WIDTH = 1920;

function getDefaultViewState(): MapViewState {
  const isLargeScreen = window.innerWidth > LARGE_SCREEN_WIDTH;
  return {
    center: DEFAULT_CENTER,
    zoom: isLargeScreen ? DEFAULT_ZOOM_HIGH_RES : DEFAULT_ZOOM_LOW_RES,
  };
}

@Injectable({
  providedIn: 'root',
})
export class MapSyncService {
  private viewStateSubject = new BehaviorSubject<MapViewState>(
    getDefaultViewState(),
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
