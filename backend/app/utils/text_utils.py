"""
text_utils.py — Stateless text preprocessing helpers.

These implement the four preprocessing steps defined in the implementation
plan (Section 2 — Preprocessing Steps inside document_processor.py).
They are pure functions with no I/O, making them trivially unit-testable.

Used by: app/services/document_processor.py (Phase 2)
"""

import re
import unicodedata


# ------------------------------------------------------------------ #
# Constants
# ------------------------------------------------------------------ #

# Minimum character count for a page/section to be considered non-empty
_MIN_PAGE_LENGTH = 30

# Pattern matching runs of 2+ blank lines (paragraph separators)
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")

# Pattern matching runs of 2+ spaces or tabs (collapsed to single space)
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")

# Control characters except common whitespace (\n \r \t)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


# ------------------------------------------------------------------ #
# Step 1 — Encoding cleanup
# ------------------------------------------------------------------ #


def clean_encoding(text: str) -> str:
    """
    Normalise unicode (NFC), strip null bytes and ASCII control characters.

    Handles common artefacts from PDF extraction such as:
    - Null bytes embedded by some PDF libraries
    - Private-use unicode codepoints from symbol fonts
    - Non-printable control characters
    """
    # NFC normalisation merges combining characters (e.g. e + ́ → é)
    text = unicodedata.normalize("NFC", text)

    # Remove null bytes
    text = text.replace("\x00", "")

    # Remove remaining control characters (keep \n \r \t)
    text = _CONTROL_CHAR_RE.sub("", text)

    return text


# ------------------------------------------------------------------ #
# Step 2 — Whitespace normalisation
# ------------------------------------------------------------------ #


def normalize_whitespace(text: str) -> str:
    """
    Collapse consecutive spaces/tabs and reduce triple+ newlines to double.

    Preserves paragraph structure (double newlines) while eliminating
    the ragged whitespace that PDF extractors commonly produce.
    """
    # Collapse horizontal whitespace runs
    text = _MULTI_SPACE_RE.sub(" ", text)

    # Reduce 3+ consecutive newlines to exactly 2 (one blank line)
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)

    # Strip leading/trailing whitespace from every line
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines)

    return text.strip()


# ------------------------------------------------------------------ #
# Step 3 — Empty page / section removal
# ------------------------------------------------------------------ #


def is_empty_page(text: str, min_length: int = _MIN_PAGE_LENGTH) -> bool:
    """
    Return True when a page or section is effectively empty.

    A page is considered empty if its stripped text is shorter than
    min_length characters. This filters out:
    - Blank pages
    - Pages containing only page numbers or headers
    - Sections that extracted as whitespace only
    """
    return len(text.strip()) < min_length


def filter_empty_pages(pages: list[str], min_length: int = _MIN_PAGE_LENGTH) -> list[str]:
    """
    Drop empty pages from a list and return the cleaned list.
    Logs the number of dropped pages so callers can surface this in telemetry.
    """
    return [p for p in pages if not is_empty_page(p, min_length)]


# ------------------------------------------------------------------ #
# Convenience — run all preprocessing steps in order
# ------------------------------------------------------------------ #


def preprocess_text(text: str) -> str:
    """
    Apply the full preprocessing pipeline to a single string:
      1. Encoding cleanup
      2. Whitespace normalisation

    Use filter_empty_pages() separately when operating on a list of pages
    so the caller can log the drop count.
    """
    text = clean_encoding(text)
    text = normalize_whitespace(text)
    return text


# ------------------------------------------------------------------ #
# Security — Context Sanitization
# ------------------------------------------------------------------ #


# Common prompt injection phrases that should not appear in retrieved context
_PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore previous instructions", re.IGNORECASE),
    re.compile(r"forget the system prompt", re.IGNORECASE),
    re.compile(r"you are chatgpt", re.IGNORECASE),
    re.compile(r"system:", re.IGNORECASE),
    re.compile(r"assistant:", re.IGNORECASE),
    re.compile(r"user:", re.IGNORECASE),
]


def sanitize_context_for_prompt(context: str) -> tuple[str, int]:
    """
    Remove common prompt injection phrases from the retrieved context.
    Normalizes whitespace after removal to ensure clean formatting.

    Returns
    -------
    tuple[str, int]
        The sanitized context string and the total number of injection patterns removed.
    """
    original_context = context
    total_removed = 0

    for pattern in _PROMPT_INJECTION_PATTERNS:
        # Find all occurrences to count them
        matches = pattern.findall(context)
        if matches:
            total_removed += len(matches)
            # Remove all matches
            context = pattern.sub("", context)

    if total_removed > 0:
        context = normalize_whitespace(context)

    return context, total_removed
