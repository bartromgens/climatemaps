import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

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

  getUnit(): TemperatureUnit {
    return this.unitSubject.value;
  }

  setUnit(unit: TemperatureUnit): void {
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
