from typing import TypedDict, List, Dict
import dspy


class GraphState(TypedDict):
    question: str
    generation: str
    search: str
    documents: List[str]
    steps: List[str]

class ExtractInfo(dspy.Signature):
    """Extract structured information from text."""

    text: str = dspy.InputField()
    title: str = dspy.OutputField()
    query: str = dspy.OutputField()
    headings: list[str] = dspy.OutputField()
    extract_content: str = dspy.OutputField(desc="Extract the information that will answer the query")

class DecomposeQuestion(dspy.Signature):
    """Extract structured information from text."""

    question: str = dspy.InputField()
    sub_questions: list[str, str] = dspy.OutputField(desc="Decompose the quetion into sub questions. Don't generate more than 3 sub questions.")
