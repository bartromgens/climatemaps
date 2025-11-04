import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { ReactiveFormsModule, FormControl } from '@angular/forms';
import { Observable } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { MatomoTracker } from 'ngx-matomo-client';

import { GeocodingService, LocationSuggestion } from './geocoding.service';
import { MapNavigationService } from './map-navigation.service';

@Component({
  selector: 'app-location-search',
  standalone: true,
  imports: [
    CommonModule,
    MatAutocompleteModule,
    MatInputModule,
    MatIconModule,
    MatButtonModule,
    ReactiveFormsModule,
  ],
  templateUrl: './location-search.component.html',
  styleUrl: './location-search.component.scss',
})
export class LocationSearchComponent {
  searchControl = new FormControl('');
  filteredLocations$: Observable<LocationSuggestion[]>;
  private readonly tracker = inject(MatomoTracker);

  constructor(
    private geocodingService: GeocodingService,
    private mapNavigationService: MapNavigationService,
  ) {
    this.filteredLocations$ = this.searchControl.valueChanges.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap((value) => {
        const query = typeof value === 'string' ? value : '';
        return this.geocodingService.searchLocations(query);
      }),
    );
  }

  displayLocationName(location: LocationSuggestion | null): string {
    return location ? location.displayName : '';
  }

  onLocationSelected(location: LocationSuggestion): void {
    const zoom = this.geocodingService.getZoomLevelForLocation(location);
    this.mapNavigationService.navigateToLocation(
      location.lat,
      location.lon,
      zoom,
      true,
    );

    this.tracker.trackEvent(
      'Search',
      'Location Selected',
      location.displayName,
    );
  }

  clearSearch(): void {
    this.searchControl.setValue('');
  }
}
