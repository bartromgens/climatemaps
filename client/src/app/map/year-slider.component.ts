import { Component } from '@angular/core';
import { MatSliderModule } from '@angular/material/slider';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-year-slider',
  standalone: true,
  imports: [CommonModule, MatSliderModule],
  templateUrl: './year-slider.component.html',
  styleUrls: ['./year-slider.component.scss'],
})
export class YearSliderComponent {
  years = ['2000', '2030', '2050', '2070', '2100'];
  value = 1;

  onInput(event: any) {
    console.log(event);
  }

  displayWith = (val: number) => this.years[val - 1] || '';
}
