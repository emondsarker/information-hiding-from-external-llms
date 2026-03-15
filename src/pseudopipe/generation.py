"""Stage 2: GEN — Pseudonym candidate generation via Qwen (GEN_prompt)."""

from __future__ import annotations

import hashlib
import logging
import random
import re

from pseudopipe import config
from pseudopipe.detection import Entity
from pseudopipe.mapping import MappingStore

logger = logging.getLogger(__name__)


_used_names: set[str] = set()


def _hash_index(text: str, names: list[str]) -> int:
    """Deterministic index from a hash of the entity text."""
    h = int(hashlib.sha256(text.encode()).hexdigest(), 16)
    return h % len(names)


def _pick_fallback(text: str, names: list[str]) -> str:
    """Pick a fallback name, avoiding duplicates."""
    idx = _hash_index(text, names)
    for offset in range(len(names)):
        candidate = names[(idx + offset) % len(names)]
        if candidate not in _used_names:
            _used_names.add(candidate)
            return candidate
    # All names used; append a suffix to make unique
    base = names[idx]
    _used_names.add(f"{base} II")
    return f"{base} II"


def _query_qwen(prompt: str) -> str | None:
    """Query local Qwen model via ollama. Returns None on failure."""
    try:
        import ollama

        response = ollama.chat(
            model=config.OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.7},
        )
        return response["message"]["content"].strip().strip('"').strip("'")
    except Exception as e:
        logger.warning("Qwen query failed: %s", e)
        return None


def _generate_person_name(original: str) -> str:
    prompt = (
        f"Generate a fictional full name with a similar cultural origin as '{original}'. "
        "Return ONLY the name, nothing else."
    )
    result = _query_qwen(prompt)
    if result and len(result.split()) >= 2 and len(result) < 50:
        return result
    # Fallback
    return _pick_fallback(original, config.FALLBACK_PERSON_NAMES)


def _generate_org_name(original: str) -> str:
    prompt = (
        f"Generate a fictional company name in the same industry as '{original}'. "
        "Return ONLY the company name, nothing else."
    )
    result = _query_qwen(prompt)
    if result and len(result) < 60:
        return result
    return _pick_fallback(original, config.FALLBACK_ORG_NAMES)


def _generate_project_name(original: str) -> str:
    prompt = (
        f"Generate a fictional project codename similar in style to '{original}'. "
        "Return ONLY the project name (e.g. 'Project Phoenix'), nothing else."
    )
    result = _query_qwen(prompt)
    if result and len(result) < 50:
        return result
    return _pick_fallback(original, config.FALLBACK_PROJECT_NAMES)


def _generate_machine_name(original: str) -> str:
    prompt = (
        f"Generate a fictional industrial machine/equipment name similar in style to '{original}'. "
        "Return ONLY the machine name, nothing else."
    )
    result = _query_qwen(prompt)
    if result and len(result) < 50:
        return result
    return _pick_fallback(original, config.FALLBACK_MACHINE_NAMES)


def _scale_monetary_value(text: str) -> tuple[str, float]:
    """Apply random scaling factor to monetary values. Returns (new_text, scale_factor)."""
    scale = random.uniform(*config.MONEY_SCALE_RANGE)

    # Try percentage first (before monetary)
    pct_match = re.match(r"^(\d+(?:\.\d+)?)\s*%$", text)
    if pct_match:
        num = float(pct_match.group(1))
        scaled = round(num * scale, 1)
        return f"{scaled}%", scale

    # Extract numeric value and suffix (monetary)
    has_dollar = text.startswith("$")
    match = re.match(r"^\$?([\d,]+(?:\.\d+)?)\s*(M|B|K|million|billion|thousand)?(.*)$", text, re.IGNORECASE)
    if match:
        num_str = match.group(1).replace(",", "")
        num = float(num_str)
        suffix = match.group(2) or ""
        rest = match.group(3) or ""
        prefix = "$" if has_dollar else ""

        scaled = num * scale
        # Round based on magnitude
        if scaled >= 100:
            scaled = round(scaled, 0)
            formatted = f"{prefix}{scaled:,.0f}"
        elif scaled >= 1:
            scaled = round(scaled, 1)
            formatted = f"{prefix}{scaled:,.1f}"
        else:
            scaled = round(scaled, 2)
            formatted = f"{prefix}{scaled:,.2f}"

        return f"{formatted}{suffix}{rest}", scale

    # Fallback: return as-is with scale 1.0
    return text, 1.0


def generate_pseudonyms(entities: list[Entity], mapping: MappingStore) -> MappingStore:
    """Generate pseudonyms for all detected entities, storing in mapping."""
    # Reset and seed used names from existing mappings to avoid collisions
    _used_names.clear()
    _used_names.update(entry.pseudonym for entry in mapping.mappings)

    for entity in entities:
        # Skip if already mapped (reuse for consistency)
        if mapping.get_pseudonym(entity.text) is not None:
            continue

        label = entity.label
        text = entity.text

        if label == "PERSON":
            pseudonym = _generate_person_name(text)
            mapping.add(text, pseudonym, label)

        elif label == "ORG":
            pseudonym = _generate_org_name(text)
            mapping.add(text, pseudonym, label)

        elif label in ("MONEY", "CARDINAL"):
            pseudonym, scale = _scale_monetary_value(text)
            mapping.add(text, pseudonym, label, scale_factor=scale)

        elif label == "PERCENT":
            pseudonym, scale = _scale_monetary_value(text)
            mapping.add(text, pseudonym, label, scale_factor=scale)

        elif label == "PROJECT":
            pseudonym = _generate_project_name(text)
            mapping.add(text, pseudonym, label)

        elif label == "MACHINE":
            pseudonym = _generate_machine_name(text)
            mapping.add(text, pseudonym, label)

        elif label in ("GPE", "LOC"):
            # For locations, use Qwen to generate a fictional but plausible alternative
            prompt = (
                f"Generate a fictional city or location name that could substitute for '{text}'. "
                "Return ONLY the location name, nothing else."
            )
            pseudonym = _query_qwen(prompt)
            if not pseudonym or len(pseudonym) > 40:
                pseudonym = _pick_fallback(text, config.FALLBACK_LOCATION_NAMES)
            mapping.add(text, pseudonym, label)

        elif label == "EMAIL":
            local_part = f"user{abs(hash(text)) % 1000}"
            pseudonym = f"{local_part}@example.com"
            mapping.add(text, pseudonym, label)

        elif label == "FINANCIAL_METRIC":
            # Keep financial metric labels as-is (ARR, MRR, EBITDA are generic terms)
            continue

        else:
            logger.debug("Unhandled entity label %s for '%s'", label, text)

    return mapping
