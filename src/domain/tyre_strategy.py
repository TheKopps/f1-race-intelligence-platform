from typing import Any

from analytics_framework import PipelineStep


class ComputeTyreStrategyStep(PipelineStep):
    """
    Pipeline step used to compute tyre strategy by driver and stint.
    """

    def __init__(
        self,
        input_key: str = "laps",
        output_key: str = "tyre_strategy",
    ):
        super().__init__("Compute Tyre Strategy")
        self.input_key = input_key
        self.output_key = output_key

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        laps = context[self.input_key].copy()

        strategy = (
            laps.groupby(["Driver", "Team", "Stint", "Compound"], as_index=False)
            .agg(
                first_lap=("LapNumber", "min"),
                last_lap=("LapNumber", "max"),
                laps_in_stint=("LapNumber", "count"),
                average_lap_time=("lap_time_seconds", "mean"),
                best_lap_time=("lap_time_seconds", "min"),
            )
            .sort_values(["Driver", "Stint"])
            .reset_index(drop=True)
        )

        context[self.output_key] = strategy

        return context
