import { Component, OnInit, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterOutlet } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { ReactiveFormsModule, FormControl } from '@angular/forms';
import { Observable } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';

import { GeocodingService, LocationSuggestion } from './core/geocoding.service';
import { MapNavigationService } from './core/map-navigation.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    RouterLink,
    MatToolbarModule,
    MatButtonModule,
    MatAutocompleteModule,
    MatInputModule,
    MatFormFieldModule,
    MatIconModule,
    MatMenuModule,
    ReactiveFormsModule,
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent implements OnInit {
  readonly title: string = 'OpenClimateMap';
  isMobile = false;
  searchControl = new FormControl('');
  filteredLocations$: Observable<LocationSuggestion[]>;

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

  ngOnInit(): void {
    this.checkMobile();
  }

  @HostListener('window:resize', ['$event'])
  onResize(): void {
    this.checkMobile();
  }

  private checkMobile(): void {
    this.isMobile = window.innerWidth <= 768;
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
      !this.isMobile,
    );
  }

  clearSearch(): void {
    this.searchControl.setValue('');
  }
}
