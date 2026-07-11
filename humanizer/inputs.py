"""Read source text from raw strings, text files, or PDFs.

PDFs extract with messy line breaks, hyphenation, and page furniture, so we
run a cleanup pass to hand the model (or the rule engine) tidy prose.
"""

from __future__ import annotations

import re
from pathlib import Path


def _dehyphenate(text: str) -> str:
    """Join words that a PDF split across a line break with a hyphen."""
    return re.sub(r"(\w)-\n(\w)", r"\1\2", text)


def _normalize_whitespace(text: str) -> str:
    """Collapse PDF line noise into normal paragraphs.

    Single newlines inside a paragraph become spaces; blank lines stay as
    paragraph breaks. Runs of spaces collapse to one.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _dehyphenate(text)
    # Protect paragraph breaks, then flatten remaining single newlines.
    text = re.sub(r"\n[ \t]*\n+", "\u0000", text)
    text = re.sub(r"[ \t]*\n[ \t]*", " ", text)
    text = text.replace("\u0000", "\n\n")
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def clean_extracted_text(text: str) -> str:
    """Public cleanup entry point for extracted or pasted-from-PDF text."""
    return _normalize_whitespace(text)


def read_pdf(path: str | Path) -> str:
    """Extract and clean text from a PDF file."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "Reading PDFs needs the 'pypdf' package. Install it with "
            "'pip install pypdf'."
        ) from exc

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    raw = "\n\n".join(pages)
    cleaned = clean_extracted_text(raw)
    if not cleaned:
        raise ValueError(
            f"No extractable text found in {path}. It may be a scanned image "
            "PDF that needs OCR."
        )
    return cleaned


def read_text_file(path: str | Path) -> str:
    """Read a plain-text file and normalize its whitespace."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return clean_extracted_text(path.read_text(encoding="utf-8", errors="replace"))


def resolve_input(
    *, text: str | None, file: str | None, pdf: str | None
) -> str:
    """Return the source text from whichever input was supplied."""
    provided = [name for name, val in
                (("text", text), ("file", file), ("pdf", pdf)) if val]
    if not provided:
        raise ValueError("No input given. Use --text, --file, or --pdf.")
    if len(provided) > 1:
        raise ValueError(
            f"Give only one input at a time (got: {', '.join(provided)})."
        )

    if text:
        return clean_extracted_text(text)
    if pdf:
        return read_pdf(pdf)
    return read_text_file(file)  # type: ignore[arg-type]
