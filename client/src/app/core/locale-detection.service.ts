import { Injectable } from '@angular/core';

export interface LocaleInfo {
  country: string | null;
  language: string;
  region: string | null;
}

@Injectable({
  providedIn: 'root',
})
export class LocaleDetectionService {
  private readonly IMPERIAL_COUNTRIES = new Set([
    'US', // United States
    'BS', // Bahamas
    'BZ', // Belize
    'KY', // Cayman Islands
    'PW', // Palau
    'FM', // Micronesia
    'MH', // Marshall Islands
    'LR', // Liberia
    'MM', // Myanmar (Burma)
  ]);

  detectLocale(): LocaleInfo {
    const language = navigator.language || navigator.languages?.[0] || 'en';
    const parts = language.split('-');
    const detectedLanguage = parts[0] || 'en';
    const detectedRegion = parts[1] || null;

    return {
      country: detectedRegion,
      language: detectedLanguage,
      region: detectedRegion,
    };
  }

  private isImperialCountry(localeInfo: LocaleInfo): boolean {
    return (
      (localeInfo.country !== null &&
        this.IMPERIAL_COUNTRIES.has(localeInfo.country.toUpperCase())) ||
      (localeInfo.region !== null &&
        this.IMPERIAL_COUNTRIES.has(localeInfo.region.toUpperCase()))
    );
  }

  shouldUseFahrenheit(localeInfo?: LocaleInfo): boolean {
    if (!localeInfo) {
      localeInfo = this.detectLocale();
    }

    console.log('[LocaleDetection] Detected locale:', {
      language: localeInfo.language,
      country: localeInfo.country,
      region: localeInfo.region,
      navigatorLanguage: navigator.language,
    });

    if (this.isImperialCountry(localeInfo)) {
      console.log(
        '[LocaleDetection] Using Fahrenheit for country/region:',
        localeInfo.country || localeInfo.region,
      );
      return true;
    }

    // Default to Celsius for unknown or uncertain locations
    console.log('[LocaleDetection] Using Celsius (default)');
    return false;
  }

  shouldUseInches(localeInfo?: LocaleInfo): boolean {
    if (!localeInfo) {
      localeInfo = this.detectLocale();
    }

    console.log('[LocaleDetection] Detected locale for precipitation:', {
      language: localeInfo.language,
      country: localeInfo.country,
      region: localeInfo.region,
      navigatorLanguage: navigator.language,
    });

    if (this.isImperialCountry(localeInfo)) {
      console.log(
        '[LocaleDetection] Using inches for country/region:',
        localeInfo.country || localeInfo.region,
      );
      return true;
    }

    // Default to mm for unknown or uncertain locations
    console.log('[LocaleDetection] Using mm (default)');
    return false;
  }

  getDetectedCountry(): string | null {
    const locale = this.detectLocale();
    return locale.country;
  }

  getDetectedLanguage(): string {
    const locale = this.detectLocale();
    return locale.language;
  }
}
