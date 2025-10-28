import { Component, OnInit, HostListener, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterOutlet } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule, MatIconRegistry } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { ReactiveFormsModule, FormControl } from '@angular/forms';
import { DomSanitizer } from '@angular/platform-browser';
import { Observable } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { MatomoTracker } from 'ngx-matomo-client';

import { GeocodingService, LocationSuggestion } from './core/geocoding.service';
import { MapNavigationService } from './core/map-navigation.service';
import { TemperatureUnitSelectorComponent } from './core/temperature-unit-selector.component';
import { PrecipitationUnitSelectorComponent } from './core/precipitation-unit-selector.component';

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
    TemperatureUnitSelectorComponent,
    PrecipitationUnitSelectorComponent,
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent implements OnInit {
  readonly title: string = 'OpenClimateMap';
  isMobile = false;
  searchControl = new FormControl('');
  filteredLocations$: Observable<LocationSuggestion[]>;
  private readonly tracker = inject(MatomoTracker);

  constructor(
    private geocodingService: GeocodingService,
    private mapNavigationService: MapNavigationService,
    private matIconRegistry: MatIconRegistry,
    private domSanitizer: DomSanitizer,
  ) {
    this.matIconRegistry.addSvgIcon(
      'github',
      this.domSanitizer.bypassSecurityTrustResourceUrl('assets/github.svg'),
    );

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
