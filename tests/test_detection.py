"""Tests for Stage 1: Detection."""

from __future__ import annotations

import pytest

from pseudopipe.detection import detect_ner, detect_entities, Entity


SAMPLE_TEXT = (
    "John Harrison, CEO of ToyMakers Inc., reported $42M in revenue. "
    "Sarah Chen projects 34% growth. Project Moonbeam uses the TurboMold 3000."
)


def test_detect_ner_finds_persons():
    entities = detect_ner(SAMPLE_TEXT)
    texts = {e.text for e in entities}
    assert "John Harrison" in texts or "Harrison" in texts


def test_detect_ner_finds_org():
    entities = detect_ner(SAMPLE_TEXT)
    labels = {e.label for e in entities}
    texts = {e.text for e in entities}
    # Should find ToyMakers Inc. or similar
    assert any("ToyMakers" in t for t in texts) or "ORG" in labels


def test_detect_ner_finds_money():
    entities = detect_ner(SAMPLE_TEXT)
    money_entities = [e for e in entities if e.label == "MONEY"]
    assert len(money_entities) >= 1


def test_detect_ner_finds_percent():
    entities = detect_ner(SAMPLE_TEXT)
    pct_entities = [e for e in entities if e.label in ("PERCENT", "CARDINAL")]
    assert len(pct_entities) >= 1


def test_detect_ner_finds_custom_entities():
    entities = detect_ner(SAMPLE_TEXT)
    texts = {e.text.lower() for e in entities}
    labels = {e.label for e in entities}
    # At least one custom entity should be found
    has_project = any("moonbeam" in t for t in texts)
    has_machine = any("turbomold" in t for t in texts)
    assert has_project or has_machine or "PROJECT" in labels or "MACHINE" in labels


def test_detect_entities_deduplicates():
    # NER-only detection to ensure no duplicates
    entities = detect_entities(SAMPLE_TEXT, use_prompt=False)
    keys = [(e.text, e.start_char) for e in entities]
    assert len(keys) == len(set(keys))


def test_detect_entities_sorted_by_position():
    entities = detect_entities(SAMPLE_TEXT, use_prompt=False)
    positions = [e.start_char for e in entities]
    assert positions == sorted(positions)


def test_entity_dataclass():
    e = Entity(text="Test", label="ORG", start_char=0, end_char=4)
    assert e.text == "Test"
    assert e.label == "ORG"
    # Frozen dataclass
    with pytest.raises(AttributeError):
        e.text = "Other"


def test_detect_ner_finds_email():
    text = "Contact rtorres@toymakers.com for details."
    entities = detect_ner(text)
    email_entities = [e for e in entities if e.label == "EMAIL"]
    assert len(email_entities) == 1
    assert email_entities[0].text == "rtorres@toymakers.com"
