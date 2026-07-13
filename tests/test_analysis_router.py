from src.llm.question_parser import mock_parse_f1_question
from src.router.analysis_router import route_analysis_request


def test_route_explain_winner_question():
    parsed_question = mock_parse_f1_question("Qui a gagné Bahrain 2023 et pourquoi ?")

    route = route_analysis_request(parsed_question)

    assert route.can_run is True
    assert route.intent == "explain_winner"
    assert route.pipeline_name == "explain_winner_pipeline"
    assert route.year == 2023
    assert route.grand_prix == "Bahrain"


def test_route_compare_drivers_question():
    parsed_question = mock_parse_f1_question("Compare Leclerc et Sainz à Bahrain 2023")

    route = route_analysis_request(parsed_question)

    assert route.can_run is True
    assert route.intent == "compare_drivers"
    assert route.pipeline_name == "compare_drivers_pipeline"
    assert route.comparison_drivers == ["LEC", "SAI"]


def test_route_missing_year_cannot_run():
    parsed_question = mock_parse_f1_question("Qui a gagné Bahrain et pourquoi ?")

    route = route_analysis_request(parsed_question)

    assert route.can_run is False
    assert "year" in route.missing_fields


def test_route_unknown_question_cannot_run():
    parsed_question = mock_parse_f1_question("Quelle est la meilleure pizza ?")

    route = route_analysis_request(parsed_question)

    assert route.can_run is False
    assert route.pipeline_name == "unknown_pipeline"
    assert "intent" in route.missing_fields
