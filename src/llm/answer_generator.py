import os
from typing import Any

import pandas as pd
from analytics_framework import PipelineStep
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

from src.llm.prompts import ANSWER_GENERATOR_SYSTEM_PROMPT


class GeneratedF1Answer(BaseModel):
    """
    Structured final answer generated from F1 analysis results.
    """

    answer: str = Field(
        description="Final natural language answer to the user's question."
    )

    key_reasons: list[str] = Field(
        default_factory=list,
        description="Main reasons supporting the answer.",
    )

    confidence: str = Field(
        default="medium",
        description="Confidence level based on available data: low, medium or high.",
    )

    answer_mode: str = Field(
        default="mock",
        description="Answer generation mode: mock or openai.",
    )


def _dataframe_to_records(
    value: Any,
    max_rows: int = 10,
) -> Any:
    if isinstance(value, pd.DataFrame):
        return value.head(max_rows).to_dict(orient="records")

    return value


def _build_answer_payload(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "original_question": context.get("original_question"),
        "parsed_question": context.get("parsed_question"),
        "analysis_route": context.get("analysis_route"),
        "winner": context.get("winner"),
        "driver_summary": _dataframe_to_records(
            context.get("driver_summary"),
            max_rows=10,
        ),
        "tyre_strategy": _dataframe_to_records(
            context.get("tyre_strategy"),
            max_rows=20,
        ),
        "race_insights": context.get("race_insights"),
    }


def mock_generate_f1_answer(context: dict[str, Any]) -> GeneratedF1Answer:
    """
    Generate a local deterministic answer without calling the OpenAI API.
    """
    winner = context.get("winner", {})
    race_insights = context.get("race_insights", [])

    winner_name = winner.get("full_name") or winner.get("driver")
    winner_team = winner.get("team")

    if winner_name and winner_team:
        introduction = f"{winner_name} won the race for {winner_team}."
    elif winner_name:
        introduction = f"{winner_name} won the race."
    else:
        introduction = "The race winner was identified from the race results."

    if race_insights:
        reasons_text = " ".join(race_insights)
    else:
        reasons_text = (
            "The explanation is based on the available race result, pace and "
            "strategy metrics."
        )

    answer = f"{introduction} {reasons_text}"

    return GeneratedF1Answer(
        answer=answer,
        key_reasons=race_insights,
        confidence="medium",
        answer_mode="mock",
    )


def openai_generate_f1_answer(
    context: dict[str, Any],
    model: str | None = None,
) -> GeneratedF1Answer:
    """
    Generate a final answer using OpenAI from structured pipeline outputs.
    """
    selected_model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    client = OpenAI()
    payload = _build_answer_payload(context)

    response = client.responses.parse(
        model=selected_model,
        input=[
            {
                "role": "system",
                "content": ANSWER_GENERATOR_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": str(payload),
            },
        ],
        text_format=GeneratedF1Answer,
    )

    generated_answer = response.output_parsed
    generated_answer.answer_mode = "openai"

    return generated_answer


def generate_f1_answer(
    context: dict[str, Any],
    model: str | None = None,
) -> GeneratedF1Answer:
    """
    Generate the final answer from pipeline outputs.

    Supported modes:
    - mock: local deterministic answer
    - openai: OpenAI answer generation with fallback to mock
    """
    load_dotenv()

    mode = os.getenv("F1_LLM_MODE", "mock").lower()

    if mode == "mock":
        return mock_generate_f1_answer(context)

    try:
        return openai_generate_f1_answer(context=context, model=model)
    except Exception as error:
        print(f"OpenAI answer generation failed, falling back to mock: {error}")
        return mock_generate_f1_answer(context)


class GenerateF1AnswerStep(PipelineStep):
    """
    Pipeline step used to generate a final natural language answer.
    """

    def __init__(
        self,
        output_key: str = "final_answer",
    ):
        super().__init__("Generate F1 Answer")
        self.output_key = output_key

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        generated_answer = generate_f1_answer(context)
        context[self.output_key] = generated_answer.model_dump()

        return context
