import { Component, Input, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormControl } from '@angular/forms';
import { MatIconModule, MatIconRegistry } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatMenuModule } from '@angular/material/menu';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { DomSanitizer } from '@angular/platform-browser';
import { Observable } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { MatomoTracker } from 'ngx-matomo-client';
import {
  GeocodingService,
  LocationSuggestion,
} from '../../core/geocoding.service';
import { MapNavigationService } from '../../core/map-navigation.service';
import { TemperatureUnitSelectorComponent } from '../../core/temperature-unit-selector.component';
import { PrecipitationUnitSelectorComponent } from '../../core/precipitation-unit-selector.component';

@Component({
  selector: 'app-mobile-hamburger-menu',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    MatIconModule,
    MatButtonModule,
    MatMenuModule,
    MatAutocompleteModule,
    MatInputModule,
    MatFormFieldModule,
    TemperatureUnitSelectorComponent,
    PrecipitationUnitSelectorComponent,
  ],
  templateUrl: './mobile-hamburger-menu.component.html',
  styleUrl: './mobile-hamburger-menu.component.scss',
})
export class MobileHamburgerMenuComponent {
  @Input() isMobile = false;

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
