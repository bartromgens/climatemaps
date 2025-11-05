import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class LocalStorageService {
  private isAvailable(): boolean {
    try {
      if (typeof localStorage === 'undefined') {
        return false;
      }
      const testKey = '__localStorage_test__';
      localStorage.setItem(testKey, 'test');
      localStorage.removeItem(testKey);
      return true;
    } catch {
      return false;
    }
  }

  getItem(key: string): string | null {
    if (!this.isAvailable()) {
      return null;
    }

    try {
      return localStorage.getItem(key);
    } catch (e) {
      console.warn(`[LocalStorage] Failed to read key "${key}":`, e);
      return null;
    }
  }

  setItem(key: string, value: string): boolean {
    if (!this.isAvailable()) {
      return false;
    }

    try {
      localStorage.setItem(key, value);
      return true;
    } catch (e) {
      console.warn(`[LocalStorage] Failed to write key "${key}":`, e);
      return false;
    }
  }

  removeItem(key: string): boolean {
    if (!this.isAvailable()) {
      return false;
    }

    try {
      localStorage.removeItem(key);
      return true;
    } catch (e) {
      console.warn(`[LocalStorage] Failed to remove key "${key}":`, e);
      return false;
    }
  }
}

