import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatSliderModule } from '@angular/material/slider';
import { CommonModule } from '@angular/common';
import { YearRange } from '../core/metadata.service';

@Component({
  selector: 'app-year-slider',
  standalone: true,
  imports: [CommonModule, MatSliderModule],
  templateUrl: './year-slider.component.html',
  styleUrls: ['./year-slider.component.scss'],
})
export class YearSliderComponent {
  @Output() valueChange = new EventEmitter<YearRange>();
  @Input() value = 1;

  years: YearRange[] = [
    { value: [1970, 2000], label: '1970-2000' },
    { value: [2021, 2040], label: '2021-2040' },
    { value: [2041, 2060], label: '2041-2060' },
    { value: [2061, 2080], label: '2061-2080' },
    { value: [2081, 2100], label: '2081-2100' },
  ];

  onInput(value: number) {
    console.log('onInput', value);
    this.value = value;
    this.valueChange.emit(this.years[value - 1]);
  }

  displayWith = (val: number) => this.years[val - 1]?.label || '';
}
