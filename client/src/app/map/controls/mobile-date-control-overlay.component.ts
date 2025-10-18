import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatSliderModule } from '@angular/material/slider';
import { YearRange } from '../../core/metadata.service';

@Component({
  selector: 'app-mobile-date-control-overlay',
  standalone: true,
  imports: [CommonModule, MatSliderModule],
  templateUrl: './mobile-date-control-overlay.component.html',
  styleUrl: './mobile-date-control-overlay.component.scss',
  host: {
    '[class.month-hidden]': 'hideMonthSelector',
    '[class.year-hidden]': 'hideYearSelector',
  },
})
export class MobileDateControlOverlayComponent {
  @Input() selectedMonth = 1;
  @Input() selectedYearRange: YearRange | null = null;
  @Input() yearRanges: YearRange[] = [];
  @Input() hideMonthSelector = false;
  @Input() hideYearSelector = false;
  @Output() monthChange = new EventEmitter<number>();
  @Output() yearRangeChange = new EventEmitter<YearRange>();

  months = [
    'Jan',
    'Feb',
    'Mar',
    'Apr',
    'May',
    'Jun',
    'Jul',
    'Aug',
    'Sep',
    'Oct',
    'Nov',
    'Dec',
  ];

  get sliderValue(): number {
    if (!this.selectedYearRange || this.yearRanges.length === 0) {
      return 1;
    }
    const index = this.yearRanges.findIndex((year) => {
      const matchesPrimary =
        year.value[0] === this.selectedYearRange!.value[0] &&
        year.value[1] === this.selectedYearRange!.value[1];
      const matchesAdditional = year.additionalValues?.some(
        (additionalValue) =>
          additionalValue[0] === this.selectedYearRange!.value[0] &&
          additionalValue[1] === this.selectedYearRange!.value[1],
      );
      return matchesPrimary || matchesAdditional;
    });
    return index >= 0 ? index + 1 : 1;
  }

  onMonthChange(value: number): void {
    this.selectedMonth = value;
    this.monthChange.emit(value);
  }

  onYearRangeChange(value: number): void {
    if (
      this.yearRanges.length > 0 &&
      value >= 1 &&
      value <= this.yearRanges.length
    ) {
      this.yearRangeChange.emit(this.yearRanges[value - 1]);
    }
  }

  displayWith = (val: number): string => {
    return this.months[val - 1] || '';
  };

  displayYearWith = (val: number): string => {
    if (
      this.yearRanges.length > 0 &&
      val >= 1 &&
      val <= this.yearRanges.length
    ) {
      return this.yearRanges[val - 1]?.label || '';
    }
    return '';
  };
}
