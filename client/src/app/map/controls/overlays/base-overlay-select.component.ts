import { Component, inject, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatomoTracker } from 'ngx-matomo-client';

@Component({
  selector: 'app-base-overlay-select',
  standalone: true,
  imports: [CommonModule, FormsModule, MatFormFieldModule, MatSelectModule],
  templateUrl: './base-overlay-select.component.html',
  styleUrl: './base-overlay-select.component.scss',
  host: {
    '[style.bottom.px]': 'bottomPosition',
  },
})
export class BaseOverlaySelectComponent<T> {
  private readonly tracker = inject(MatomoTracker);

  @Input() label = '';
  @Input() selectedValue: T | null = null;
  @Input() options: T[] = [];
  @Input() availableOptions: T[] = [];
  @Input() show = false;
  @Input() trackingCategory = 'Control Selection';
  @Input() trackingAction = 'Selection Change (Overlay)';
  @Input() getDisplayName: (value: T) => string = (value: T) =>
    String(value);
  @Input() bottomPosition = 20;
  @Output() valueChange = new EventEmitter<T | null>();

  onSelectionChange(event: any): void {
    const value = event.value as T | null;
    this.valueChange.emit(value);

    if (value) {
      const displayName = this.getDisplayName(value);
      this.tracker.trackEvent(
        this.trackingCategory,
        this.trackingAction,
        displayName,
      );
    }
  }

  isAvailable(option: T): boolean {
    return this.availableOptions.includes(option);
  }
}

