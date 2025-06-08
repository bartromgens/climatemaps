import { Component, Input } from '@angular/core';
import { MatToolbarModule } from '@angular/material/toolbar';

import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-footer',
  standalone: true,
  imports: [CommonModule, MatToolbarModule],
  templateUrl: './footer.component.html',
  styleUrl: './footer.component.scss',
})
export class FooterComponent {
}
