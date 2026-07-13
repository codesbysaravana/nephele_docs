"""Prompt template for coding-question generation via LLM.

The returned prompt instructs the model to produce a single coding
question as strict JSON that conforms to the ``CodingQuestion`` schema.
"""

from typing import List


def get_coding_question_prompt(
    topic: str,
    difficulty: str,
    candidate_skills: List[str],
) -> str:
    """Build a system prompt for generating one coding question.

    Parameters
    ----------
    topic:
        The data-structure / algorithm topic (e.g. ``"Arrays"``).
    difficulty:
        One of ``"Easy"``, ``"Medium"``, ``"Hard"``.
    candidate_skills:
        A list of skills the candidate listed on their profile.
        The LLM should try to make the question relevant to these
        skills where possible.

    Returns
    -------
    str
        A fully-formed system prompt string.
    """

    skills_section = ", ".join(candidate_skills) if candidate_skills else "general programming"

    return (
        "You are an expert technical interviewer at a top-tier software company.\n"
        "Generate exactly ONE coding interview question.\n\n"
        "REQUIREMENTS:\n"
        f"- Topic: {topic}\n"
        f"- Difficulty: {difficulty}\n"
        f"- The candidate has experience with: {skills_section}. "
        "Try to make the question relevant to their skill set when possible, "
        "but the topic and difficulty MUST match the values above.\n"
        "- The question must be original and self-contained.\n"
        "- Include clear sample input/output.\n"
        "- Include realistic constraints (input size, value ranges).\n"
        "- Provide 1-3 progressive hints.\n\n"
        "OUTPUT FORMAT — respond with a SINGLE JSON object and nothing else:\n"
        "{\n"
        '  "title": "<concise problem title>",\n'
        f'  "difficulty": "{difficulty}",\n'
        f'  "topic": "{topic}",\n'
        '  "target_complexity": "<e.g. O(N) time, O(1) space>",\n'
        '  "description": "<full problem statement>",\n'
        '  "examples": [\n'
        '    {\n'
        '      "input": "<example input>",\n'
        '      "output": "<expected output>",\n'
        '      "explanation": "<optional explanation>"\n'
        '    }\n'
        '  ],\n'
        '  "constraints": ["<constraint 1>", "<constraint 2>"],\n'
        '  "hints": ["<hint 1>", "<hint 2>", "<hint 3>"]\n'
        "}\n\n"
        "Do NOT include any text outside the JSON object.  "
        "Do NOT wrap the JSON in markdown code fences."
    )
