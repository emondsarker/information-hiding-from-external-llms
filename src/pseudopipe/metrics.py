"""Evaluation metrics: PRR, PPS, SCS, cosine, BERTScore, ROUGE, entity accuracy, semantic drift."""

from __future__ import annotations

import logging
from dataclasses import dataclass, asdict

import numpy as np

from pseudopipe import config
from pseudopipe.detection import Entity, detect_ner
from pseudopipe.mapping import MappingStore

logger = logging.getLogger(__name__)


@dataclass
class MetricsReport:
    privacy_removal_rate: float | None = None
    privacy_preservation_score: float | None = None
    semantic_correctness_score: float | None = None
    cosine_similarity: float | None = None
    bert_score_f1: float | None = None
    rouge_1: float | None = None
    rouge_2: float | None = None
    rouge_l: float | None = None
    entity_mapping_accuracy: float | None = None
    semantic_drift: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def compute_prr(original_text: str, pseudonymized_text: str) -> float:
    """Privacy Removal Rate: fraction of original entities NOT found in pseudonymized text.

    PRR = |P' ∩ P| / |P| ... but we want the removal rate, so:
    PRR = 1 - (entities_still_present / total_original_entities)
    """
    original_entities = detect_ner(original_text)
    if not original_entities:
        return 1.0

    original_texts = {e.text.lower() for e in original_entities}
    still_present = sum(1 for t in original_texts if t in pseudonymized_text.lower())

    return 1.0 - (still_present / len(original_texts))


def compute_pps(mapping: MappingStore) -> float:
    """Privacy Preservation Score: avg semantic distance between original and pseudonym.

    PPS = avg(1 - sim(original_i, pseudonym_i))
    """
    if not mapping.mappings:
        return 1.0

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(config.METRICS_EMBEDDING_MODEL)

    scores = []
    for entry in mapping.mappings:
        if entry.label in ("MONEY", "CARDINAL", "PERCENT"):
            # For numeric values, compute based on scale factor
            if entry.scale_factor is not None:
                scores.append(abs(1.0 - entry.scale_factor))
            continue

        embeddings = model.encode([entry.original, entry.pseudonym])
        cos_sim = float(
            np.dot(embeddings[0], embeddings[1])
            / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
        )
        scores.append(1.0 - cos_sim)

    return float(np.mean(scores)) if scores else 1.0


def compute_scs(pseudonymized_text: str) -> float:
    """Semantic Correctness Score: perplexity of pseudonymized text.

    Lower = better (text reads more naturally).
    Uses a lightweight approach via sentence-transformers.
    """
    # Approximate SCS using sentence coherence scores
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(config.SIMILARITY_MODEL)

    sentences = [s.strip() for s in pseudonymized_text.split(".") if s.strip()]
    if len(sentences) < 2:
        return 0.0

    # Compute pairwise cosine similarity of adjacent sentences
    embeddings = model.encode(sentences)
    coherence_scores = []
    for i in range(len(embeddings) - 1):
        cos_sim = float(
            np.dot(embeddings[i], embeddings[i + 1])
            / (np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[i + 1]) + 1e-8)
        )
        coherence_scores.append(cos_sim)

    # Invert: lower coherence = higher SCS (worse)
    # Scale to approximate perplexity-like range
    mean_coherence = float(np.mean(coherence_scores))
    scs = (1.0 - mean_coherence) * 100.0
    return scs


def compute_cosine_similarity(original: str, pseudonymized: str) -> float:
    """Overall cosine similarity between original and pseudonymized text."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(config.SIMILARITY_MODEL)
    embeddings = model.encode([original, pseudonymized])
    return float(
        np.dot(embeddings[0], embeddings[1])
        / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
    )


def compute_bert_score(reference: str, hypothesis: str) -> float:
    """BERTScore F1 between reference and hypothesis texts."""
    try:
        from bert_score import score as bert_score_fn

        P, R, F1 = bert_score_fn(
            [hypothesis], [reference], lang="en", verbose=False
        )
        return float(F1[0])
    except Exception as e:
        logger.warning("BERTScore computation failed: %s", e)
        return 0.0


def compute_rouge(reference: str, hypothesis: str) -> dict[str, float]:
    """ROUGE-1/2/L F-measure between reference and hypothesis."""
    try:
        from rouge_score import rouge_scorer

        scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
        scores = scorer.score(reference, hypothesis)
        return {
            "rouge_1": scores["rouge1"].fmeasure,
            "rouge_2": scores["rouge2"].fmeasure,
            "rouge_l": scores["rougeL"].fmeasure,
        }
    except Exception as e:
        logger.warning("ROUGE computation failed: %s", e)
        return {"rouge_1": 0.0, "rouge_2": 0.0, "rouge_l": 0.0}


def compute_entity_mapping_accuracy(
    original_text: str,
    deanonymized_text: str,
) -> float:
    """Fraction of original entities correctly restored in de-anonymized text."""
    original_entities = detect_ner(original_text)
    if not original_entities:
        return 1.0

    original_texts = {e.text for e in original_entities}
    restored = sum(1 for t in original_texts if t in deanonymized_text)
    return restored / len(original_texts)


def compute_semantic_drift(original: str, deanonymized: str) -> float:
    """Semantic drift: 1 - cosine_sim(original, deanonymized)."""
    cos_sim = compute_cosine_similarity(original, deanonymized)
    return 1.0 - cos_sim


def compute_all_metrics(
    original_text: str,
    pseudonymized_text: str,
    deanonymized_text: str | None,
    mapping: MappingStore,
) -> MetricsReport:
    """Compute all metrics and return a MetricsReport."""
    report = MetricsReport()

    report.privacy_removal_rate = compute_prr(original_text, pseudonymized_text)
    report.privacy_preservation_score = compute_pps(mapping)
    report.semantic_correctness_score = compute_scs(pseudonymized_text)
    report.cosine_similarity = compute_cosine_similarity(original_text, pseudonymized_text)

    if deanonymized_text:
        report.bert_score_f1 = compute_bert_score(original_text, deanonymized_text)
        rouge = compute_rouge(original_text, deanonymized_text)
        report.rouge_1 = rouge["rouge_1"]
        report.rouge_2 = rouge["rouge_2"]
        report.rouge_l = rouge["rouge_l"]
        report.entity_mapping_accuracy = compute_entity_mapping_accuracy(
            original_text, deanonymized_text
        )
        report.semantic_drift = compute_semantic_drift(original_text, deanonymized_text)

    return report
