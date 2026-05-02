import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class SelectedMonthService {
  private month: number = new Date().getMonth() + 1;

  getMonth(): number {
    return this.month;
  }

  setMonth(month: number): void {
    this.month = month;
  }
}
