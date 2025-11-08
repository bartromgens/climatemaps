import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ToastService } from '../../core/toast.service';
import { MatomoTracker } from 'ngx-matomo-client';

export interface LocationCoordinates {
  lat: number;
  lon: number;
}

@Injectable({
  providedIn: 'root',
})
export class GeolocationService {
  constructor(
    private toastService: ToastService,
    private tracker: MatomoTracker,
  ) {}

  getCurrentPosition(): Observable<LocationCoordinates> {
    return new Observable<LocationCoordinates>((observer) => {
      if (!navigator.geolocation) {
        this.toastService.showError(
          'Geolocation is not supported by your browser',
          5000,
        );
        observer.error(new Error('Geolocation not supported'));
        return;
      }

      this.toastService.showInfo('Getting your location...', 2000);

      navigator.geolocation.getCurrentPosition(
        (position: globalThis.GeolocationPosition) => {
          const lat = position.coords.latitude;
          const lon = position.coords.longitude;
          observer.next({ lat, lon });
          observer.complete();

          this.tracker.trackEvent(
            'Map Interaction',
            'Location Button',
            'Device Location',
          );
        },
        (error: GeolocationPositionError) => {
          let errorMessage = 'Unable to get your location';
          switch (error.code) {
            case error.PERMISSION_DENIED:
              errorMessage =
                'Location access denied. Please enable location permissions in your browser settings.';
              break;
            case error.POSITION_UNAVAILABLE:
              errorMessage = 'Location information is unavailable';
              break;
            case error.TIMEOUT:
              errorMessage = 'Location request timed out';
              break;
          }
          this.toastService.showError(errorMessage, 6000);
          observer.error(error);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0,
        },
      );
    });
  }
}
