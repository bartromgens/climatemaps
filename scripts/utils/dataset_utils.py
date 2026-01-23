from datetime import datetime
from typing import List, Union

from climatemaps.bbox import BoundingBox
from climatemaps.datasets import (
    ClimateDataConfig,
    ClimateDifferenceDataConfig,
    ClimateModel,
    ClimateScenario,
    ClimateVarKey,
    HISTORIC_DATA_SETS,
    FUTURE_DATA_SETS,
    DIFFERENCE_DATA_SETS,
)
from climatemaps.logger import logger


def filter_datasets(
    climate_model: ClimateModel | None = None,
    variable_type: ClimateVarKey | None = None,
    dataset_type: str | None = None,
    future_date_range: tuple[int, int] | None = None,
    climate_scenario: ClimateScenario | None = None,
) -> List[Union[ClimateDataConfig, ClimateDifferenceDataConfig]]:
    dataset_groups = {
        "historic": HISTORIC_DATA_SETS,
        "future": FUTURE_DATA_SETS,
        "difference": DIFFERENCE_DATA_SETS,
    }

    if dataset_type is not None:
        if dataset_type not in dataset_groups:
            logger.warning(
                f"No datasets found for type '{dataset_type}'. "
                f"Available types: {', '.join(dataset_groups.keys())}"
            )
            return []
        dataset_groups = {dataset_type: dataset_groups[dataset_type]}

    all_datasets = []

    for name, datasets in dataset_groups.items():
        filtered = list(datasets)

        if climate_model is not None:
            if name == "historic":
                filtered = []
            else:
                filtered = [ds for ds in filtered if ds.get_climate_model() == climate_model]

        if variable_type is not None:
            filtered = [ds for ds in filtered if ds.get_variable_type() == variable_type]

        if future_date_range is not None and name in ("future", "difference"):
            filtered = [ds for ds in filtered if ds.get_year_range() == future_date_range]

        if climate_scenario is not None and name in ("future", "difference"):
            filtered = [ds for ds in filtered if ds.get_climate_scenario() == climate_scenario]

        all_datasets.extend(filtered)

    return all_datasets


def create_tasks(
    datasets: List[Union[ClimateDataConfig, ClimateDifferenceDataConfig]],
    month_lower: int,
    month_upper: int,
    force_recreate: bool,
    if_older_than: datetime | None = None,
    bbox: BoundingBox | None = None,
) -> List[tuple]:
    tasks = [
        (config, month, force_recreate, if_older_than, bbox)
        for config in datasets
        for month in range(month_lower, month_upper + 1)
    ]

    month_range = f"{month_lower}-{month_upper}" if month_lower != month_upper else str(month_lower)
    logger.info(f"Created {len(tasks)} tasks (months {month_range}, {len(datasets)} datasets)")

    return tasks
