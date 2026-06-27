"""Prompt template for LLM-based resume data extraction."""

import textwrap


def get_resume_extraction_prompt(raw_text: str) -> str:
    """Return a system+user prompt instructing the LLM to extract structured
    JSON from raw resume text.

    The JSON schema matches the ``ResumeData`` Pydantic model exactly so the
    response can be validated directly.

    Args:
        raw_text: Plain-text content extracted from a PDF or DOCX resume.

    Returns:
        A fully-formed prompt string ready to be sent as the user message
        alongside a system message.
    """

    prompt = textwrap.dedent(f"""\
        You are an expert resume parser. Your task is to extract structured
        information from the following resume text and return it as a single
        valid JSON object. Do NOT include any text outside the JSON object.

        The JSON object MUST have exactly the following keys and types:

        {{
            "name": "<string> Full name of the candidate",
            "email": "<string> Email address, or empty string if not found",
            "phone": "<string> Phone number, or empty string if not found",
            "skills": ["<string>", ...],
            "technologies": ["<string>", ...],
            "projects": [
                {{
                    "title": "<string> Project title",
                    "description": "<string> Brief description of the project",
                    "technologies": ["<string>", ...]
                }}
            ],
            "experience": [
                {{
                    "role": "<string> Job title / role",
                    "company": "<string> Company or organization name",
                    "duration": "<string> Duration, e.g. '2 years', 'Jan 2020 - Mar 2022', '6 months'",
                    "description": "<string> Brief description of responsibilities"
                }}
            ],
            "education": [
                {{
                    "degree": "<string> Degree name, e.g. 'B.Tech', 'M.Sc.'",
                    "field_of_study": "<string> Major / field",
                    "institution": "<string> University or college name",
                    "year": "<string> Graduation year or date range"
                }}
            ],
            "certifications": ["<string>", ...],
            "domains": ["<string> Domain areas the candidate has worked in, e.g. 'Web Development', 'Machine Learning'", ...]
        }}

        Rules:
        1. If a field is not present in the resume, use an empty string "" for
           string fields or an empty list [] for list fields.
        2. Extract ALL skills, technologies, projects, and experience entries
           you can find.
        3. For "technologies", include programming languages, frameworks,
           libraries, databases, cloud platforms, and tools.
        4. For "domains", infer the high-level domains from the resume content
           (e.g., "Web Development", "Data Science", "DevOps", "Mobile Development").
        5. Return ONLY the JSON object. No markdown fences, no explanation.

        --- RESUME TEXT START ---
        {raw_text}
        --- RESUME TEXT END ---
    """)
    return prompt
