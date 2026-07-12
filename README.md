@'
# F1 Race Intelligence Platform

Question-driven Formula 1 analytics application using FastF1, LLMs and a reusable Python analytics framework.

## Objective

The goal of this project is to answer Formula 1 race questions using real timing and race data from FastF1.

Example questions:

- Who won Bahrain 2023 and why?
- What was Ferrari's tyre strategy?
- Could Ferrari have achieved a better result?
- Compare Leclerc and Sainz race pace.
- Which driver had the best tyre management?

## Tech Stack

- Python
- FastF1
- pandas
- matplotlib
- Streamlit
- OpenAI API
- pydantic
- analytics-framework

## Architecture

```text
User question
      ↓
LLM question parser
      ↓
Structured analysis request
      ↓
Analysis router
      ↓
FastF1 data pipeline
      ↓
Metrics and visualizations
      ↓
LLM answer generator
      ↓
Final answer with charts