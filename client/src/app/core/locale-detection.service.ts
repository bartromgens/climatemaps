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
  private readonly FAHRENHEIT_COUNTRIES = new Set([
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

    // Check if the detected country uses Fahrenheit
    if (
      localeInfo.country &&
      this.FAHRENHEIT_COUNTRIES.has(localeInfo.country.toUpperCase())
    ) {
      console.log(
        '[LocaleDetection] Using Fahrenheit for country:',
        localeInfo.country,
      );
      return true;
    }

    // Check if the region suggests Fahrenheit usage
    if (
      localeInfo.region &&
      this.FAHRENHEIT_COUNTRIES.has(localeInfo.region.toUpperCase())
    ) {
      console.log(
        '[LocaleDetection] Using Fahrenheit for region:',
        localeInfo.region,
      );
      return true;
    }

    // Default to Celsius for unknown or uncertain locations
    console.log('[LocaleDetection] Using Celsius (default)');
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
