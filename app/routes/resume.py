"""FastAPI routes for resume upload, analysis, and question generation."""

import logging
import os
import tempfile
import uuid
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.models.candidate_profile import CandidateProfile
from app.resume.analyzer import ResumeAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Resume"])

# Shared analyzer instance — created once, reused across requests.
_analyzer = ResumeAnalyzer()

# Allowed MIME types and extensions
_ALLOWED_EXTENSIONS = {".pdf", ".docx"}
_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post(
    "/upload",
    response_model=CandidateProfile,
    summary="Upload and analyse a resume",
    description=(
        "Accepts a PDF or DOCX resume file, extracts structured data via LLM, "
        "builds a candidate profile with level classification and interview "
        "focus recommendations."
    ),
)
async def upload_resume(file: UploadFile = File(...)) -> CandidateProfile:
    """Upload a resume file and receive a full ``CandidateProfile``.

    The file is saved to a temporary location, processed through the
    analysis pipeline, and then cleaned up.

    Args:
        file: The uploaded resume file (PDF or DOCX).

    Returns:
        A ``CandidateProfile`` JSON response.

    Raises:
        HTTPException 400: If the file type is unsupported or the file is empty.
        HTTPException 413: If the file exceeds the size limit.
        HTTPException 500: If processing fails unexpectedly.
    """

    # Validate filename and extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided.",
        )

    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()

    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file type '{ext}'. "
                f"Allowed types: {', '.join(sorted(_ALLOWED_EXTENSIONS))}"
            ),
        )

    # Read file content
    try:
        content = await file.read()
    except Exception as exc:
        logger.exception("Failed to read uploaded file: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read the uploaded file.",
        )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(content) > _MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File too large ({len(content)} bytes). "
                f"Maximum allowed size is {_MAX_FILE_SIZE_BYTES} bytes."
            ),
        )

    # Save to a temporary file
    tmp_path: str | None = None
    try:
        suffix = ext
        unique_name = f"resume_{uuid.uuid4().hex}{suffix}"
        tmp_dir = tempfile.gettempdir()
        tmp_path = os.path.join(tmp_dir, unique_name)

        with open(tmp_path, "wb") as tmp_file:
            tmp_file.write(content)

        logger.info(
            "Saved uploaded resume to temp file: %s (%d bytes)",
            tmp_path,
            len(content),
        )

        # Run the full analysis pipeline
        profile = await _analyzer.analyze(tmp_path)
        return profile

    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        logger.exception("Resume analysis failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Resume analysis failed: {exc}",
        )

    except Exception as exc:
        logger.exception("Unexpected error during resume analysis: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the resume.",
        )

    finally:
        # Clean up the temporary file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                logger.debug("Cleaned up temp file: %s", tmp_path)
            except OSError:
                logger.warning("Failed to clean up temp file: %s", tmp_path)


@router.post(
    "/questions",
    response_model=List[str],
    summary="Generate personalised interview questions",
    description=(
        "Accepts a CandidateProfile JSON body and returns exactly 10 "
        "personalized interview questions calibrated to the candidate's "
        "level, skills, and project experience."
    ),
)
async def generate_questions(profile: CandidateProfile) -> List[str]:
    """Generate 10 personalised interview questions from a ``CandidateProfile``.

    Args:
        profile: A ``CandidateProfile`` (typically obtained from
            ``POST /resume/upload``).

    Returns:
        A JSON array of 10 interview question strings.

    Raises:
        HTTPException 500: If question generation fails unexpectedly.
    """

    try:
        questions = await _analyzer.generate_questions(profile)
        logger.info(
            "Generated %d questions for candidate: %s",
            len(questions),
            profile.resume_data.name or "<unknown>",
        )
        return questions

    except Exception as exc:
        logger.exception("Question generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate interview questions.",
        )
