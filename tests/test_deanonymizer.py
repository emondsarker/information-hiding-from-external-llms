"""Tests for de-anonymization."""

from __future__ import annotations

from pseudopipe.deanonymizer import deanonymize
from pseudopipe.mapping import MappingStore


def _make_mapping() -> MappingStore:
    m = MappingStore()
    m.add("ToyMakers Inc.", "FunCraft Industries", "ORG")
    m.add("John Harrison", "Alex Morgan", "PERSON")
    m.add("Sarah Chen", "Jamie Santos", "PERSON")
    m.add("$42M", "$37.8M", "MONEY", scale_factor=0.9)
    return m


def test_deanonymize_basic():
    text = "FunCraft Industries reported strong results under Alex Morgan."
    mapping = _make_mapping()
    result = deanonymize(text, mapping)
    assert "ToyMakers Inc." in result
    assert "John Harrison" in result
    assert "FunCraft Industries" not in result
    assert "Alex Morgan" not in result


def test_deanonymize_possessive():
    text = "Alex Morgan's leadership at FunCraft Industries has been excellent."
    mapping = _make_mapping()
    result = deanonymize(text, mapping)
    assert "John Harrison's" in result
    assert "ToyMakers Inc." in result


def test_deanonymize_multiple_entities():
    text = "Alex Morgan and Jamie Santos lead FunCraft Industries."
    mapping = _make_mapping()
    result = deanonymize(text, mapping)
    assert "John Harrison" in result
    assert "Sarah Chen" in result
    assert "ToyMakers Inc." in result


def test_deanonymize_preserves_non_mapped_text():
    text = "The weather is nice today at FunCraft Industries."
    mapping = _make_mapping()
    result = deanonymize(text, mapping)
    assert "The weather is nice today" in result
    assert "ToyMakers Inc." in result


def test_deanonymize_empty_mapping():
    text = "Nothing to replace here."
    mapping = MappingStore()
    result = deanonymize(text, mapping)
    assert result == text


def test_deanonymize_monetary():
    text = "Revenue reached $37.8M last quarter."
    mapping = _make_mapping()
    result = deanonymize(text, mapping)
    assert "$42M" in result
    assert "$37.8M" not in result


def test_no_numeric_collision():
    """Reversing numeric pseudonyms must not cause substring collisions."""
    m = MappingStore()
    m.add("$45", "$44.8", "MONEY", scale_factor=0.99)
    m.add("$8", "$7.2", "MONEY", scale_factor=0.9)
    text = "Cost was $44.8 and fee was $7.2."
    result = deanonymize(text, m)
    assert "$45" in result
    assert "$8" in result
    assert "\x00" not in result
