

"""
Minimal PDF reader using pdfplumber.
Provides read_pdf(path) → extracted text.
"""

import pdfplumber


def read_pdf(path: str) -> str:
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            text_parts.append(txt)
    return "\n".join(text_parts)