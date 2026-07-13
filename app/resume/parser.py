"""Resume file parser — extracts plain text from PDF and DOCX files."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_resume_text(file_path: str) -> str:
    """Extract all text content from a resume file.

    Supports:
        - PDF files (via ``pymupdf`` / ``fitz``)
        - DOCX files (via ``python-docx``)

    Args:
        file_path: Absolute or relative path to the resume file.

    Returns:
        The full extracted text as a single string with pages / paragraphs
        joined by newline characters.

    Raises:
        FileNotFoundError: If *file_path* does not exist.
        ValueError: If the file extension is not ``.pdf`` or ``.docx``.
        RuntimeError: If text extraction fails for any other reason.
    """

    path = Path(file_path)

    if not path.exists():
        logger.error("Resume file not found: %s", file_path)
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    extension = path.suffix.lower()
    logger.info("Parsing resume file '%s' (detected type: %s)", path.name, extension)

    if extension == ".pdf":
        return _extract_from_pdf(path)
    elif extension == ".docx":
        return _extract_from_docx(path)
    else:
        logger.error("Unsupported resume format: %s", extension)
        raise ValueError(
            f"Unsupported resume file format '{extension}'. "
            "Only .pdf and .docx files are supported."
        )


def _extract_from_pdf(path: Path) -> str:
    """Extract text from a PDF file using PyMuPDF (fitz).

    Args:
        path: ``Path`` object pointing to the PDF.

    Returns:
        Concatenated text of all pages separated by newlines.

    Raises:
        RuntimeError: If PyMuPDF fails to open or read the file.
    """

    try:
        import fitz  # pymupdf
    except ImportError as exc:
        logger.error("pymupdf (fitz) is not installed.")
        raise RuntimeError(
            "pymupdf is required for PDF parsing. "
            "Install it with: pip install pymupdf"
        ) from exc

    try:
        pages_text: list[str] = []
        with fitz.open(str(path)) as doc:
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text")
                if text:
                    pages_text.append(text.strip())
                    logger.debug(
                        "Page %d: extracted %d characters", page_num, len(text)
                    )

        full_text = "\n\n".join(pages_text)
        logger.info(
            "PDF extraction complete — %d page(s), %d total characters",
            len(pages_text),
            len(full_text),
        )
        return full_text

    except Exception as exc:
        logger.exception("Failed to extract text from PDF: %s", path)
        raise RuntimeError(f"PDF extraction failed for {path}: {exc}") from exc


def _extract_from_docx(path: Path) -> str:
    """Extract text from a DOCX file using python-docx.

    Args:
        path: ``Path`` object pointing to the DOCX file.

    Returns:
        Concatenated paragraph text separated by newlines.

    Raises:
        RuntimeError: If python-docx fails to open or read the file.
    """

    try:
        import docx  # python-docx
    except ImportError as exc:
        logger.error("python-docx is not installed.")
        raise RuntimeError(
            "python-docx is required for DOCX parsing. "
            "Install it with: pip install python-docx"
        ) from exc

    try:
        document = docx.Document(str(path))
        paragraphs: list[str] = []
        for para in document.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)

        full_text = "\n".join(paragraphs)
        logger.info(
            "DOCX extraction complete — %d paragraph(s), %d total characters",
            len(paragraphs),
            len(full_text),
        )
        return full_text

    except Exception as exc:
        logger.exception("Failed to extract text from DOCX: %s", path)
        raise RuntimeError(f"DOCX extraction failed for {path}: {exc}") from exc
