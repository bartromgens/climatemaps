import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { ClimateMap, ClimateMapResource } from './climatemap';

export interface ClimateValueResponse {
  value: number;
  data_type: string;
  month: number;
  latitude: number;
  longitude: number;
  unit: string;
  variable_name: string;
}

export interface NearestCityResponse {
  city_name: string;
  country_code: string;
  latitude: number;
  longitude: number;
}

@Injectable({
  providedIn: 'root',
})
export class ClimateMapService {
  constructor(private httpClient: HttpClient) {}

  public getClimateMapList(): Observable<ClimateMap[]> {
    const url = `${environment.apiBaseUrl}/climatemap`;
    return new Observable<ClimateMap[]>((observer) => {
      this.httpClient.get<ClimateMapResource[]>(url).subscribe((resources) => {
        observer.next(ClimateMap.fromResources(resources));
        observer.complete();
      });
    });
  }

  public getClimateValue(
    dataType: string,
    month: number,
    lat: number,
    lon: number,
  ): Observable<ClimateValueResponse> {
    const url = `${environment.apiBaseUrl}/value/${dataType}/${month}`;
    return this.httpClient.get<ClimateValueResponse>(url, {
      params: { lat: lat.toString(), lon: lon.toString() },
    });
  }

  public getNearestCity(
    lat: number,
    lon: number,
  ): Observable<NearestCityResponse> {
    const url = `${environment.apiBaseUrl}/nearest-city`;
    return this.httpClient.get<NearestCityResponse>(url, {
      params: { lat: lat.toString(), lon: lon.toString() },
    });
  }
}
