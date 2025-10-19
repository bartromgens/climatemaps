import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-show-change-toggle-overlay',
  standalone: true,
  imports: [CommonModule, MatButtonModule],
  templateUrl: './show-change-toggle-overlay.component.html',
  styleUrl: './show-change-toggle-overlay.component.scss',
})
export class ShowChangeToggleOverlayComponent {
  @Input() isActive = false;
  @Input() disabled = false;
  @Output() toggleChange = new EventEmitter<boolean>();

  onToggleClick(): void {
    if (!this.disabled) {
      this.toggleChange.emit(!this.isActive);
    }
  }
}
