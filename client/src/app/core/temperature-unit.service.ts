import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { LocaleDetectionService } from './locale-detection.service';
import { LocalStorageService } from './local-storage.service';

export enum TemperatureUnit {
  CELSIUS = '°C',
  FAHRENHEIT = '°F',
}

@Injectable({
  providedIn: 'root',
})
export class TemperatureUnitService {
  private unitSubject = new BehaviorSubject<TemperatureUnit>(
    TemperatureUnit.CELSIUS,
  );
  public unit$: Observable<TemperatureUnit> = this.unitSubject.asObservable();

  constructor(
    private localeDetectionService: LocaleDetectionService,
    private localStorageService: LocalStorageService,
  ) {
    this.initializeFromLocale();
  }

  private initializeFromLocale(): void {
    const storedUnit = this.localStorageService.getItem(
      'temperatureUnit',
    ) as TemperatureUnit | null;
    let initialUnit: TemperatureUnit;

    if (storedUnit && Object.values(TemperatureUnit).includes(storedUnit)) {
      initialUnit = storedUnit;
    } else {
      const shouldUseFahrenheit =
        this.localeDetectionService.shouldUseFahrenheit();
      initialUnit = shouldUseFahrenheit
        ? TemperatureUnit.FAHRENHEIT
        : TemperatureUnit.CELSIUS;
    }

    console.log('[TemperatureUnit] Initialized with unit:', initialUnit);
    this.unitSubject.next(initialUnit);
  }

  getUnit(): TemperatureUnit {
    return this.unitSubject.value;
  }

  setUnit(unit: TemperatureUnit): void {
    this.localStorageService.setItem('temperatureUnit', unit);
    this.unitSubject.next(unit);
  }

  toggleUnit(): void {
    const newUnit =
      this.unitSubject.value === TemperatureUnit.CELSIUS
        ? TemperatureUnit.FAHRENHEIT
        : TemperatureUnit.CELSIUS;
    this.setUnit(newUnit);
  }

  convertTemperature(celsius: number): number {
    if (this.unitSubject.value === TemperatureUnit.FAHRENHEIT) {
      return this.celsiusToFahrenheit(celsius);
    }
    return celsius;
  }

  celsiusToFahrenheit(celsius: number): number {
    return (celsius * 9) / 5 + 32;
  }

  fahrenheitToCelsius(fahrenheit: number): number {
    return ((fahrenheit - 32) * 5) / 9;
  }
}
