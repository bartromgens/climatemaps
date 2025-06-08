import { Component } from '@angular/core';
import { MatSliderModule } from "@angular/material/slider";
import { CommonModule } from "@angular/common";

@Component({
  selector: 'app-month-slider',
  standalone: true,
  imports: [
    CommonModule,
    MatSliderModule,
  ],
  templateUrl: './month-slider.component.html',
  styleUrls: ['./month-slider.component.scss']
})
export class MonthSliderComponent {
  months = [
    'January', 'February', 'March',
    'April', 'May', 'June',
    'July', 'August', 'September',
    'October', 'November', 'December'
  ];

  value = 1;

  onInput(event: any) {
    console.log(event);
  }

  displayWith = (val: number) =>
    this.months[val - 1] || '';
}
