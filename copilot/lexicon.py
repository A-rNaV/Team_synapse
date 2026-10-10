"""Word-level Hinglish and retail synonyms for the keyword rules.

The original message is left unchanged. Rules see a copy with these words
replaced. Phrases are matched on word boundaries, longest first.
"""

from __future__ import annotations

import re

# Longer phrases first so "sabse zyada" is not split into separate words.
_PAIRS = (
    ("sabse zyada", "most"),
    ("pichhle mahine", "last 30 days"),
    ("bina bill", "without receipt"),
    ("khatam", "out of stock"),
    ("kharab", "bad"),
    ("maal", "goods"),
    ("saman", "goods"),
    ("toota", "broken"),
    ("supplier", "vendor"),
    ("kaunsa", "which"),
    ("kal", "yesterday"),
    ("godown", "warehouse"),
    ("dukaan", "store"),
    ("wapas", "return"),
    ("poora", "entire"),
    ("saare", "all"),
    ("bandh", "down"),
)

_PATTERN = re.compile(
    "|".join(r"\b" + re.escape(source) + r"\b" for source, _target in _PAIRS),
    re.IGNORECASE,
)
_TARGET = {source: target for source, target in _PAIRS}


def apply_lexicon(text: str) -> str:
    """Return a copy of text with glossary words replaced. The input is not modified."""

    def _replace(match: re.Match) -> str:
        return _TARGET[match.group(0).lower()]

    return _PATTERN.sub(_replace, text)
