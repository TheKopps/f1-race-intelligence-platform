from typing import Any

from analytics_framework import PipelineStep


class ComputeRaceResultsStep(PipelineStep):
    """
    Pipeline step used to extract race results and identify the winner.
    """

    def __init__(
        self,
        input_key: str = "session",
        results_key: str = "race_results",
        winner_key: str = "winner",
    ):
        super().__init__("Compute Race Results")
        self.input_key = input_key
        self.results_key = results_key
        self.winner_key = winner_key

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        session = context[self.input_key]

        results = session.results.copy()

        selected_columns = [
            "Position",
            "ClassifiedPosition",
            "DriverNumber",
            "Abbreviation",
            "FullName",
            "TeamName",
            "GridPosition",
            "Status",
            "Points",
        ]

        existing_columns = [
            column for column in selected_columns if column in results.columns
        ]

        results = results[existing_columns].copy()

        if "Position" in results.columns:
            results = results.sort_values("Position").reset_index(drop=True)

        winner_row = results.iloc[0]

        winner = {
            "driver": winner_row.get("Abbreviation"),
            "full_name": winner_row.get("FullName"),
            "team": winner_row.get("TeamName"),
            "position": winner_row.get("Position"),
            "status": winner_row.get("Status"),
        }

        context[self.results_key] = results
        context[self.winner_key] = winner

        return context
