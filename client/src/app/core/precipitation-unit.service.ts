import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { LocaleDetectionService } from './locale-detection.service';
import { PrecipitationUtils } from '../utils/precipitation-utils';

export enum PrecipitationUnit {
  MM = 'mm',
  INCHES = 'in',
}

@Injectable({
  providedIn: 'root',
})
export class PrecipitationUnitService {
  private unitSubject = new BehaviorSubject<PrecipitationUnit>(
    PrecipitationUnit.MM,
  );
  public unit$: Observable<PrecipitationUnit> = this.unitSubject.asObservable();

  constructor(private localeDetectionService: LocaleDetectionService) {
    this.initializeFromLocale();
  }

  private initializeFromLocale(): void {
    const shouldUseInches = this.localeDetectionService.shouldUseInches();
    const initialUnit = shouldUseInches
      ? PrecipitationUnit.INCHES
      : PrecipitationUnit.MM;
    console.log('[PrecipitationUnit] Initialized with unit:', initialUnit);
    this.unitSubject.next(initialUnit);
  }

  getUnit(): PrecipitationUnit {
    return this.unitSubject.value;
  }

  setUnit(unit: PrecipitationUnit): void {
    this.unitSubject.next(unit);
  }

  toggleUnit(): void {
    const newUnit =
      this.unitSubject.value === PrecipitationUnit.MM
        ? PrecipitationUnit.INCHES
        : PrecipitationUnit.MM;
    this.setUnit(newUnit);
  }

  convertPrecipitation(mm: number): number {
    if (this.unitSubject.value === PrecipitationUnit.INCHES) {
      return PrecipitationUtils.mmToInches(mm);
    }
    return mm;
  }
}
