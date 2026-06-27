"""LLM-based resume data extractor using Groq API with structured JSON output."""

import json
import logging
from typing import Any, Dict

import groq

from app.config import GROQ_API_KEY
from app.models.candidate_profile import ResumeData
from app.prompts.resume_analysis import get_resume_extraction_prompt

logger = logging.getLogger(__name__)

_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


class ResumeExtractor:
    """Extracts structured ``ResumeData`` from raw resume text via the Groq LLM
    API.

    Uses JSON-mode (``response_format={"type": "json_object"}``) to guarantee
    that the model returns valid JSON, which is then validated against the
    ``ResumeData`` Pydantic model.
    """

    def __init__(self) -> None:
        if not GROQ_API_KEY:
            logger.warning(
                "GROQ_API_KEY is not set — LLM calls will fail at runtime."
            )
        self._client = groq.AsyncGroq(api_key=GROQ_API_KEY)
        logger.info("ResumeExtractor initialised (model=%s)", _MODEL)

    async def extract(self, raw_text: str) -> ResumeData:
        """Send raw resume text to the LLM and return validated ``ResumeData``.

        Args:
            raw_text: Plain-text content extracted from a resume file.

        Returns:
            A validated ``ResumeData`` instance. If the LLM call or
            validation fails, a best-effort ``ResumeData`` with defaults is
            returned so the pipeline never crashes outright.
        """

        prompt = get_resume_extraction_prompt(raw_text)
        logger.info("Sending resume text (%d chars) to Groq for extraction", len(raw_text))

        try:
            chat_completion = await self._client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise resume parser. Always respond "
                            "with a single valid JSON object matching the "
                            "requested schema. No extra text."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=4096,
            )

            raw_json = chat_completion.choices[0].message.content
            logger.debug("Raw LLM response (first 500 chars): %s", raw_json[:500] if raw_json else "<empty>")

            if not raw_json:
                logger.error("LLM returned an empty response.")
                return ResumeData()

            parsed: Dict[str, Any] = json.loads(raw_json)
            resume_data = ResumeData.model_validate(parsed)
            logger.info(
                "Resume extraction successful — name=%s, skills=%d, projects=%d",
                resume_data.name,
                len(resume_data.skills),
                len(resume_data.projects),
            )
            return resume_data

        except json.JSONDecodeError as exc:
            logger.exception("Failed to parse LLM response as JSON: %s", exc)
            return ResumeData()

        except groq.APIError as exc:
            logger.exception("Groq API error during resume extraction: %s", exc)
            return ResumeData()

        except Exception as exc:
            logger.exception("Unexpected error during resume extraction: %s", exc)
            return ResumeData()
