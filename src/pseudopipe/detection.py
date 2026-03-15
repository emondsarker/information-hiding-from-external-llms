"""Stage 1: DET — Privacy Detection (NER + prompt-based)."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

import spacy
from spacy.language import Language
from spacy.tokens import Span

from pseudopipe import config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Entity:
    text: str
    label: str
    start_char: int
    end_char: int


def _build_custom_patterns(nlp: Language) -> Language:
    """Add EntityRuler with financial and custom entity patterns before NER."""
    ruler = nlp.add_pipe("entity_ruler", before="ner")

    patterns = []

    # Financial metric patterns
    for pat in config.FINANCIAL_PATTERNS:
        patterns.append(pat)

    # Custom domain entities (exact phrase match)
    for entity_text, entity_label in config.CUSTOM_ENTITIES.items():
        tokens = entity_text.split()
        pattern = {"label": entity_label, "pattern": [{"LOWER": t.lower()} for t in tokens]}
        patterns.append(pattern)

    ruler.add_patterns(patterns)
    return nlp


def _load_spacy_model() -> Language:
    """Load spaCy model with custom EntityRuler patterns."""
    nlp = spacy.load(config.SPACY_MODEL)
    nlp = _build_custom_patterns(nlp)
    return nlp


_nlp_cache: Language | None = None


def _get_nlp() -> Language:
    global _nlp_cache
    if _nlp_cache is None:
        _nlp_cache = _load_spacy_model()
    return _nlp_cache


def detect_ner(text: str) -> list[Entity]:
    """DET_NER: Detect entities using spaCy NER + EntityRuler."""
    nlp = _get_nlp()
    doc = nlp(text)
    entities = []
    allowed_labels = config.NER_ENTITY_LABELS | set(config.CUSTOM_ENTITIES.values()) | {"FINANCIAL_METRIC"}
    # Common abbreviations that are not real entities
    skip_texts = {"CEO", "CFO", "CTO", "COO", "VP", "SVP", "EVP", "CIO", "CMO"}
    for ent in doc.ents:
        if ent.label_ not in allowed_labels:
            continue
        # Skip common title abbreviations misidentified as ORG
        if ent.text.strip() in skip_texts:
            continue
        # Skip entities containing newlines (likely NER errors spanning lines)
        if "\n" in ent.text:
            continue
        entities.append(Entity(text=ent.text, label=ent.label_, start_char=ent.start_char, end_char=ent.end_char))

    # Detect emails (spaCy NER doesn't find them)
    entities.extend(_detect_emails(text))

    return entities


_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def _detect_emails(text: str) -> list[Entity]:
    """Detect email addresses via regex."""
    entities = []
    for match in _EMAIL_RE.finditer(text):
        entities.append(Entity(
            text=match.group(), label="EMAIL",
            start_char=match.start(), end_char=match.end(),
        ))
    return entities


def detect_prompt(text: str) -> list[Entity]:
    """DET_prompt: Use local Qwen model to detect entities NER might miss."""
    try:
        import ollama
    except ImportError:
        logger.warning("ollama package not available, skipping prompt-based detection")
        return []

    prompt = (
        "Identify all sensitive entities (people, companies, financial figures, "
        "proprietary project names, trade secrets, locations) in the following text. "
        "Return ONLY a JSON array of objects with keys: text, label. "
        "Labels should be one of: PERSON, ORG, MONEY, PERCENT, GPE, LOC, PROJECT, MACHINE.\n\n"
        f"Text:\n{text}"
    )

    try:
        response = ollama.chat(
            model=config.OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.1},
        )
        content = response["message"]["content"]

        # Extract JSON from response (handle markdown code blocks)
        if "```" in content:
            start = content.find("[")
            end = content.rfind("]") + 1
            content = content[start:end]

        detected = json.loads(content)
        entities = []
        for item in detected:
            ent_text = item.get("text", "")
            label = item.get("label", "UNKNOWN")
            # Find position in original text
            idx = text.find(ent_text)
            if idx >= 0:
                entities.append(Entity(text=ent_text, label=label, start_char=idx, end_char=idx + len(ent_text)))
        return entities
    except Exception as e:
        logger.warning("Prompt-based detection failed: %s", e)
        return []


def detect_entities(text: str, use_prompt: bool = True) -> list[Entity]:
    """Combined detection: merge NER + prompt-based results, deduplicate."""
    ner_entities = detect_ner(text)
    prompt_entities = detect_prompt(text) if use_prompt else []

    # Merge and deduplicate by (text, start_char)
    seen: set[tuple[str, int]] = set()
    merged: list[Entity] = []

    for ent in ner_entities + prompt_entities:
        key = (ent.text, ent.start_char)
        if key not in seen:
            seen.add(key)
            merged.append(ent)

    # Sort by start position
    merged.sort(key=lambda e: e.start_char)
    return merged
