import { Component, EventEmitter, inject, Input, Output } from '@angular/core';
import { MatSliderModule } from '@angular/material/slider';
import { CommonModule } from '@angular/common';
import { YearRange } from '../../core/metadata.service';
import { MatomoTracker } from 'ngx-matomo-client';

@Component({
  selector: 'app-year-slider',
  standalone: true,
  imports: [CommonModule, MatSliderModule],
  templateUrl: './year-slider.component.html',
  styleUrls: ['./year-slider.component.scss'],
})
export class YearSliderComponent {
  private readonly tracker = inject(MatomoTracker);

  @Output() valueChange = new EventEmitter<YearRange>();
  @Input() value: YearRange | null = null;
  @Input() years: YearRange[] = [];
  @Input() disabled = false;

  get sliderValue(): number {
    if (!this.value || this.years.length === 0) {
      return 1;
    }
    const index = this.years.findIndex((year) => {
      const matchesPrimary =
        year.value[0] === this.value!.value[0] &&
        year.value[1] === this.value!.value[1];
      const matchesAdditional = year.additionalValues?.some(
        (additionalValue) =>
          additionalValue[0] === this.value!.value[0] &&
          additionalValue[1] === this.value!.value[1],
      );
      return matchesPrimary || matchesAdditional;
    });
    return index >= 0 ? index + 1 : 1;
  }

  onInput(value: number) {
    console.log('onInput', value);
    if (this.years.length > 0 && value >= 1 && value <= this.years.length) {
      const selectedYear = this.years[value - 1];
      this.valueChange.emit(selectedYear);

      this.tracker.trackEvent(
        'Slider Control',
        'Year Range Change',
        selectedYear.label,
        value,
      );
    }
  }

  displayWith = (val: number) => {
    if (this.years.length > 0 && val >= 1 && val <= this.years.length) {
      return this.years[val - 1]?.label || '';
    }
    return '';
  };
}
