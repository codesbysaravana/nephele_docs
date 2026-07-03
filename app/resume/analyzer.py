"""Top-level resume analysis orchestrator.

Chains together file parsing → LLM extraction → profile building and also
provides LLM-powered interview question generation.
"""

import json
import logging
from typing import List

import groq

from app.config import GROQ_API_KEY
from app.models.candidate_profile import CandidateProfile, ResumeData
from app.prompts.resume_questions import get_resume_questions_prompt
from app.resume.extractor import ResumeExtractor
from app.resume.parser import extract_resume_text
from app.resume.profile_builder import ProfileBuilder

logger = logging.getLogger(__name__)

_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


class ResumeAnalyzer:
    """Orchestrates the full resume analysis pipeline.

    Usage::

        analyzer = ResumeAnalyzer()
        profile = await analyzer.analyze("path/to/resume.pdf")
        questions = await analyzer.generate_questions(profile)
    """

    def __init__(self) -> None:
        self._extractor = ResumeExtractor()
        self._profile_builder = ProfileBuilder()
        self._groq_client = groq.AsyncGroq(api_key=GROQ_API_KEY or "missing_api_key")
        logger.info("ResumeAnalyzer initialised")

    async def analyze(self, file_path: str) -> CandidateProfile:
        """Run the full pipeline: parse → extract → build profile.

        Args:
            file_path: Path to a ``.pdf`` or ``.docx`` resume file.

        Returns:
            A fully populated ``CandidateProfile``.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is unsupported.
            RuntimeError: If text extraction fails.
        """

        logger.info("Starting resume analysis for: %s", file_path)

        # Step 1 — Extract raw text from the file
        raw_text = extract_resume_text(file_path)
        if not raw_text.strip():
            logger.warning("Extracted text is empty for file: %s", file_path)
            return CandidateProfile(resume_data=ResumeData())

        # Step 2 — Send raw text to the LLM for structured extraction
        resume_data = await self._extractor.extract(raw_text)

        # Step 3 — Build the candidate profile heuristically
        profile = self._profile_builder.build(resume_data)

        logger.info(
            "Resume analysis complete — candidate=%s, level=%s",
            profile.resume_data.name or "<unknown>",
            profile.candidate_level.value,
        )
        return profile

    async def generate_questions(
        self, profile: CandidateProfile
    ) -> List[str]:
        """Generate 10 personalized interview questions for the candidate.

        Args:
            profile: A ``CandidateProfile`` built from the candidate's resume.

        Returns:
            A list of exactly 10 interview question strings. Falls back to
            generic questions if the LLM call fails.
        """

        prompt = get_resume_questions_prompt(profile)
        logger.info("Generating interview questions for: %s", profile.resume_data.name or "<unknown>")

        try:
            chat_completion = await self._groq_client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a senior technical interviewer. Respond "
                            "with a JSON object containing exactly 10 "
                            "interview questions. No extra text."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=4096,
            )

            raw_json = chat_completion.choices[0].message.content
            if not raw_json:
                logger.error("LLM returned empty response for question generation.")
                return self._fallback_questions(profile)

            parsed = json.loads(raw_json)

            # Accept "questions" key or fall back to first list value
            questions: List[str] = []
            if isinstance(parsed, dict):
                if "questions" in parsed and isinstance(parsed["questions"], list):
                    questions = [str(q) for q in parsed["questions"]]
                else:
                    # Try to find the first list value in the dict
                    for value in parsed.values():
                        if isinstance(value, list):
                            questions = [str(q) for q in value]
                            break
            elif isinstance(parsed, list):
                questions = [str(q) for q in parsed]

            if not questions:
                logger.warning("LLM response parsed but no questions found.")
                return self._fallback_questions(profile)

            # Ensure exactly 10
            questions = questions[:10]
            while len(questions) < 10:
                questions.append(
                    f"Can you tell us more about your experience with "
                    f"{profile.resume_data.skills[len(questions) % max(len(profile.resume_data.skills), 1)]}?"
                    if profile.resume_data.skills
                    else "Can you walk us through a challenging project you've worked on?"
                )

            logger.info("Successfully generated %d interview questions", len(questions))
            return questions

        except json.JSONDecodeError as exc:
            logger.exception("Failed to parse question-generation response: %s", exc)
            return self._fallback_questions(profile)

        except groq.APIError as exc:
            logger.exception("Groq API error during question generation: %s", exc)
            return self._fallback_questions(profile)

        except Exception as exc:
            logger.exception("Unexpected error during question generation: %s", exc)
            return self._fallback_questions(profile)

    @staticmethod
    def _fallback_questions(profile: CandidateProfile) -> List[str]:
        """Generate generic fallback questions when the LLM is unavailable.

        Args:
            profile: The candidate profile to personalise questions minimally.

        Returns:
            A list of 10 generic but reasonable interview questions.
        """

        name = profile.resume_data.name or "the candidate"
        skills = profile.resume_data.skills[:3] if profile.resume_data.skills else ["your primary technology"]

        return [
            f"Can you introduce yourself and summarise your technical background?",
            f"What motivated you to pursue a career in software development?",
            f"Tell us about your experience with {skills[0]}.",
            f"Describe a challenging technical problem you solved recently.",
            f"How do you approach learning a new technology or framework?",
            f"Can you walk us through the architecture of one of your projects?",
            f"How do you handle code reviews and feedback from peers?",
            f"Describe a situation where you had to debug a difficult production issue.",
            f"What is your experience with version control and collaborative development?",
            f"Where do you see your career heading in the next 2-3 years?",
        ]
