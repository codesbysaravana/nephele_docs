"""Prompt template for evaluating a candidate's coding-round explanation.

The returned prompt instructs the model to score the candidate on five
dimensions and produce strict JSON conforming to ``CodingEvaluation``.
"""

from app.models.coding_models import CodingQuestion


def get_coding_evaluation_prompt(
    question: CodingQuestion,
    candidate_explanation: str,
) -> str:
    """Build a system prompt for evaluating a candidate's verbal answer.

    Parameters
    ----------
    question:
        The ``CodingQuestion`` that was posed to the candidate.
    candidate_explanation:
        The candidate's spoken / typed explanation of their approach.

    Returns
    -------
    str
        A fully-formed system prompt string.
    """

    return (
        "You are an expert technical interviewer evaluating a candidate's "
        "verbal explanation of their solution approach to a coding problem.\n\n"
        "=== PROBLEM ===\n"
        f"Title: {question.title}\n"
        f"Difficulty: {question.difficulty.value}\n"
        f"Topic: {question.topic.value}\n"
        f"Description:\n{question.description}\n"
        f"Sample Input: {question.sample_input}\n"
        f"Sample Output: {question.sample_output}\n"
        f"Constraints: {question.constraints}\n\n"
        "=== CANDIDATE'S EXPLANATION ===\n"
        f"{candidate_explanation}\n\n"
        "=== EVALUATION CRITERIA ===\n"
        "Score each dimension from 0.0 to 10.0 (one decimal place):\n"
        "1. **understanding** — Did the candidate correctly understand the "
        "problem statement, edge cases, and constraints?\n"
        "2. **logic** — Is the proposed algorithmic approach correct? Would it "
        "produce the right answer for all valid inputs?\n"
        "3. **time_complexity** — Did the candidate discuss time complexity? "
        "Is their analysis accurate?\n"
        "4. **space_complexity** — Did the candidate discuss space complexity? "
        "Is their analysis accurate?\n"
        "5. **communication** — How clearly and coherently did the candidate "
        "explain their thought process?\n"
        "6. **overall** — A holistic score reflecting all the above.\n"
        "7. **feedback** — Constructive free-text feedback (2-4 sentences).\n\n"
        "OUTPUT FORMAT — respond with a SINGLE JSON object and nothing else:\n"
        "{\n"
        '  "understanding": <float>,\n'
        '  "logic": <float>,\n'
        '  "time_complexity": <float>,\n'
        '  "space_complexity": <float>,\n'
        '  "communication": <float>,\n'
        '  "overall": <float>,\n'
        '  "feedback": "<string>"\n'
        "}\n\n"
        "Do NOT include any text outside the JSON object.  "
        "Do NOT wrap the JSON in markdown code fences."
    )
