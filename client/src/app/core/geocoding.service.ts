import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';

import { environment } from '../../environments/environment';

export interface GeocodingLocation {
  display_name: string;
  latitude: number;
  longitude: number;
  type: string;
  bounding_box?: number[];
}

export interface LocationSuggestion {
  displayName: string;
  lat: number;
  lon: number;
  type: string;
  boundingBox?: [number, number, number, number];
}

@Injectable({
  providedIn: 'root',
})
export class GeocodingService {
  private readonly API_URL = `${environment.apiBaseUrl}/geocode`;

  constructor(private http: HttpClient) {}

  searchLocations(query: string): Observable<LocationSuggestion[]> {
    if (!query || query.trim().length < 2) {
      return of([]);
    }

    const params = new HttpParams().set('query', query).set('limit', '10');

    return this.http.get<GeocodingLocation[]>(this.API_URL, { params }).pipe(
      map((results) =>
        results.map((result) => this.mapToLocationSuggestion(result)),
      ),
      catchError((error) => {
        console.error('Geocoding error:', error);
        return of([]);
      }),
    );
  }

  private mapToLocationSuggestion(
    result: GeocodingLocation,
  ): LocationSuggestion {
    return {
      displayName: result.display_name,
      lat: result.latitude,
      lon: result.longitude,
      type: result.type,
      boundingBox:
        result.bounding_box && result.bounding_box.length === 4
          ? [
              result.bounding_box[0],
              result.bounding_box[1],
              result.bounding_box[2],
              result.bounding_box[3],
            ]
          : undefined,
    };
  }

  getZoomLevelForLocation(location: LocationSuggestion): number {
    const type = location.type.toLowerCase();

    if (type === 'country') {
      return 5;
    } else if (type === 'state') {
      return 6;
    } else if (type === 'city') {
      return 7;
    } else if (type === 'town') {
      return 7;
    } else if (type === 'village') {
      return 7;
    } else if (type === 'hamlet') {
      return 7;
    }
    return 7;
  }
}
