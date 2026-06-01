import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';

export const MOBILE_MAX_WIDTH = 768;

export function isMobileViewport(): boolean {
  return window.innerWidth <= MOBILE_MAX_WIDTH;
}

export const blockOnMobileGuard: CanActivateFn = () => {
  if (isMobileViewport()) {
    return inject(Router).createUrlTree(['/']);
  }
  return true;
};
