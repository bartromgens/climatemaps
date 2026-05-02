import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { ClimateVarKey } from '../../../utils/enum';
import { CLIMATE_VARIABLE_DESCRIPTIONS } from '../../../utils/climate-variable-descriptions';

@Component({
  selector: 'app-variable-info-overlay',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatButtonModule],
  templateUrl: './variable-info-overlay.component.html',
  styleUrl: './variable-info-overlay.component.scss',
})
export class VariableInfoOverlayComponent {
  @Input() selectedVariableType: ClimateVarKey | undefined;
  @Input() displayName: string | undefined;

  expanded = false;

  get description(): string {
    if (!this.selectedVariableType) return '';
    return CLIMATE_VARIABLE_DESCRIPTIONS[this.selectedVariableType] ?? '';
  }

  toggle(): void {
    this.expanded = !this.expanded;
  }
}
