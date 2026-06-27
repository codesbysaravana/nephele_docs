"""Prompt template for generating personalized interview questions from a
candidate profile."""

import textwrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.candidate_profile import CandidateProfile


def get_resume_questions_prompt(profile: "CandidateProfile") -> str:
    """Return a prompt instructing the LLM to generate exactly 10 personalised
    interview questions based on the candidate's resume data.

    Questions reference the candidate's specific projects, skills, and
    technologies so the interview feels tailored rather than generic.

    Args:
        profile: A fully-built ``CandidateProfile`` instance.

    Returns:
        A prompt string ready to be sent as the user message.
    """

    rd = profile.resume_data

    # Build readable summaries for the prompt context
    skills_text = ", ".join(rd.skills) if rd.skills else "None listed"
    tech_text = ", ".join(rd.technologies) if rd.technologies else "None listed"
    domains_text = ", ".join(profile.primary_domains) if profile.primary_domains else "General"
    strengths_text = ", ".join(profile.strength_areas) if profile.strength_areas else "Not determined"

    projects_lines: list[str] = []
    for idx, proj in enumerate(rd.projects, start=1):
        techs = ", ".join(proj.technologies) if proj.technologies else "N/A"
        projects_lines.append(
            f"  {idx}. {proj.title or 'Untitled'} — {proj.description or 'No description'} "
            f"(Technologies: {techs})"
        )
    projects_text = "\n".join(projects_lines) if projects_lines else "  None listed"

    experience_lines: list[str] = []
    for idx, exp in enumerate(rd.experience, start=1):
        experience_lines.append(
            f"  {idx}. {exp.role or 'Unknown Role'} at {exp.company or 'Unknown Company'} "
            f"({exp.duration or 'Unknown duration'}) — {exp.description or 'No description'}"
        )
    experience_text = "\n".join(experience_lines) if experience_lines else "  None listed"

    education_lines: list[str] = []
    for idx, edu in enumerate(rd.education, start=1):
        education_lines.append(
            f"  {idx}. {edu.degree or 'N/A'} in {edu.field_of_study or 'N/A'} "
            f"from {edu.institution or 'N/A'} ({edu.year or 'N/A'})"
        )
    education_text = "\n".join(education_lines) if education_lines else "  None listed"

    certs_text = ", ".join(rd.certifications) if rd.certifications else "None listed"

    prompt = textwrap.dedent(f"""\
        You are a senior technical interviewer. Based on the candidate profile
        below, generate exactly 10 personalized interview questions.

        CANDIDATE PROFILE:
        - Name: {rd.name or 'Unknown'}
        - Level: {profile.candidate_level.value}
        - Total Experience: {profile.total_experience_years} years
        - Skills: {skills_text}
        - Technologies: {tech_text}
        - Domains: {domains_text}
        - Strengths: {strengths_text}
        - Certifications: {certs_text}

        PROJECTS:
        {projects_text}

        EXPERIENCE:
        {experience_text}

        EDUCATION:
        {education_text}

        INSTRUCTIONS:
        1. Generate exactly 10 questions. No more, no fewer.
        2. At least 3 questions MUST reference specific projects listed above
           by name and ask about design decisions, challenges, or
           implementation details.
        3. At least 2 questions MUST reference specific technologies or skills
           from the profile.
        4. Calibrate difficulty to the candidate's level ({profile.candidate_level.value}).
        5. Include a mix of:
           - Technical depth questions (architecture, algorithms, trade-offs)
           - Behavioural / situational questions tied to their experience
           - Problem-solving / scenario-based questions in their domain
        6. Return the questions as a JSON object with a single key "questions"
           whose value is an array of exactly 10 strings.
           Example: {{"questions": ["Question 1?", "Question 2?", ...]}}
        7. Return ONLY the JSON object. No markdown fences, no explanation.
    """)
    return prompt
