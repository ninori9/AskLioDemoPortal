from __future__ import annotations
import io
import logging
import re
import unicodedata
from dataclasses import dataclass
from typing import List, Optional

import fitz
import pypdfium2 as pdfium
import pdfplumber

logger = logging.getLogger(__name__)
_MIN_USEFUL_CHARS = 200


@dataclass
class PdfTextResult:
    success: bool
    text: Optional[str]
    method: Optional[str]


def _clean_text(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\r", "\n")
    s = re.sub(r"[\u200B-\u200D\uFEFF]", "", s)
    s = "".join(ch for ch in s if (ch == "\n" or ch == "\t" or ch >= " "))
    # de-hyphenate line-end hyphens
    s = re.sub(r"(\w)-\n(\w)", r"\1\2", s)
    # collapse excessive whitespace
    s = re.sub(r"[ \t]+", " ", s)
    # collapse blank lines to max one
    lines = [ln.strip() for ln in s.split("\n")]
    out, blank = [], False
    for ln in lines:
        if ln == "":
            if not blank:
                out.append("")
            blank = True
        else:
            out.append(ln)
            blank = False
    return "\n".join(out).strip()


def _with_pymupdf(data: bytes) -> str:
    doc = fitz.open(stream=data, filetype="pdf")
    blocks_text: List[str] = []
    try:
        for page in doc:
            # get blocks: (x0, y0, x1, y1, text, block_no, block_type)
            blocks = page.get_text("blocks")
            # sort top-to-bottom, then left-to-right
            blocks.sort(key=lambda b: (round(b[1], 1), round(b[0], 1)))
            for _, _, _, _, text, *_ in blocks:
                if not text:
                    continue
                # reflow inside block: join lines, keep single spaces
                lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
                para = re.sub(r"\s{2,}", " ", " ".join(lines)).strip()
                if para:
                    blocks_text.append(para)
            blocks_text.append("")  # blank line between pages
    finally:
        doc.close()
    return _clean_text("\n".join(blocks_text))

def _with_pdfium(data: bytes) -> str:
    doc = pdfium.PdfDocument(io.BytesIO(data))
    try:
        chunks: List[str] = []
        for i in range(len(doc)):
            page = doc[i]
            try:
                tpage = page.get_textpage()
                try:
                    chunks.append(tpage.get_text_range() or "")
                finally:
                    try: tpage.close()
                    except AttributeError: pass
            finally:
                try: page.close()
                except AttributeError: pass
        return _clean_text("\n".join(chunks))
    finally:
        try: doc.close()
        except AttributeError: pass


def _with_pdfplumber(data: bytes) -> str:
    parts: List[str] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for p in pdf.pages:
            parts.append(p.extract_text() or "")
    return _clean_text("\n".join(parts))


def extract_text_from_pdf(data: bytes) -> PdfTextResult:
    """
    Layout-friendly local extraction. No OCR here.
    Order: PyMuPDF (best paragraphs) → pdfplumber (tables-aware) → pdfium (fast).
    """
    if not data:
        return PdfTextResult(False, None, None)

    try:
        txt = _with_pymupdf(data)
        if len(txt) >= _MIN_USEFUL_CHARS:
            return PdfTextResult(True, txt, "pymupdf")
    except Exception:
        logger.exception("pymupdf failed")

    try:
        txt = _with_pdfplumber(data)
        if len(txt) >= _MIN_USEFUL_CHARS:
            return PdfTextResult(True, txt, "pdfplumber")
    except Exception:
        logger.exception("pdfplumber failed")

    try:
        txt = _with_pdfium(data)
        if len(txt) >= _MIN_USEFUL_CHARS:
            return PdfTextResult(True, txt, "pypdfium2")
    except Exception:
        logger.exception("pypdfium2 failed")

    return PdfTextResult(False, None, None)