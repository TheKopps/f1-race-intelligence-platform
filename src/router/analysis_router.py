from typing import Literal

from pydantic import BaseModel, Field

from src.llm.question_parser import ParsedF1Question

PipelineName = Literal[
    "race_winner_pipeline",
    "explain_winner_pipeline",
    "compare_drivers_pipeline",
    "team_debrief_pipeline",
    "tyre_strategy_pipeline",
    "unknown_pipeline",
]


class AnalysisRoute(BaseModel):
    """
    Structured route used to decide which analysis pipeline should run.
    """

    intent: str
    pipeline_name: PipelineName
    year: int | None
    grand_prix: str | None
    session_type: str
    driver: str | None
    team: str | None
    comparison_drivers: list[str]
    analysis_modules: list[str]
    needs_charts: bool
    can_run: bool = Field(
        description="Whether the route has enough information to run."
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="Required fields missing from the parsed question.",
    )
    message: str


PIPELINE_BY_INTENT: dict[str, PipelineName] = {
    "race_winner": "race_winner_pipeline",
    "explain_winner": "explain_winner_pipeline",
    "compare_drivers": "compare_drivers_pipeline",
    "team_debrief": "team_debrief_pipeline",
    "tyre_strategy": "tyre_strategy_pipeline",
    "unknown": "unknown_pipeline",
}


def _get_missing_fields(parsed_question: ParsedF1Question) -> list[str]:
    missing_fields = []

    if parsed_question.intent == "unknown":
        missing_fields.append("intent")

    if parsed_question.year is None:
        missing_fields.append("year")

    if parsed_question.grand_prix is None:
        missing_fields.append("grand_prix")

    if (
        parsed_question.intent == "compare_drivers"
        and len(parsed_question.comparison_drivers) < 2
    ):
        missing_fields.append("comparison_drivers")

    if parsed_question.intent == "team_debrief" and parsed_question.team is None:
        missing_fields.append("team")

    return missing_fields


def route_analysis_request(parsed_question: ParsedF1Question) -> AnalysisRoute:
    """
    Convert a parsed F1 question into an executable analysis route.
    """
    missing_fields = _get_missing_fields(parsed_question)
    can_run = len(missing_fields) == 0

    pipeline_name = PIPELINE_BY_INTENT.get(
        parsed_question.intent,
        "unknown_pipeline",
    )

    if can_run:
        message = (
            f"Ready to run {pipeline_name} for "
            f"{parsed_question.grand_prix} {parsed_question.year}."
        )
    else:
        message = "Cannot run analysis yet. Missing fields: " + ", ".join(
            missing_fields
        )

    return AnalysisRoute(
        intent=parsed_question.intent,
        pipeline_name=pipeline_name,
        year=parsed_question.year,
        grand_prix=parsed_question.grand_prix,
        session_type=parsed_question.session_type,
        driver=parsed_question.driver,
        team=parsed_question.team,
        comparison_drivers=parsed_question.comparison_drivers,
        analysis_modules=parsed_question.analysis_modules,
        needs_charts=parsed_question.needs_charts,
        can_run=can_run,
        missing_fields=missing_fields,
        message=message,
    )
