import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-contour-toggle-overlay',
  standalone: true,
  imports: [CommonModule, MatButtonModule],
  templateUrl: './contour-toggle-overlay.component.html',
  styleUrl: './contour-toggle-overlay.component.scss',
})
export class ContourToggleOverlayComponent {
  @Input() isActive = false;
  @Input() disabled = false;
  @Output() toggleChange = new EventEmitter<boolean>();

  onToggleClick(): void {
    if (!this.disabled) {
      this.toggleChange.emit(!this.isActive);
    }
  }
}
