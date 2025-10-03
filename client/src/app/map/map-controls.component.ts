import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
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

export interface MapControlsData {
  selectedVariableType: ClimateVarKey;
  selectedYearRange: YearRange | null;
  selectedResolution: SpatialResolution;
  selectedClimateScenario: ClimateScenario | null;
  selectedClimateModel: ClimateModel | null;
  showDifferenceMap: boolean;
}

export interface MapControlsOptions {
  variableTypes: ClimateVarKey[];
  yearRanges: YearRange[];
  resolutions: SpatialResolution[];
  climateScenarios: ClimateScenario[];
  climateModels: ClimateModel[];
  climateVariables: Record<ClimateVarKey, any>;
  availableVariableTypes: ClimateVarKey[];
  availableYearRanges: YearRange[];
  availableResolutions: SpatialResolution[];
  availableClimateScenarios: ClimateScenario[];
  availableClimateModels: ClimateModel[];
  isHistoricalYearRange: (yearRange: readonly [number, number]) => boolean;
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
  ],
  templateUrl: './map-controls.component.html',
  styleUrl: './map-controls.component.scss',
})
export class MapControlsComponent implements OnInit {
  @Input() controlsData!: MapControlsData;
  @Input() controlsOptions!: MapControlsOptions;
  @Output() controlsChange = new EventEmitter<MapControlsData>();

  ngOnInit(): void {
    if (!this.controlsData || !this.controlsOptions) {
      console.error('MapControlsComponent: Required inputs not provided');
    }
  }

  onVariableTypeChange(): void {
    this.emitChange();
  }

  onYearRangeChange(): void {
    this.emitChange();
  }

  onResolutionChange(): void {
    this.emitChange();
  }

  onClimateScenarioChange(): void {
    this.emitChange();
  }

  onClimateModelChange(): void {
    this.emitChange();
  }

  onDifferenceMapChange(): void {
    this.emitChange();
  }

  getResolutionDisplayName(resolution: SpatialResolution): string {
    switch (resolution) {
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

  trackByYearRange(index: number, yearRange: YearRange): string {
    return `${yearRange.value[0]}-${yearRange.value[1]}`;
  }

  private emitChange(): void {
    this.controlsChange.emit(this.controlsData);
  }
}
