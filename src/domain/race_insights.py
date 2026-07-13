from typing import Any

import pandas as pd
from analytics_framework import PipelineStep


class GenerateWinnerExplanationStep(PipelineStep):
    """
    Pipeline step used to generate a data-driven explanation of the race winner.
    """

    def __init__(
        self,
        winner_key: str = "winner",
        driver_summary_key: str = "driver_summary",
        tyre_strategy_key: str = "tyre_strategy",
        output_key: str = "race_insights",
    ):
        super().__init__("Generate Winner Explanation")
        self.winner_key = winner_key
        self.driver_summary_key = driver_summary_key
        self.tyre_strategy_key = tyre_strategy_key
        self.output_key = output_key

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        winner = context[self.winner_key]
        driver_summary = context[self.driver_summary_key]
        tyre_strategy = context[self.tyre_strategy_key]

        winner_code = winner["driver"]
        insights = []

        insights.append(f"{winner['full_name']} won the race for {winner['team']}.")

        winner_pace = driver_summary[driver_summary["Driver"] == winner_code]

        if isinstance(winner_pace, pd.DataFrame) and not winner_pace.empty:
            row = winner_pace.iloc[0]

            insights.append(
                f"{winner_code} ranked P{int(row['average_pace_rank'])} "
                f"on average race pace with an average lap time of "
                f"{row['average_lap_time']:.2f} seconds."
            )

            insights.append(
                f"{winner_code}'s best clean lap was "
                f"{row['best_lap_time']:.2f} seconds."
            )

            insights.append(
                f"{winner_code} ranked P{int(row['consistency_rank'])} "
                "for consistency based on lap time standard deviation."
            )

        winner_strategy = tyre_strategy[tyre_strategy["Driver"] == winner_code]

        if isinstance(winner_strategy, pd.DataFrame) and not winner_strategy.empty:
            compounds = winner_strategy["Compound"].dropna().tolist()
            stint_count = winner_strategy["Stint"].nunique()

            insights.append(
                f"{winner_code} completed {stint_count} stints using "
                f"the following compounds: {', '.join(compounds)}."
            )

        insights.append(
            "The result can be explained through a combination of race pace, "
            "consistency, tyre strategy and clean execution."
        )

        context[self.output_key] = insights

        return context
