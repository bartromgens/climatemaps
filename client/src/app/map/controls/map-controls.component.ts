import {
  Component,
  inject,
  Input,
  Output,
  EventEmitter,
  OnInit,
} from '@angular/core';
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
} from '../../utils/enum';
import { YearRange } from '../../core/metadata.service';
import { YearSliderComponent } from './sliders/year-slider.component';
import { MonthSliderComponent } from './sliders/month-slider.component';
import { TemperatureUnit, TemperatureUnitService } from '../../core/temperature-unit.service';
import { PrecipitationUnitService } from '../../core/precipitation-unit.service';
import { ClimateVariableHelperService } from '../../core/climate-variable-helper.service';
import { UnitUtils } from '../../utils/unit-utils';
import { MatomoTracker } from 'ngx-matomo-client';

export interface MapControlsData {
  selectedVariableType: ClimateVarKey;
  selectedYearRange: YearRange | null;
  selectedResolution: SpatialResolution;
  selectedClimateScenario: ClimateScenario | null;
  selectedClimateModel: ClimateModel | null;
  showDifferenceMap: boolean;
  showContourLines: boolean;
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
  private readonly tracker = inject(MatomoTracker);

  @Input() controlsData: MapControlsData | undefined;
  @Input() controlsOptions: MapControlsOptions | undefined;
  @Input() hideVariableSelector = false;
  @Input() showDropDownControls = true;
  @Output() controlsChange = new EventEmitter<MapControlsData>();
  temperatureUnit = TemperatureUnit.CELSIUS;

  constructor(
    private temperatureUnitService: TemperatureUnitService,
    private precipitationUnitService: PrecipitationUnitService,
    private climateVariableHelper: ClimateVariableHelperService,
  ) {}

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

    return UnitUtils.getDisplayUnit(
      climateVariable.unit,
      variableType,
      this.temperatureUnitService.getUnit(),
      this.precipitationUnitService.getUnit(),
    );
  }

  onVariableTypeChange(event: any): void {
    if (this.controlsData) {
      this.controlsData.selectedVariableType = event.value;
      this.emitChange();

      const variableName =
        this.controlsOptions?.climateVariables?.[event.value as ClimateVarKey]
          ?.displayName || event.value;
      this.tracker.trackEvent(
        'Variable Selection',
        'Variable Change',
        variableName,
      );
    }
  }

  onResolutionChange(event: any): void {
    if (this.controlsData) {
      this.controlsData.selectedResolution = event.value;
      this.emitChange();

      const resolutionName = this.getResolutionDisplayName(event.value);
      this.tracker.trackEvent(
        'Control Selection',
        'Resolution Change',
        resolutionName,
      );
    }
  }

  onClimateScenarioChange(event: any): void {
    if (this.controlsData) {
      this.controlsData.selectedClimateScenario = event.value;
      this.emitChange();

      const scenarioName = this.getClimateScenarioDisplayName(event.value);
      this.tracker.trackEvent(
        'Control Selection',
        'Climate Scenario Change',
        scenarioName,
      );
    }
  }

  onClimateModelChange(event: any): void {
    if (this.controlsData) {
      this.controlsData.selectedClimateModel = event.value;
      this.emitChange();

      const modelName = this.getClimateModelDisplayName(event.value);
      this.tracker.trackEvent(
        'Control Selection',
        'Climate Model Change',
        modelName,
      );
    }
  }

  onDifferenceMapChange(event: any): void {
    if (this.controlsData) {
      this.controlsData.showDifferenceMap = event;
      this.emitChange();

      this.tracker.trackEvent(
        'Control Selection',
        'Difference Map Toggle',
        event ? 'Enabled' : 'Disabled',
        event ? 1 : 0,
      );
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

  shouldDisableYearSlider(): boolean {
    if (!this.controlsData?.selectedVariableType) {
      return false;
    }
    return !this.climateVariableHelper.hasFuturePredictions(
      this.controlsData.selectedVariableType,
    );
  }

  private emitChange(): void {
    if (this.controlsData) {
      this.controlsChange.emit(this.controlsData);
    }
  }
}
