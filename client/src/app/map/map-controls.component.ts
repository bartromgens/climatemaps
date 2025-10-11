import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatCheckboxModule } from '@angular/material/checkbox';
import {
  ClimateVarKey,
  SpatialResolution,
  ClimateScenario,
  ClimateModel,
} from '../utils/enum';
import { YearRange } from '../core/metadata.service';
import { YearSliderComponent } from './year-slider.component';
import { MonthSliderComponent } from './month-slider.component';

export interface MapControlsData {
  selectedVariableType: ClimateVarKey;
  selectedYearRange: YearRange | null;
  selectedResolution: SpatialResolution;
  selectedClimateScenario: ClimateScenario | null;
  selectedClimateModel: ClimateModel | null;
  showDifferenceMap: boolean;
  selectedMonth: number;
}

export interface MapControlsOptions {
  variableTypes: ClimateVarKey[];
  resolutions: SpatialResolution[];
  climateScenarios: ClimateScenario[];
  climateModels: ClimateModel[];
  climateVariables: Record<ClimateVarKey, any>;
  availableVariableTypes: ClimateVarKey[];
  availableResolutions: SpatialResolution[];
  availableClimateScenarios: ClimateScenario[];
  availableClimateModels: ClimateModel[];
  isHistoricalYearRange: (yearRange: readonly [number, number]) => boolean;
  yearRanges: YearRange[];
  availableYearRanges: YearRange[];
}

@Component({
  selector: 'app-map-controls',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatFormFieldModule,
    MatSelectModule,
    MatCheckboxModule,
    YearSliderComponent,
    MonthSliderComponent,
  ],
  templateUrl: './map-controls.component.html',
  styleUrl: './map-controls.component.scss',
})
export class MapControlsComponent {
  @Input() controlsData: MapControlsData | undefined;
  @Input() controlsOptions: MapControlsOptions | undefined;
  @Output() controlsChange = new EventEmitter<MapControlsData>();

  onVariableTypeChange(event: any): void {
    if (this.controlsData) {
      this.controlsData.selectedVariableType = event.value;
      this.emitChange();
    }
  }

  onResolutionChange(event: any): void {
    if (this.controlsData) {
      this.controlsData.selectedResolution = event.value;
      this.emitChange();
    }
  }

  onClimateScenarioChange(event: any): void {
    if (this.controlsData) {
      this.controlsData.selectedClimateScenario = event.value;
      this.emitChange();
    }
  }

  onClimateModelChange(event: any): void {
    if (this.controlsData) {
      this.controlsData.selectedClimateModel = event.value;
      this.emitChange();
    }
  }

  onDifferenceMapChange(event: any): void {
    if (this.controlsData) {
      this.controlsData.showDifferenceMap = event;
      this.emitChange();
    }
  }

  onYearSelected(yearRange: YearRange): void {
    console.log('onYearSelected', yearRange);
    if (this.controlsData) {
      this.controlsData.selectedYearRange = yearRange;
      this.emitChange();
    }
  }

  onMonthSelected(month: number): void {
    console.log('onMonthSelected', month);
    if (this.controlsData) {
      this.controlsData.selectedMonth = month;
      this.emitChange();
    }
  }

  getResolutionDisplayName(resolution: SpatialResolution): string {
    switch (resolution) {
      case SpatialResolution.MIN30:
        return 'Very low';
      case SpatialResolution.MIN10:
        return 'Low';
      case SpatialResolution.MIN5:
        return 'Medium';
      case SpatialResolution.MIN2_5:
        return 'High';
      default:
        return resolution;
    }
  }

  getClimateModelDisplayName(model: ClimateModel): string {
    if (model === ClimateModel.ENSEMBLE_MEAN) {
      return 'Ensemble Mean';
    }
    return model.replace(/_/g, '-');
  }

  shouldShowFutureControls(): boolean {
    return !!(
      this.controlsData?.selectedYearRange &&
      this.controlsOptions?.isHistoricalYearRange &&
      this.controlsData.selectedYearRange.value &&
      !this.controlsOptions.isHistoricalYearRange(
        this.controlsData.selectedYearRange.value,
      )
    );
  }

  shouldShowDifferenceCheckbox(): boolean {
    return !!(
      this.controlsData?.selectedYearRange &&
      this.controlsOptions?.isHistoricalYearRange &&
      this.controlsData.selectedYearRange.value &&
      !this.controlsOptions.isHistoricalYearRange(
        this.controlsData.selectedYearRange.value,
      )
    );
  }

  private emitChange(): void {
    if (this.controlsData) {
      this.controlsChange.emit(this.controlsData);
    }
  }
}
