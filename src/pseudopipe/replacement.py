"""Stage 3: REP — Entity replacement with optional fluency rewrite."""

from __future__ import annotations

import logging
import re

from pseudopipe import config
from pseudopipe.mapping import MappingStore

logger = logging.getLogger(__name__)


def _direct_replace(text: str, mapping: MappingStore) -> str:
    """Direct string replacement using marker-based two-pass approach.

    Pass 1 replaces originals with null-byte-delimited markers so that
    already-inserted pseudonyms cannot be matched by later replacements.
    Pass 2 swaps markers for final pseudonyms.
    """
    forward = mapping.forward_map
    sorted_originals = sorted(forward.keys(), key=len, reverse=True)

    # Pass 1: Replace originals with unique markers
    markers: dict[str, str] = {}
    for i, original in enumerate(sorted_originals):
        marker = f"\x00PSE_{i}\x00"
        markers[marker] = forward[original]
        text = re.compile(re.escape(original)).sub(marker, text)

    # Pass 2: Replace markers with pseudonyms
    for marker, pseudonym in markers.items():
        text = text.replace(marker, pseudonym)

    return text


def _rewrite_for_fluency(sentence: str) -> str:
    """Use Qwen to lightly rewrite a sentence for natural fluency."""
    try:
        import ollama

        prompt = (
            "Rewrite this sentence to sound natural, keeping all names and numbers "
            "exactly as they are. Return ONLY the rewritten sentence, nothing else.\n\n"
            f"Sentence: {sentence}"
        )
        response = ollama.chat(
            model=config.OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3},
        )
        result = response["message"]["content"].strip()
        # Sanity check: result shouldn't be dramatically different in length
        if 0.5 < len(result) / max(len(sentence), 1) < 2.0:
            return result
        return sentence
    except Exception as e:
        logger.warning("Fluency rewrite failed: %s", e)
        return sentence


def replace_entities(
    text: str,
    mapping: MappingStore,
    rewrite_fluency: bool = True,
) -> str:
    """Replace entities in text using mapping, with optional fluency rewrite.

    Hybrid approach (per Hou et al.):
    1. Direct replacement (longest-first)
    2. Optional per-sentence fluency rewrite via Qwen
    """
    # Step 1: Direct replacement
    replaced = _direct_replace(text, mapping)

    if not rewrite_fluency:
        return replaced

    # Step 2: Per-sentence fluency rewrite for sentences containing replacements
    pseudonyms = set(mapping.forward_map.values())
    sentences = re.split(r"(?<=[.!?])\s+", replaced)
    rewritten = []

    for sentence in sentences:
        # Only rewrite sentences that contain pseudonyms
        contains_replacement = any(p in sentence for p in pseudonyms)
        if contains_replacement and len(sentence) > 20:
            rewritten.append(_rewrite_for_fluency(sentence))
        else:
            rewritten.append(sentence)

    return " ".join(rewritten)
