"""Reverse mapping: de-pseudonymize a report using stored mapping."""

from __future__ import annotations

import re

from pseudopipe.mapping import MappingStore


def deanonymize(text: str, mapping: MappingStore) -> str:
    """Replace pseudonyms with originals in the given text.

    Uses marker-based two-pass approach to prevent replacement collisions:
    - Pass 1: Replace pseudonyms with null-byte-delimited markers
    - Pass 2: Replace markers with original values

    Handles possessives/plurals and monetary/numeric values.
    """
    reverse = mapping.reverse_map
    sorted_pseudonyms = sorted(reverse.keys(), key=len, reverse=True)

    # Pass 1: Replace pseudonyms with markers
    markers: dict[str, str] = {}
    for i, pseudonym in enumerate(sorted_pseudonyms):
        original = reverse[pseudonym]
        marker = f"\x00DAN_{i}\x00"
        markers[marker] = original

        if pseudonym and pseudonym[0] in "$0123456789":
            # Numeric boundaries: don't match inside a longer number
            # e.g. pseudonym "47.2" must not match inside "47.20"
            pattern = re.compile(
                r"(?<!\d)" + re.escape(pseudonym) + r"(?!\d)",
                re.IGNORECASE,
            )
            text = pattern.sub(marker, text)
        else:
            pattern = re.compile(
                r"\b" + re.escape(pseudonym) + r"(?:'s|s)?\b",
                re.IGNORECASE,
            )

            def _mark(match: re.Match, _marker=marker, _pseudo=pseudonym) -> str:
                suffix = match.group(0)[len(_pseudo):]
                return _marker + suffix

            text = pattern.sub(_mark, text)

    # Pass 2: Replace markers with originals
    for marker, original in markers.items():
        text = text.replace(marker, original)

    return text
