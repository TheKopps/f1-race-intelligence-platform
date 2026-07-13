import os
import re
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

from src.llm.prompts import QUESTION_PARSER_SYSTEM_PROMPT


class ParsedF1Question(BaseModel):
    """
    Structured representation of a Formula 1 analytics question.
    """

    intent: Literal[
        "race_winner",
        "explain_winner",
        "compare_drivers",
        "team_debrief",
        "tyre_strategy",
        "unknown",
    ] = Field(description="Detected intent of the user's F1 question.")

    year: int | None = Field(
        default=None,
        description="Race year if mentioned in the question.",
    )

    grand_prix: str | None = Field(
        default=None,
        description="Grand Prix name if mentioned in the question.",
    )

    session_type: str = Field(
        default="R",
        description="FastF1 session type. Use R for race by default.",
    )

    driver: str | None = Field(
        default=None,
        description="Main driver code if explicitly mentioned.",
    )

    team: str | None = Field(
        default=None,
        description="Main team if explicitly mentioned.",
    )

    comparison_drivers: list[str] = Field(
        default_factory=list,
        description="Driver codes to compare if comparison is requested.",
    )

    needs_charts: bool = Field(
        default=True,
        description="Whether charts are useful for answering the question.",
    )

    analysis_modules: list[str] = Field(
        default_factory=list,
        description="Analysis modules required to answer the question.",
    )

    original_question: str = Field(
        description="Original user question.",
    )

    parser_mode: str = Field(
        default="mock",
        description="Parser mode used to parse the question.",
    )


GRAND_PRIX_ALIASES = {
    "bahrain": "Bahrain",
    "monaco": "Monaco",
    "monza": "Italian",
    "italy": "Italian",
    "italian": "Italian",
    "miami": "Miami",
    "silverstone": "British",
    "british": "British",
    "spa": "Belgian",
    "belgian": "Belgian",
    "jeddah": "Saudi Arabian",
    "saudi": "Saudi Arabian",
    "australia": "Australian",
    "australian": "Australian",
    "japan": "Japanese",
    "japanese": "Japanese",
    "singapore": "Singapore",
    "abu dhabi": "Abu Dhabi",
    "qatar": "Qatar",
    "austria": "Austrian",
    "austrian": "Austrian",
    "canada": "Canadian",
    "canadian": "Canadian",
    "spain": "Spanish",
    "spanish": "Spanish",
    "hungary": "Hungarian",
    "hungarian": "Hungarian",
    "zandvoort": "Dutch",
    "dutch": "Dutch",
    "mexico": "Mexico City",
    "brazil": "São Paulo",
    "sao paulo": "São Paulo",
    "las vegas": "Las Vegas",
}

DRIVER_ALIASES = {
    "verstappen": "VER",
    "max": "VER",
    "perez": "PER",
    "leclerc": "LEC",
    "charles": "LEC",
    "sainz": "SAI",
    "carlos": "SAI",
    "hamilton": "HAM",
    "lewis": "HAM",
    "russell": "RUS",
    "george": "RUS",
    "alonso": "ALO",
    "fernando": "ALO",
    "norris": "NOR",
    "lando": "NOR",
    "piastri": "PIA",
    "oscar": "PIA",
    "gasly": "GAS",
    "ocon": "OCO",
    "stroll": "STR",
    "bottas": "BOT",
    "tsunoda": "TSU",
    "albon": "ALB",
    "hulkenberg": "HUL",
    "magnussen": "MAG",
}

TEAM_ALIASES = {
    "ferrari": "Ferrari",
    "red bull": "Red Bull",
    "mercedes": "Mercedes",
    "mclaren": "McLaren",
    "aston martin": "Aston Martin",
    "alpine": "Alpine",
    "williams": "Williams",
    "haas": "Haas",
    "sauber": "Sauber",
    "alphatauri": "AlphaTauri",
}


def _extract_year(question: str) -> int | None:
    match = re.search(r"\b(20\d{2})\b", question)

    if match is None:
        return None

    return int(match.group(1))


def _extract_grand_prix(question: str) -> str | None:
    question_lower = question.lower()

    for alias, grand_prix in GRAND_PRIX_ALIASES.items():
        if alias in question_lower:
            return grand_prix

    return None


def _extract_drivers(question: str) -> list[str]:
    question_lower = question.lower()
    drivers = []

    for alias, driver_code in DRIVER_ALIASES.items():
        if alias in question_lower and driver_code not in drivers:
            drivers.append(driver_code)

    return drivers


