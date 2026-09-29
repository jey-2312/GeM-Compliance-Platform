"""Page-aware PDF/text extraction for the prototype.

Digital text extraction uses PyMuPDF first. OCR remains an explicit fallback
stub because the prototype's critical path is designed around digital PDFs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MIN_USEFUL_CHARS_PER_PAGE = 40


@dataclass(frozen=True)
class PageText:
    """Text extracted from one 1-indexed document page."""

    page: int
    text: str


def extract_pages_from_pdf(path: str | Path) -> list[PageText]:
    """Extract page-aware text from a PDF with PyMuPDF.

    If no page contains a useful amount of digital text, the explicit OCR
    fallback is invoked. The returned pages always preserve 1-indexed page
    numbers so downstream AI extraction can attach source_page/page evidence.
    """

    import fitz  # PyMuPDF

    pdf_path = str(path)
    doc = fitz.open(pdf_path)
    pages: list[PageText] = []
    useful_pages = 0

    try:
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            pages.append(PageText(page=page_number, text=text))
            if len(text.strip()) >= MIN_USEFUL_CHARS_PER_PAGE:
                useful_pages += 1
    finally:
        doc.close()

    if useful_pages == 0:
        return _ocr_fallback(pdf_path)

    return pages


def format_pages_for_llm(pages: list[PageText]) -> str:
    """Render page boundaries explicitly for the extraction prompt."""

    return "\n\n".join(
        f"===== PAGE {page.page} =====\n{page.text.strip()}".rstrip()
        for page in pages
    )


def extract_text_from_pdf(path: str | Path) -> str:
    """Backward-compatible helper returning page-aware text."""

    return format_pages_for_llm(extract_pages_from_pdf(path))


def pages_from_text(text: str) -> list[PageText]:
    """Treat a synthetic/plain-text source as one explicit page."""

    return [PageText(page=1, text=text)]


def extract_text_from_string(tender_text: str) -> str:
    """Pass-through helper retained for text fixtures."""

    return tender_text


def _ocr_fallback(path: str) -> list[PageText]:
    """Fail explicitly when the optional OCR path is reached."""

    raise NotImplementedError(
        "OCR fallback not implemented for the prototype. Use a digital-text "
        f"PDF for the demo: {path}"
    )
