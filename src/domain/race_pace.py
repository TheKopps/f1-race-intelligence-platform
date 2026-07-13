from typing import Any

from analytics_framework import PipelineStep


class ComputeDriverPaceSummaryStep(PipelineStep):
    """
    Pipeline step used to compute driver-level race pace metrics.
    """

    def __init__(
        self,
        input_key: str = "laps",
        output_key: str = "driver_summary",
    ):
        super().__init__("Compute Driver Pace Summary")
        self.input_key = input_key
        self.output_key = output_key

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        laps = context[self.input_key].copy()

        clean_laps = laps[
            laps["PitInTime"].isna()
            & laps["PitOutTime"].isna()
            & laps["lap_time_seconds"].notna()
        ].copy()

        driver_summary = (
            clean_laps.groupby(["Driver", "Team"], as_index=False)
            .agg(
                average_lap_time=("lap_time_seconds", "mean"),
                median_lap_time=("lap_time_seconds", "median"),
                best_lap_time=("lap_time_seconds", "min"),
                lap_time_std=("lap_time_seconds", "std"),
                clean_laps=("LapNumber", "count"),
                stints=("Stint", "nunique"),
            )
            .sort_values("average_lap_time")
            .reset_index(drop=True)
        )

        driver_summary["average_pace_rank"] = (
            driver_summary["average_lap_time"].rank(method="min").astype(int)
        )

        driver_summary["consistency_rank"] = (
            driver_summary["lap_time_std"].rank(method="min").astype(int)
        )

        context[self.output_key] = driver_summary

        return context
