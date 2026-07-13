from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from analytics_framework import PipelineStep


class PlotAveragePaceByDriverStep(PipelineStep):
    """
    Pipeline step used to plot average race pace by driver.
    """

    def __init__(
        self,
        input_key: str = "driver_summary",
        output_path: str | Path = "reports/figures/average_pace_by_driver.png",
        output_key: str = "average_pace_figure_path",
    ):
        super().__init__("Plot Average Pace By Driver")
        self.input_key = input_key
        self.output_path = Path(output_path)
        self.output_key = output_key

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        driver_summary = context[self.input_key].copy()
        driver_summary = driver_summary.sort_values("average_lap_time")

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        plt.figure(figsize=(12, 6))
        plt.bar(
            driver_summary["Driver"],
            driver_summary["average_lap_time"],
        )
        plt.title("Average Race Pace by Driver")
        plt.xlabel("Driver")
        plt.ylabel("Average Lap Time Seconds")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(self.output_path)
        plt.close()

        context[self.output_key] = self.output_path

        return context


class PlotWinnerLapTimeEvolutionStep(PipelineStep):
    """
    Pipeline step used to plot winner lap time evolution.
    """

    def __init__(
        self,
        laps_key: str = "laps",
        winner_key: str = "winner",
        output_path: str | Path = "reports/figures/winner_lap_time.png",
        output_key: str = "winner_lap_time_figure_path",
    ):
        super().__init__("Plot Winner Lap Time Evolution")
        self.laps_key = laps_key
        self.winner_key = winner_key
        self.output_path = Path(output_path)
        self.output_key = output_key

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        laps = context[self.laps_key].copy()
        winner = context[self.winner_key]
        winner_code = winner["driver"]

        winner_laps = laps[
            (laps["Driver"] == winner_code)
            & laps["PitInTime"].isna()
            & laps["PitOutTime"].isna()
        ].copy()

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        plt.figure(figsize=(12, 6))
        plt.plot(
            winner_laps["LapNumber"],
            winner_laps["lap_time_seconds"],
            marker="o",
        )
        plt.title(f"{winner_code} Lap Time Evolution")
        plt.xlabel("Lap")
        plt.ylabel("Lap Time Seconds")
        plt.tight_layout()
        plt.savefig(self.output_path)
        plt.close()

        context[self.output_key] = self.output_path

        return context
