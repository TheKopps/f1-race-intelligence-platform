from src.llm.question_parser import parse_f1_question
from src.router.analysis_router import route_analysis_request


def main() -> None:
    question = input("Ask an F1 question: ")

    parsed_question = parse_f1_question(question)
    analysis_route = route_analysis_request(parsed_question)

    print("\nParsed question:")
    print(parsed_question.model_dump_json(indent=2))

    print("\nAnalysis route:")
    print(analysis_route.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
