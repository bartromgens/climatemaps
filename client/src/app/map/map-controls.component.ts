import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import {
  ClimateVarKey,
  SpatialResolution,
  ClimateScenario,
  ClimateModel,
  CLIMATE_SCENARIO_DISPLAY_NAMES,
} from '../utils/enum';
import { YearRange } from '../core/metadata.service';
import { YearSliderComponent } from './year-slider.component';
import { MonthSliderComponent } from './month-slider.component';
import { TemperatureUnitService } from '../core/temperature-unit.service';
import { TemperatureUtils } from '../utils/temperature-utils';

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
    MatSlideToggleModule,
    YearSliderComponent,
    MonthSliderComponent,
  ],
  templateUrl: './map-controls.component.html',
  styleUrl: './map-controls.component.scss',
})
export class MapControlsComponent implements OnInit {
  @Input() controlsData: MapControlsData | undefined;
  @Input() controlsOptions: MapControlsOptions | undefined;
  @Output() controlsChange = new EventEmitter<MapControlsData>();
  temperatureUnit = '°C';

  constructor(private temperatureUnitService: TemperatureUnitService) {}

  ngOnInit(): void {
    this.temperatureUnitService.unit$.subscribe((unit) => {
      this.temperatureUnit = unit;
    });
  }

  getVariableUnit(variableType: ClimateVarKey): string {
    const climateVariable =
      this.controlsOptions?.climateVariables?.[variableType];
    if (!climateVariable) {
      return '';
    }

    const isTemperature = TemperatureUtils.isTemperatureVariable(variableType);
    if (isTemperature && climateVariable.unit === '°C') {
      return this.temperatureUnit;
    }

    return climateVariable.unit;
  }

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
        return 'Low';
      case SpatialResolution.MIN10:
        return 'Medium';
      case SpatialResolution.MIN5:
        return 'High';
      case SpatialResolution.MIN2_5:
        return 'Very High';
      default:
        return resolution;
    }
  }

  getClimateScenarioDisplayName(scenario: ClimateScenario): string {
    return CLIMATE_SCENARIO_DISPLAY_NAMES[scenario] || scenario;
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
