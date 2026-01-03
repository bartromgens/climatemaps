# Datasets Module

This module contains all climate dataset configurations for the OpenClimateMap project. It has been refactored into a modular structure for better maintainability and extensibility.

## Module Structure

```
datasets/
├── __init__.py           # Public API exports
├── enums.py             # Enum definitions (DataFormat, ClimateVarKey, etc.)
├── models.py            # Data models and configuration classes
├── conversions.py       # Data conversion functions
├── config.py            # Climate variables and contour configurations
├── historic.py          # Historical dataset configurations
├── future.py            # Future climate projection configurations
└── difference.py        # Difference map configurations (future - historical)
```

## Adding a New Dataset Configuration

### 1. Historic Dataset

Edit `historic.py` and add a new configuration group to `HISTORIC_DATA_GROUPS`:

```python
HISTORIC_DATA_GROUPS: List[ClimateDataConfigGroup] = [
    # ... existing groups ...
    CHELSAClimateDataConfigGroup(
        variable_types=[ClimateVarKey.YOUR_VARIABLE],
        format=DataFormat.YOUR_FORMAT,
        source="https://your-data-source.com",
        resolutions=[SpatialResolution.MIN0_5],
        year_ranges=[(1981, 2010)],
    ),
]
```

### 2. Future Dataset

Edit `future.py` and add a new configuration group to `FUTURE_DATA_GROUPS`:

```python
FUTURE_DATA_GROUPS: List[FutureClimateDataConfigGroup] = [
    # ... existing groups ...
    FutureClimateDataConfigGroup(
        variable_types=[ClimateVarKey.YOUR_VARIABLE],
        format=DataFormat.GEOTIFF_WORLDCLIM_CMIP6,
        source="https://your-data-source.com",
        resolutions=[SpatialResolution.MIN10],
        year_ranges=FUTURE_DATE_RANGES,
        climate_scenarios=[ClimateScenario.SSP126, ClimateScenario.SSP585],
        climate_models=[ClimateModel.ENSEMBLE_MEAN],
        filepath_template=FUTURE_FILE_TEMPLATE,
    ),
]
```

### 3. New Climate Variable

1. Add the variable enum to `enums.py`:
```python
class ClimateVarKey(enum.Enum):
    YOUR_VARIABLE = "YOUR_VARIABLE"
```

2. Add the variable definition to `config.py`:
```python
CLIMATE_VARIABLES: Dict[ClimateVarKey, ClimateVariable] = {
    ClimateVarKey.YOUR_VARIABLE: ClimateVariable(
        name="YourVariable",
        display_name="Your Variable Display Name",
        unit="unit",
        filename="yourvar"
    ),
}
```

3. Add the contour configuration to `config.py`:
```python
CLIMATE_CONTOUR_CONFIGS: Dict[ClimateVarKey, ContourPlotConfig] = {
    ClimateVarKey.YOUR_VARIABLE: ContourPlotConfig(
        level_lower=0,
        level_upper=100,
        colormap=plt.cm.viridis,
        title="Your Variable",
        unit="unit"
    ),
}
```

### 4. New Data Format

1. Add the format enum to `enums.py`:
```python
class DataFormat(enum.Enum):
    YOUR_FORMAT = "YOUR_FORMAT"
```

2. Create a custom config group class in `models.py` if the format requires special handling (like CHELSA or CRU TS do).

### 5. Data Conversion Function

If your dataset requires custom data conversion, add it to `conversions.py`:

```python
def your_conversion_function(
    values: npt.NDArray[np.floating], month: int
) -> npt.NDArray[np.floating]:
    # Your conversion logic here
    return converted_values
```

## Key Concepts

- **ClimateDataConfig**: Base configuration class for a single dataset
- **FutureClimateDataConfig**: Configuration for future climate projections
- **ClimateDifferenceDataConfig**: Configuration for difference maps (future - historical)
- **ClimateDataConfigGroup**: Groups multiple configurations with similar parameters
- **Config Groups**: Use these to define multiple datasets efficiently (they generate individual configs via `create_configs()`)

## Best Practices

1. **Separation of concerns**: Keep configuration data separate from business logic
2. **Use config groups**: When defining multiple related datasets, use config groups rather than individual configs
3. **Type hints**: Always include proper type hints for better code clarity
4. **Enums over strings**: Use enums for categorical values (climate models, variables, etc.)
5. **Document sources**: Always include the source URL for dataset configurations

