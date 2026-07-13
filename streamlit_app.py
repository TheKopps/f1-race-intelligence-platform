from pathlib import Path

import streamlit as st

from app import build_explain_winner_pipeline
from src.llm.question_parser import parse_f1_question
from src.router.analysis_router import route_analysis_request

PROJECT_ROOT = Path(__file__).resolve().parent


st.set_page_config(
    page_title="F1 Race Intelligence Platform",
    page_icon="🏎️",
    layout="wide",
)


st.title("🏎️ F1 Race Intelligence Platform")

st.markdown(
    """
Ask a Formula 1 race question and get a data-driven answer using FastF1,
a question parser, an analysis router and automated race analytics.
"""
)

st.sidebar.title("Settings")

example_questions = [
    "Qui a gagné Bahrain 2023 et pourquoi ?",
    "Who won Bahrain 2023 and why?",
    "Compare Leclerc et Sainz à Bahrain 2023",
    "Ferrari pouvait-elle faire mieux à Bahrain 2023 ?",
    "Quelle était la stratégie pneus à Bahrain 2023 ?",
]

selected_example = st.sidebar.selectbox(
    "Example questions",
    example_questions,
)

question = st.text_input(
    "Ask an F1 question",
    value=selected_example,
)

run_analysis = st.button("Run analysis")


def run_question_analysis(question: str) -> dict:
    parsed_question = parse_f1_question(question)
    route = route_analysis_request(parsed_question)

    if not route.can_run:
        return {
            "parsed_question": parsed_question,
            "route": route,
            "result": None,
            "error": route.message,
        }

    if route.pipeline_name not in {
        "race_winner_pipeline",
        "explain_winner_pipeline",
    }:
        return {
            "parsed_question": parsed_question,
            "route": route,
            "result": None,
            "error": (
                "This pipeline is not implemented yet. "
                f"Requested pipeline: {route.pipeline_name}"
            ),
        }

    pipeline = build_explain_winner_pipeline(
        year=route.year,
        grand_prix=route.grand_prix,
        session_type=route.session_type,
    )

    pipeline.context["original_question"] = parsed_question.original_question
    pipeline.context["parsed_question"] = parsed_question.model_dump()
    pipeline.context["analysis_route"] = route.model_dump()

    result = pipeline.run()

    return {
        "parsed_question": parsed_question,
        "route": route,
        "result": result,
        "error": None,
    }


if run_analysis:
    with st.spinner("Running F1 analysis... First FastF1 load can take some time."):
        analysis = run_question_analysis(question)

    parsed_question = analysis["parsed_question"]
    route = analysis["route"]
    result = analysis["result"]
    error = analysis["error"]

    st.subheader("Parsed Question")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Intent", parsed_question.intent)

    with col2:
        st.metric("Grand Prix", parsed_question.grand_prix or "Missing")

    with col3:
        st.metric("Year", parsed_question.year or "Missing")

    with st.expander("View parsed question JSON"):
        st.json(parsed_question.model_dump())

    st.subheader("Analysis Route")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Pipeline", route.pipeline_name)

    with col2:
        st.metric("Can run", str(route.can_run))

    with col3:
        st.metric("Session", route.session_type)

    with st.expander("View route JSON"):
        st.json(route.model_dump())

    if error is not None:
        st.error(error)
        st.stop()

    st.subheader("Final Answer")

    final_answer = result["final_answer"]

    st.write(final_answer["answer"])

    st.markdown("### Key reasons")

    for reason in final_answer["key_reasons"]:
        st.markdown(f"- {reason}")

    st.markdown("### Winner")

    st.json(result["winner"])

    st.markdown("### Driver Summary")

    st.dataframe(
        result["driver_summary"],
        use_container_width=True,
    )

    st.markdown("### Tyre Strategy")

    st.dataframe(
        result["tyre_strategy"],
        use_container_width=True,
    )

    st.markdown("### Visualizations")

    fig_col1, fig_col2 = st.columns(2)

    average_pace_figure = result.get("average_pace_figure_path")
    winner_lap_time_figure = result.get("winner_lap_time_figure_path")

    with fig_col1:
        if average_pace_figure is not None:
            st.image(
                str(average_pace_figure),
                caption="Average race pace by driver",
                use_container_width=True,
            )

    with fig_col2:
        if winner_lap_time_figure is not None:
            st.image(
                str(winner_lap_time_figure),
                caption="Winner lap time evolution",
                use_container_width=True,
            )

    st.markdown("### Generated Report")

    report_path = result.get("markdown_report_path")

    if report_path is not None:
        st.success(f"Markdown report generated: {report_path}")

        with open(report_path, encoding="utf-8") as report_file:
            report_content = report_file.read()

        with st.expander("View Markdown report"):
            st.markdown(report_content)
