from pathlib import Path

from analytics_framework import Config, Pipeline, setup_logger
from analytics_framework.export import CSVExportStep, ExcelExportStep
from analytics_framework.reporting import MarkdownReportStep

from src.domain.fastf1_steps import (
    BuildRaceLapsDatasetStep,
    LoadFastF1SessionStep,
)
from src.domain.race_insights import GenerateWinnerExplanationStep
from src.domain.race_pace import ComputeDriverPaceSummaryStep
from src.domain.race_results import ComputeRaceResultsStep
from src.domain.tyre_strategy import ComputeTyreStrategyStep
from src.llm.question_parser import parse_f1_question
from src.router.analysis_router import route_analysis_request
from src.visualization.race_plots import (
    PlotAveragePaceByDriverStep,
    PlotWinnerLapTimeEvolutionStep,
)

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def build_explain_winner_pipeline(
    year: int,
    grand_prix: str,
    session_type: str,
) -> Pipeline:
    config = Config.from_yaml(CONFIG_PATH)

    logger = setup_logger(
        name="f1_race_intelligence",
        log_file=config.resolve_path(
            "outputs.pipeline_log",
            base_path=PROJECT_ROOT,
        ),
    )

    pipeline = Pipeline(
        project_name=config.get("project.name"),
        logger=logger,
        stop_on_error=config.get("pipeline.stop_on_error", True),
    )

    pipeline.add_step(
        LoadFastF1SessionStep(
            year=year,
            grand_prix=grand_prix,
            session_type=session_type,
            cache_path=config.resolve_path(
                "fastf1.cache_path",
                base_path=PROJECT_ROOT,
            ),
            output_key="session",
        )
    )

    pipeline.add_step(BuildRaceLapsDatasetStep())
    pipeline.add_step(ComputeRaceResultsStep())
    pipeline.add_step(ComputeDriverPaceSummaryStep())
    pipeline.add_step(ComputeTyreStrategyStep())
    pipeline.add_step(GenerateWinnerExplanationStep())

    pipeline.add_step(
        CSVExportStep(
            input_key="laps",
            output_path=config.resolve_path(
                "outputs.laps_dataset",
                base_path=PROJECT_ROOT,
            ),
            output_key="laps_export_path",
        )
    )

    pipeline.add_step(
        CSVExportStep(
            input_key="race_results",
            output_path=config.resolve_path(
                "outputs.race_results",
                base_path=PROJECT_ROOT,
            ),
            output_key="race_results_export_path",
        )
    )

    pipeline.add_step(
        CSVExportStep(
            input_key="tyre_strategy",
            output_path=config.resolve_path(
                "outputs.tyre_strategy",
                base_path=PROJECT_ROOT,
            ),
            output_key="tyre_strategy_export_path",
        )
    )

    pipeline.add_step(
        ExcelExportStep(
            input_key="driver_summary",
            output_path=config.resolve_path(
                "outputs.driver_summary",
                base_path=PROJECT_ROOT,
            ).with_suffix(".xlsx"),
            sheet_name="Driver Summary",
            output_key="driver_summary_export_path",
        )
    )

    pipeline.add_step(
        PlotAveragePaceByDriverStep(
            output_path=config.resolve_path(
                "outputs.average_pace_figure",
                base_path=PROJECT_ROOT,
            )
        )
    )

    pipeline.add_step(
        PlotWinnerLapTimeEvolutionStep(
            output_path=config.resolve_path(
                "outputs.winner_lap_time_figure",
                base_path=PROJECT_ROOT,
            )
        )
    )

    pipeline.add_step(
        MarkdownReportStep(
            title=f"F1 Race Intelligence Report - {grand_prix} {year}",
            output_path=config.resolve_path(
                "outputs.race_report",
                base_path=PROJECT_ROOT,
            ),
            context_keys=[
                "winner",
                "driver_summary",
                "tyre_strategy",
                "race_insights",
            ],
        )
    )

    return pipeline


def main() -> None:
    question = input("Ask an F1 question: ")

    parsed_question = parse_f1_question(question)
    route = route_analysis_request(parsed_question)

    print("\nParsed question:")
    print(parsed_question.model_dump_json(indent=2))

    print("\nAnalysis route:")
    print(route.model_dump_json(indent=2))

    if not route.can_run:
        print(f"\n{route.message}")
        return

    if route.pipeline_name not in {
        "race_winner_pipeline",
        "explain_winner_pipeline",
    }:
        print(
            "\nThis pipeline is not implemented yet. "
            f"Requested pipeline: {route.pipeline_name}"
        )
        return

    pipeline = build_explain_winner_pipeline(
        year=route.year,
        grand_prix=route.grand_prix,
        session_type=route.session_type,
    )

    result = pipeline.run()

    print("\nAnswer:")
    for insight in result["race_insights"]:
        print(f"- {insight}")

    print("\nGenerated outputs:")
    print(f"- Race report: {result['markdown_report_path']}")
    print(f"- Average pace figure: {result['average_pace_figure_path']}")
    print(f"- Winner lap time figure: {result['winner_lap_time_figure_path']}")


if __name__ == "__main__":
    main()
