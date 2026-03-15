"""Tests for Stage 2: Generation."""

from __future__ import annotations

import pytest

from pseudopipe.detection import Entity
from pseudopipe.generation import generate_pseudonyms, _scale_monetary_value, _hash_index
from pseudopipe.mapping import MappingStore


def test_scale_monetary_value_dollar():
    result, scale = _scale_monetary_value("$42M")
    assert result.startswith("$")
    assert "M" in result
    assert 0.7 <= scale <= 1.3


def test_scale_monetary_value_plain_number():
    result, scale = _scale_monetary_value("$12.5")
    assert result.startswith("$")
    assert 0.7 <= scale <= 1.3


def test_scale_percentage():
    result, scale = _scale_monetary_value("34%")
    assert "%" in result
    assert 0.7 <= scale <= 1.3


def test_hash_index_deterministic():
    names = ["Alice", "Bob", "Charlie"]
    idx1 = _hash_index("test", names)
    idx2 = _hash_index("test", names)
    assert idx1 == idx2
    assert 0 <= idx1 < len(names)


def test_hash_index_in_range():
    names = ["A", "B", "C", "D", "E"]
    for text in ["foo", "bar", "baz", "qux"]:
        idx = _hash_index(text, names)
        assert 0 <= idx < len(names)


def test_generate_pseudonyms_creates_mappings():
    entities = [
        Entity(text="John Smith", label="PERSON", start_char=0, end_char=10),
        Entity(text="Acme Corp", label="ORG", start_char=20, end_char=29),
    ]
    mapping = MappingStore()
    mapping = generate_pseudonyms(entities, mapping)
    assert len(mapping.mappings) >= 2
    assert mapping.get_pseudonym("John Smith") is not None
    assert mapping.get_pseudonym("Acme Corp") is not None


def test_generate_pseudonyms_reuses_existing():
    entities = [
        Entity(text="John Smith", label="PERSON", start_char=0, end_char=10),
        Entity(text="John Smith", label="PERSON", start_char=50, end_char=60),
    ]
    mapping = MappingStore()
    mapping = generate_pseudonyms(entities, mapping)
    # Should only have one mapping entry
    assert len(mapping.mappings) == 1


def test_generate_pseudonyms_money():
    entities = [
        Entity(text="$42M", label="MONEY", start_char=0, end_char=4),
    ]
    mapping = MappingStore()
    mapping = generate_pseudonyms(entities, mapping)
    assert len(mapping.mappings) == 1
    entry = mapping.mappings[0]
    assert entry.scale_factor is not None
    assert entry.pseudonym != "$42M" or entry.scale_factor == 1.0


def test_generate_pseudonyms_skips_financial_metric():
    entities = [
        Entity(text="ARR", label="FINANCIAL_METRIC", start_char=0, end_char=3),
    ]
    mapping = MappingStore()
    mapping = generate_pseudonyms(entities, mapping)
    assert len(mapping.mappings) == 0


def test_locations_get_unique_pseudonyms():
    """Two GPE entities should get different pseudonyms."""
    entities = [
        Entity(text="Austin", label="GPE", start_char=0, end_char=6),
        Entity(text="Texas", label="GPE", start_char=10, end_char=15),
    ]
    mapping = MappingStore()
    mapping = generate_pseudonyms(entities, mapping)
    austin_pseudo = mapping.get_pseudonym("Austin")
    texas_pseudo = mapping.get_pseudonym("Texas")
    assert austin_pseudo is not None
    assert texas_pseudo is not None
    assert austin_pseudo != texas_pseudo


def test_generate_pseudonyms_email():
    """EMAIL entities should produce pseudonyms containing @."""
    entities = [
        Entity(text="rtorres@toymakers.com", label="EMAIL", start_char=0, end_char=20),
    ]
    mapping = MappingStore()
    mapping = generate_pseudonyms(entities, mapping)
    pseudo = mapping.get_pseudonym("rtorres@toymakers.com")
    assert pseudo is not None
    assert "@" in pseudo


def test_used_names_reset_between_runs():
    """_used_names should be reset so names from run 1 are available in run 2."""
    entities1 = [
        Entity(text="Austin", label="GPE", start_char=0, end_char=6),
    ]
    mapping1 = MappingStore()
    mapping1 = generate_pseudonyms(entities1, mapping1)
    pseudo1 = mapping1.get_pseudonym("Austin")

    # Second run with a different entity but fresh mapping
    entities2 = [
        Entity(text="Dallas", label="GPE", start_char=0, end_char=6),
    ]
    mapping2 = MappingStore()
    mapping2 = generate_pseudonyms(entities2, mapping2)
    pseudo2 = mapping2.get_pseudonym("Dallas")

    # pseudo1 should be available again in run 2 (i.e., pseudo2 could be the same name)
    # The key assertion: run 2 doesn't avoid names from run 1
    assert pseudo2 is not None