def _extract_team(question: str) -> str | None:
    question_lower = question.lower()

    for alias, team in TEAM_ALIASES.items():
        if alias in question_lower:
            return team

    return None


def _detect_intent(question: str) -> str:
    question_lower = question.lower()

    winner_patterns = [
        "qui a gagné",
        "who won",
        "winner",
        "vainqueur",
    ]

    why_patterns = [
        "pourquoi",
        "why",
        "expliquer",
        "explain",
    ]

    compare_patterns = [
        "compare",
        "comparaison",
        "comparer",
        "versus",
        " vs ",
    ]

    tyre_patterns = [
        "pneu",
        "pneus",
        "tyre",
        "tire",
        "compound",
        "stratégie",
        "strategie",
        "strategy",
        "pit",
        "arrêt",
        "arret",
    ]

    team_debrief_patterns = [
        "pouvait",
        "faire mieux",
        "could",
        "better result",
        "debrief",
    ]

    if any(pattern in question_lower for pattern in compare_patterns):
        return "compare_drivers"

    if any(pattern in question_lower for pattern in tyre_patterns):
        return "tyre_strategy"

    if any(pattern in question_lower for pattern in team_debrief_patterns):
        return "team_debrief"

    asks_winner = any(pattern in question_lower for pattern in winner_patterns)
    asks_why = any(pattern in question_lower for pattern in why_patterns)

    if asks_winner and asks_why:
        return "explain_winner"

    if asks_winner:
        return "race_winner"

    return "unknown"


def _get_analysis_modules(intent: str) -> list[str]:
    modules_by_intent = {
        "race_winner": [
            "race_result",
        ],
        "explain_winner": [
            "race_result",
            "race_pace",
            "tyre_strategy",
            "consistency",
        ],
        "compare_drivers": [
            "race_pace",
            "consistency",
            "driver_comparison",
        ],
        "team_debrief": [
            "race_result",
            "race_pace",
            "tyre_strategy",
            "team_analysis",
        ],
        "tyre_strategy": [
            "tyre_strategy",
            "race_pace",
        ],
        "unknown": [],
    }

    return modules_by_intent.get(intent, [])


def mock_parse_f1_question(question: str) -> ParsedF1Question:
    """
    Parse an F1 question locally without calling the OpenAI API.

    This mode is useful during development when API quota is unavailable.
    """
    intent = _detect_intent(question)
    drivers = _extract_drivers(question)

    driver = drivers[0] if len(drivers) == 1 else None
    comparison_drivers = drivers if intent == "compare_drivers" else []

    return ParsedF1Question(
        intent=intent,
        year=_extract_year(question),
        grand_prix=_extract_grand_prix(question),
        session_type="R",
        driver=driver,
        team=_extract_team(question),
        comparison_drivers=comparison_drivers,
        needs_charts=intent != "unknown",
        analysis_modules=_get_analysis_modules(intent),
        original_question=question,
        parser_mode="mock",
    )


def openai_parse_f1_question(
    question: str,
    model: str | None = None,
) -> ParsedF1Question:
    """
    Parse a natural language F1 question using OpenAI Structured Outputs.
    """
    selected_model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    client = OpenAI()

    response = client.responses.parse(
        model=selected_model,
        input=[
            {
                "role": "system",
                "content": QUESTION_PARSER_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": question,
            },
        ],
        text_format=ParsedF1Question,
    )

    parsed_question = response.output_parsed
    parsed_question.original_question = question
    parsed_question.parser_mode = "openai"

    return parsed_question


def parse_f1_question(
    question: str,
    model: str | None = None,
) -> ParsedF1Question:
    """
    Parse a natural language F1 question into a structured analysis request.

    Supported modes:
    - mock: local rule-based parser
    - openai: OpenAI API parser, with fallback to mock if the API fails
    """
    load_dotenv()

    mode = os.getenv("F1_LLM_MODE", "mock").lower()

    if mode == "mock":
        return mock_parse_f1_question(question)

    try:
        return openai_parse_f1_question(question=question, model=model)
    except Exception as error:
        print(f"OpenAI parser failed, falling back to mock parser: {error}")
        return mock_parse_f1_question(question)


if __name__ == "__main__":
    questions = [
        "Qui a gagné Bahrain 2023 et pourquoi ?",
        "Compare Leclerc et Sainz à Bahrain 2023",
        "Ferrari pouvait-elle faire mieux à Bahrain 2023 ?",
        "Quelle était la stratégie pneus à Bahrain 2023 ?",
    ]

    for question in questions:
        parsed = parse_f1_question(question)
        print(parsed.model_dump_json(indent=2))
        print("-" * 80)
