import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { ClimateMap, ClimateMapResource } from './climatemap';

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
}
