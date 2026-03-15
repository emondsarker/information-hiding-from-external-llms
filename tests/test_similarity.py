"""Tests for QA Gate: similarity checking."""

from __future__ import annotations

import pytest

from pseudopipe.similarity import compute_similarity, _chunk_text


def test_chunk_text_single_paragraph():
    text = "This is a short paragraph."
    chunks = _chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_multiple_paragraphs():
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    chunks = _chunk_text(text)
    assert len(chunks) >= 1


def test_chunk_text_empty():
    chunks = _chunk_text("")
    assert len(chunks) == 1


def test_similarity_identical_text():
    text = "The quick brown fox jumps over the lazy dog."
    result = compute_similarity(text, text)
    assert result["mean_similarity"] > 0.99
    assert result["passes_threshold"] is True


def test_similarity_similar_text():
    original = "John Harrison is the CEO of ToyMakers Inc. with $42M in revenue."
    pseudonymized = "Alex Morgan is the CEO of FunCraft Industries with $38M in revenue."
    result = compute_similarity(original, pseudonymized)
    # Should be reasonably similar (same structure, different names)
    assert result["mean_similarity"] > 0.5
    assert "per_chunk" in result


def test_similarity_very_different_text():
    text1 = "The company reported strong financial results this quarter."
    text2 = "A cat sat on a mat in the sunshine."
    result = compute_similarity(text1, text2)
    assert result["mean_similarity"] < 0.8


def test_similarity_result_keys():
    result = compute_similarity("Hello world", "Hello world")
    assert "mean_similarity" in result
    assert "min_similarity" in result
    assert "per_chunk" in result
    assert "passes_threshold" in result
