from typing import List

from climatemaps.datasets.future import FUTURE_DATA_SETS
from climatemaps.datasets.historic import HISTORIC_DATA_SETS
from climatemaps.datasets.models import ClimateDifferenceDataConfig


def create_difference_map_configs() -> List[ClimateDifferenceDataConfig]:
    difference_configs = []

    for future_config in FUTURE_DATA_SETS:
        historical_config = None
        for hist_config in HISTORIC_DATA_SETS:
            if (
                hist_config.variable_type == future_config.variable_type
                and hist_config.resolution_input == future_config.resolution_input
            ):
                historical_config = hist_config
                break

        if historical_config:
            diff_config = ClimateDifferenceDataConfig(
                variable_type=future_config.variable_type,
                filepath="",
                format=future_config.format,
                resolution_input=future_config.resolution_input,
                year_range=future_config.year_range,
                reader_function=future_config.reader_function,
                conversion_function=None,
                conversion_factor=1,
                source=f"Difference: {future_config.source} - {historical_config.source}",
                historical_config=historical_config,
                future_config=future_config,
            )
            difference_configs.append(diff_config)

    return difference_configs


DIFFERENCE_DATA_SETS: List[ClimateDifferenceDataConfig] = create_difference_map_configs()
