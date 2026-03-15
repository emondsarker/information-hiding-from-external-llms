"""QA Gate: sentence-transformer cosine similarity check."""

from __future__ import annotations

import logging

import numpy as np

from pseudopipe import config

logger = logging.getLogger(__name__)

_model_cache = None


def _get_model():
    global _model_cache
    if _model_cache is None:
        from sentence_transformers import SentenceTransformer

        _model_cache = SentenceTransformer(config.SIMILARITY_MODEL)
    return _model_cache


def _chunk_text(text: str, max_chunk_len: int = 500) -> list[str]:
    """Split text into paragraph-sized chunks."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) > max_chunk_len and current:
            chunks.append(current.strip())
            current = para
        else:
            current = current + "\n\n" + para if current else para
    if current:
        chunks.append(current.strip())
    return chunks if chunks else [text]


def compute_similarity(original: str, pseudonymized: str) -> dict:
    """Compute cosine similarity between original and pseudonymized text.

    For long texts, computes per-chunk similarity and reports mean + min.
    Returns dict with keys: mean_similarity, min_similarity, per_chunk, passes_threshold.
    """
    model = _get_model()
    orig_chunks = _chunk_text(original)
    pseudo_chunks = _chunk_text(pseudonymized)

    # Align chunk counts (use min to avoid index errors)
    n_chunks = min(len(orig_chunks), len(pseudo_chunks))
    orig_chunks = orig_chunks[:n_chunks]
    pseudo_chunks = pseudo_chunks[:n_chunks]

    similarities = []
    for oc, pc in zip(orig_chunks, pseudo_chunks):
        embeddings = model.encode([oc, pc])
        cos_sim = float(np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        ))
        similarities.append(cos_sim)

    mean_sim = float(np.mean(similarities))
    min_sim = float(np.min(similarities))
    passes = mean_sim >= config.SIMILARITY_THRESHOLD

    if not passes:
        logger.warning(
            "Similarity below threshold: mean=%.3f, min=%.3f (threshold=%.2f)",
            mean_sim, min_sim, config.SIMILARITY_THRESHOLD,
        )

    return {
        "mean_similarity": mean_sim,
        "min_similarity": min_sim,
        "per_chunk": similarities,
        "passes_threshold": passes,
    }
