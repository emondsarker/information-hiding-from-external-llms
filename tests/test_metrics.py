"""Tests for evaluation metrics."""

from __future__ import annotations

import pytest

from pseudopipe.mapping import MappingStore
from pseudopipe.metrics import (
    MetricsReport,
    compute_prr,
    compute_pps,
    compute_cosine_similarity,
    compute_rouge,
    compute_entity_mapping_accuracy,
    compute_semantic_drift,
    compute_all_metrics,
)


ORIGINAL = (
    "John Harrison, CEO of ToyMakers Inc., reported $42M in annual revenue. "
    "Sarah Chen projects 34% growth for the company."
)

PSEUDONYMIZED = (
    "Alex Morgan, CEO of FunCraft Industries, reported $38M in annual revenue. "
    "Jamie Santos projects 28% growth for the company."
)


def test_metrics_report_to_dict():
    report = MetricsReport(privacy_removal_rate=0.9, cosine_similarity=0.85)
    d = report.to_dict()
    assert d["privacy_removal_rate"] == 0.9
    assert d["cosine_similarity"] == 0.85
    assert d["bert_score_f1"] is None


def test_compute_prr():
    prr = compute_prr(ORIGINAL, PSEUDONYMIZED)
    # Original entities should not appear in pseudonymized text
    assert 0.0 <= prr <= 1.0
    # Should be fairly high since names are different
    assert prr > 0.3


def test_compute_prr_identical():
    prr = compute_prr(ORIGINAL, ORIGINAL)
    # All entities still present
    assert prr == 0.0


def test_compute_pps():
    mapping = MappingStore()
    mapping.add("John Harrison", "Alex Morgan", "PERSON")
    mapping.add("ToyMakers Inc.", "FunCraft Industries", "ORG")
    pps = compute_pps(mapping)
    assert 0.0 <= pps <= 1.0


def test_compute_pps_empty():
    mapping = MappingStore()
    pps = compute_pps(mapping)
    assert pps == 1.0


def test_compute_cosine_similarity():
    sim = compute_cosine_similarity(ORIGINAL, PSEUDONYMIZED)
    assert 0.0 <= sim <= 1.0
    # Should be similar since structure is preserved
    assert sim > 0.5


def test_compute_cosine_similarity_identical():
    sim = compute_cosine_similarity(ORIGINAL, ORIGINAL)
    assert sim > 0.99


def test_compute_rouge():
    scores = compute_rouge(ORIGINAL, PSEUDONYMIZED)
    assert "rouge_1" in scores
    assert "rouge_2" in scores
    assert "rouge_l" in scores
    for v in scores.values():
        assert 0.0 <= v <= 1.0


def test_compute_entity_mapping_accuracy_perfect():
    # De-anonymized text contains all originals
    accuracy = compute_entity_mapping_accuracy(ORIGINAL, ORIGINAL)
    assert accuracy == 1.0


def test_compute_entity_mapping_accuracy_none():
    accuracy = compute_entity_mapping_accuracy(ORIGINAL, "Completely different text with no entities.")
    assert accuracy < 1.0


def test_compute_semantic_drift():
    drift = compute_semantic_drift(ORIGINAL, ORIGINAL)
    assert drift < 0.01  # Nearly zero for identical text


def test_compute_all_metrics_no_deanonymized():
    mapping = MappingStore()
    mapping.add("John Harrison", "Alex Morgan", "PERSON")
    report = compute_all_metrics(ORIGINAL, PSEUDONYMIZED, None, mapping)
    assert report.privacy_removal_rate is not None
    assert report.privacy_preservation_score is not None
    assert report.cosine_similarity is not None
    # No de-anonymized text, so these should be None
    assert report.bert_score_f1 is None
    assert report.rouge_1 is None


def test_compute_all_metrics_with_deanonymized():
    mapping = MappingStore()
    mapping.add("John Harrison", "Alex Morgan", "PERSON")
    report = compute_all_metrics(ORIGINAL, PSEUDONYMIZED, ORIGINAL, mapping)
    assert report.privacy_removal_rate is not None
    assert report.bert_score_f1 is not None
    assert report.rouge_1 is not None
    assert report.entity_mapping_accuracy is not None
    assert report.semantic_drift is not None
