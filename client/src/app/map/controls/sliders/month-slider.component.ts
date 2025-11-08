import { Component, EventEmitter, inject, Input, Output } from '@angular/core';
import { MatSliderModule } from '@angular/material/slider';
import { CommonModule } from '@angular/common';
import { MatomoTracker } from 'ngx-matomo-client';

@Component({
  selector: 'app-month-slider',
  standalone: true,
  imports: [CommonModule, MatSliderModule],
  templateUrl: './month-slider.component.html',
  styleUrls: ['./month-slider.component.scss'],
  host: {
    class: 'month-slider',
  },
})
export class MonthSliderComponent {
  private readonly tracker = inject(MatomoTracker);

  @Output() valueChange = new EventEmitter<number>();
  @Input() value = 1;

  months = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December',
  ];

  onInput(value: number) {
    console.log('onInput', value);
    this.value = value;
    this.valueChange.emit(value);

    this.tracker.trackEvent(
      'Slider Control',
      'Month Change',
      this.months[value - 1],
      value,
    );
  }

  displayWith = (val: number) => {
    return this.months[val - 1] || '';
  };
}
