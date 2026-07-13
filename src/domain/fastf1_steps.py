from pathlib import Path
from typing import Any

import fastf1
from analytics_framework import PipelineStep


class LoadFastF1SessionStep(PipelineStep):
    """
    Pipeline step used to load a FastF1 session.
    """

    def __init__(
        self,
        year: int,
        grand_prix: str,
        session_type: str,
        cache_path: str | Path,
        output_key: str = "session",
    ):
        super().__init__("Load FastF1 Session")
        self.year = year
        self.grand_prix = grand_prix
        self.session_type = session_type
        self.cache_path = Path(cache_path)
        self.output_key = output_key

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        self.cache_path.mkdir(parents=True, exist_ok=True)
        fastf1.Cache.enable_cache(str(self.cache_path))

        session = fastf1.get_session(
            self.year,
            self.grand_prix,
            self.session_type,
        )
        session.load()

        context[self.output_key] = session

        return context


class BuildRaceLapsDatasetStep(PipelineStep):
    """
    Pipeline step used to prepare a clean race laps dataset.
    """

    def __init__(
        self,
        input_key: str = "session",
        output_key: str = "laps",
    ):
        super().__init__("Build Race Laps Dataset")
        self.input_key = input_key
        self.output_key = output_key

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        session = context[self.input_key]

        laps = session.laps.copy()

        selected_columns = [
            "Driver",
            "Team",
            "LapNumber",
            "LapTime",
            "Compound",
            "TyreLife",
            "Stint",
            "PitInTime",
            "PitOutTime",
            "TrackStatus",
            "IsPersonalBest",
        ]

        existing_columns = [
            column for column in selected_columns if column in laps.columns
        ]

        laps = laps[existing_columns].copy()
        laps = laps[laps["LapTime"].notna()].copy()
        laps["lap_time_seconds"] = laps["LapTime"].dt.total_seconds()

        context[self.output_key] = laps

        return context
