"""Light text cleaning for text pulled out of PDFs (Member 3)."""
from __future__ import annotations

import re
import unicodedata


def clean_text(raw: str) -> str:
    """Make extracted PDF text easier to chunk and embed.

    - Normalises odd unicode forms (ligatures such as the "fi" glyph).
    - Re-joins words that were split with a hyphen at a line break ("evalu-\\nation").
    - Collapses all runs of whitespace (including line breaks) into single spaces.
    """
    text = unicodedata.normalize("NFKC", raw or "")
    text = text.replace("\x00", " ")
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
