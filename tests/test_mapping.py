"""Tests for MappingStore."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pseudopipe.mapping import MappingStore, MappingEntry


def test_add_and_get():
    store = MappingStore()
    store.add("ToyMakers", "FunCraft", "ORG")
    assert store.get_pseudonym("ToyMakers") == "FunCraft"
    assert store.get_original("FunCraft") == "ToyMakers"


def test_add_duplicate_ignored():
    store = MappingStore()
    store.add("ToyMakers", "FunCraft", "ORG")
    store.add("ToyMakers", "DifferentName", "ORG")
    assert len(store.mappings) == 1
    assert store.get_pseudonym("ToyMakers") == "FunCraft"


def test_scale_factor():
    store = MappingStore()
    store.add("$42M", "$37.8M", "MONEY", scale_factor=0.9)
    assert store.get_scale_factor("$37.8M") == 0.9


def test_get_nonexistent():
    store = MappingStore()
    assert store.get_pseudonym("nothing") is None
    assert store.get_original("nothing") is None
    assert store.get_scale_factor("nothing") is None


def test_forward_reverse_maps():
    store = MappingStore()
    store.add("A", "X", "PERSON")
    store.add("B", "Y", "ORG")
    assert store.forward_map == {"A": "X", "B": "Y"}
    assert store.reverse_map == {"X": "A", "Y": "B"}


def test_save_and_load(tmp_path: Path):
    store = MappingStore(run_id="test-run")
    store.add("ToyMakers", "FunCraft", "ORG")
    store.add("$42M", "$37.8M", "MONEY", scale_factor=0.9)

    path = tmp_path / "mapping.json"
    store.save(path)

    loaded = MappingStore.load(path)
    assert loaded.run_id == "test-run"
    assert len(loaded.mappings) == 2
    assert loaded.get_pseudonym("ToyMakers") == "FunCraft"
    assert loaded.get_scale_factor("$37.8M") == 0.9


def test_save_creates_parent_dirs(tmp_path: Path):
    store = MappingStore()
    store.add("X", "Y", "ORG")
    path = tmp_path / "subdir" / "nested" / "mapping.json"
    store.save(path)
    assert path.exists()


def test_json_format(tmp_path: Path):
    store = MappingStore(run_id="fmt-test")
    store.add("Alice", "Bob", "PERSON")
    path = tmp_path / "mapping.json"
    store.save(path)

    data = json.loads(path.read_text())
    assert data["run_id"] == "fmt-test"
    assert len(data["mappings"]) == 1
    assert data["mappings"][0]["original"] == "Alice"
    assert data["mappings"][0]["pseudonym"] == "Bob"
