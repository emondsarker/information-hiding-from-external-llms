"""Tests for Stage 3: Replacement."""

from __future__ import annotations

from pseudopipe.replacement import _direct_replace, replace_entities
from pseudopipe.mapping import MappingStore


def _make_mapping() -> MappingStore:
    m = MappingStore()
    m.add("ToyMakers Inc.", "FunCraft Industries", "ORG")
    m.add("John Harrison", "Alex Morgan", "PERSON")
    m.add("$42M", "$37.8M", "MONEY", scale_factor=0.9)
    return m


def test_direct_replace_basic():
    text = "ToyMakers Inc. was founded by John Harrison."
    mapping = _make_mapping()
    result = _direct_replace(text, mapping)
    assert "FunCraft Industries" in result
    assert "Alex Morgan" in result
    assert "ToyMakers Inc." not in result
    assert "John Harrison" not in result


def test_direct_replace_multiple_occurrences():
    text = "John Harrison leads ToyMakers Inc. John Harrison is the CEO."
    mapping = _make_mapping()
    result = _direct_replace(text, mapping)
    assert result.count("Alex Morgan") == 2
    assert "John Harrison" not in result


def test_direct_replace_preserves_surrounding_text():
    text = "Hello world. ToyMakers Inc. is great. Goodbye."
    mapping = _make_mapping()
    result = _direct_replace(text, mapping)
    assert result.startswith("Hello world.")
    assert result.endswith("Goodbye.")


def test_replace_entities_no_fluency():
    text = "John Harrison, CEO of ToyMakers Inc., reported $42M revenue."
    mapping = _make_mapping()
    result = replace_entities(text, mapping, rewrite_fluency=False)
    assert "Alex Morgan" in result
    assert "FunCraft Industries" in result
    assert "$37.8M" in result
    assert "John Harrison" not in result
    assert "ToyMakers Inc." not in result


def test_direct_replace_longest_first():
    """Ensure longer matches are replaced before shorter ones."""
    m = MappingStore()
    m.add("ToyMakers Inc.", "FunCraft Industries", "ORG")
    m.add("ToyMakers", "FunCraft", "ORG")  # Shorter match
    text = "ToyMakers Inc. is owned by ToyMakers."
    result = _direct_replace(text, m)
    # The "ToyMakers Inc." should be fully replaced, not partially
    assert "FunCraft Industries" in result


def test_no_numeric_collision():
    """Inserted pseudonyms must not become targets for later replacements."""
    m = MappingStore()
    m.add("34%", "32.8%", "PERCENT", scale_factor=0.96)
    m.add("8%", "9.3%", "PERCENT", scale_factor=1.16)
    text = "Growth was 34% and costs rose 8%."
    result = _direct_replace(text, m)
    assert "32.8%" in result
    assert "9.3%" in result
    assert "32.9.3%" not in result


def test_no_marker_remnants():
    """No null-byte markers should remain in output."""
    m = MappingStore()
    m.add("34%", "32.8%", "PERCENT", scale_factor=0.96)
    m.add("8%", "9.3%", "PERCENT", scale_factor=1.16)
    text = "Growth was 34% and costs rose 8%."
    result = _direct_replace(text, m)
    assert "\x00" not in result
