#!/usr/bin/env python3

import argparse
from pathlib import Path
from typing import List

from climatemaps.datasets import (
    ClimateScenario,
    ClimateVarKey,
    SpatialResolution,
)
from climatemaps.ensemble import compute_ensemble_mean
from climatemaps.logger import logger


def generate_all_ensemble_means(
    base_dir: Path,
    output_dir: Path,
    variables: List[ClimateVarKey] = None,
    scenarios: List[ClimateScenario] = None,
    resolutions: List[SpatialResolution] = None,
) -> None:
    if variables is None:
        variables = [ClimateVarKey.T_MIN, ClimateVarKey.T_MAX, ClimateVarKey.PRECIPITATION]

    if scenarios is None:
        scenarios = [
            ClimateScenario.SSP126,
            ClimateScenario.SSP245,
            ClimateScenario.SSP370,
            ClimateScenario.SSP585,
        ]

    if resolutions is None:
        resolutions = [SpatialResolution.MIN10]

    year_ranges = [(2021, 2040), (2041, 2060), (2061, 2080), (2081, 2100)]

    total = len(variables) * len(scenarios) * len(resolutions) * len(year_ranges)
    processed = 0

    for variable in variables:
        for scenario in scenarios:
            for resolution in resolutions:
                for year_range in year_ranges:
                    processed += 1
                    logger.info(f"\nProcessing {processed}/{total}")

                    try:
                        compute_ensemble_mean(
                            base_dir,
                            resolution,
                            variable,
                            scenario,
                            year_range,
                            output_dir,
                        )
                    except FileNotFoundError as e:
                        logger.warning(f"Skipping: {e}")
                        continue
                    except Exception as e:
                        logger.error(
                            f"Error processing {variable.name} {scenario.name} {year_range}: {e}"
                        )
                        continue

    logger.info(f"\nCompleted processing {processed} combinations")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate ensemble mean climate data from individual climate models"
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("data/raw/worldclim/future"),
        help="Base directory containing individual model files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw/worldclim/future"),
        help="Output directory for ensemble mean files",
    )

    args = parser.parse_args()

    generate_all_ensemble_means(
        base_dir=args.base_dir,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
