import { Component, inject, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { ClimateModel } from '../../utils/enum';
import { MatomoTracker } from 'ngx-matomo-client';

@Component({
  selector: 'app-climate-model-overlay',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatFormFieldModule,
    MatSelectModule,
  ],
  templateUrl: './climate-model-overlay.component.html',
  styleUrl: './climate-model-overlay.component.scss',
})
export class ClimateModelOverlayComponent {
  private readonly tracker = inject(MatomoTracker);

  @Input() selectedClimateModel: ClimateModel | null = null;
  @Input() climateModels: ClimateModel[] = [];
  @Input() availableClimateModels: ClimateModel[] = [];
  @Input() show = false;
  @Output() climateModelChange = new EventEmitter<ClimateModel | null>();

  onClimateModelChange(event: any): void {
    const model = event.value as ClimateModel | null;
    this.climateModelChange.emit(model);

    if (model) {
      const modelName = this.getClimateModelDisplayName(model);
      this.tracker.trackEvent(
        'Control Selection',
        'Climate Model Change (Overlay)',
        modelName,
      );
    }
  }

  getClimateModelDisplayName(model: ClimateModel): string {
    if (model === ClimateModel.ENSEMBLE_MEAN) {
      return 'Ensemble Mean';
    }
    return model.replace(/_/g, '-');
  }
}

