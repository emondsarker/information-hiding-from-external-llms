"""Generate a comparative pipeline report.

Two copies of the same input text are processed:
  Path A (Pipeline): detect → pseudonymize → Claude → de-anonymize
  Path B (Baseline): Claude on the original text directly

The two LLM outputs are compared to measure how much quality
the pseudonymization architecture costs.
"""

from pathlib import Path

from pseudopipe.pipeline import run_pipeline
from pseudopipe.external_llm import send_to_claude
from pseudopipe.metrics import (
    compute_bert_score,
    compute_cosine_similarity,
    compute_rouge,
)


def main():
    input_text = Path("sample_data/toymakers_memo.txt").read_text()

    # ── Path A: Full pipeline (de-id → LLM → re-id) ──
    print("Running Path A: full pseudonymization pipeline...")
    pipeline_result = run_pipeline(
        input_text,
        use_prompt_detection=False,
        rewrite_fluency=False,
        skip_claude=False,
        mapping_output_path=Path("/tmp/pseudopipe_mapping.json"),
    )

    # ── Path B: Baseline (original text → LLM directly) ──
    print("Running Path B: sending original text to Claude (baseline)...")
    try:
        baseline_response = send_to_claude(input_text)
    except Exception as e:
        print(f"Baseline Claude call failed: {e}")
        baseline_response = None

    # ── Comparison metrics ──
    comparison = {}
    if baseline_response and pipeline_result.deanonymized_report:
        print("Computing comparison metrics...")
        comparison["cosine_similarity"] = compute_cosine_similarity(
            baseline_response, pipeline_result.deanonymized_report
        )
        comparison["bert_score_f1"] = compute_bert_score(
            baseline_response, pipeline_result.deanonymized_report
        )
        rouge = compute_rouge(
            baseline_response, pipeline_result.deanonymized_report
        )
        comparison.update(rouge)

    # ── Build report ──
    sections = []

    # Section 0: Original
    sections.append("=" * 80)
    sections.append("ORIGINAL TEXT")
    sections.append("=" * 80)
    sections.append(input_text)

    # Section 1: Detected entities
    sections.append("\n" + "=" * 80)
    sections.append("STAGE 1: DETECTED ENTITIES (DET)")
    sections.append("=" * 80)
    for e in pipeline_result.entities:
        sections.append(f"  [{e.label:20s}]  {e.text!r:40s}  (chars {e.start_char}-{e.end_char})")
    sections.append(f"\n  Total: {len(pipeline_result.entities)} entities detected")

    # Section 2: Mappings
    sections.append("\n" + "=" * 80)
    sections.append("STAGE 2: PSEUDONYM MAPPINGS (GEN)")
    sections.append("=" * 80)
    for entry in pipeline_result.mapping.mappings:
        extra = f"  (scale={entry.scale_factor:.2f})" if entry.scale_factor else ""
        sections.append(f"  [{entry.label:20s}]  {entry.original!r:30s}  →  {entry.pseudonym!r:30s}{extra}")
    sections.append(f"\n  Total: {len(pipeline_result.mapping.mappings)} mappings created")

    # Section 3: Pseudonymized text
    sections.append("\n" + "=" * 80)
    sections.append("STAGE 3: PSEUDONYMIZED TEXT (REP)")
    sections.append("=" * 80)
    sections.append(pipeline_result.pseudonymized_text)

    # Section 4: Similarity QA gate
    sections.append("\n" + "=" * 80)
    sections.append("QA GATE: SIMILARITY CHECK")
    sections.append("=" * 80)
    sim = pipeline_result.similarity
    sections.append(f"  Mean similarity:   {sim['mean_similarity']:.4f}")
    sections.append(f"  Min similarity:    {sim['min_similarity']:.4f}")
    sections.append(f"  Per-chunk scores:  {[f'{s:.3f}' for s in sim['per_chunk']]}")
    sections.append(f"  Passes threshold:  {sim['passes_threshold']} (threshold=0.65)")

    # Section 5: Path A — Pipeline LLM response (pseudonymized input)
    sections.append("\n" + "=" * 80)
    sections.append("PATH A — CLAUDE RESPONSE (on pseudonymized input)")
    sections.append("=" * 80)
    sections.append(pipeline_result.claude_response or "[No response]")

    # Section 6: Path A — De-anonymized report
    sections.append("\n" + "=" * 80)
    sections.append("PATH A — DE-ANONYMIZED FINAL REPORT")
    sections.append("=" * 80)
    sections.append(pipeline_result.deanonymized_report or "[No report]")

    # Section 7: Path B — Baseline LLM response (original input)
    sections.append("\n" + "=" * 80)
    sections.append("PATH B — CLAUDE RESPONSE (on original input, baseline)")
    sections.append("=" * 80)
    sections.append(baseline_response or "[No response]")

    # Section 8: Pipeline metrics
    sections.append("\n" + "=" * 80)
    sections.append("PIPELINE METRICS (Path A internals)")
    sections.append("=" * 80)
    if pipeline_result.metrics:
        m = pipeline_result.metrics.to_dict()
        labels = {
            "privacy_removal_rate":       "Privacy Removal Rate (PRR)        — % of original entities removed",
            "privacy_preservation_score": "Privacy Preservation Score (PPS)  — semantic distance orig↔pseudo",
            "semantic_correctness_score": "Semantic Correctness Score (SCS)  — pseudo text naturalness (lower=better)",
            "cosine_similarity":          "Cosine Similarity                 — orig vs pseudo text",
            "bert_score_f1":              "BERTScore F1                      — orig vs de-anonymized report",
            "rouge_1":                    "ROUGE-1                           — orig vs de-anonymized report",
            "rouge_2":                    "ROUGE-2                           — orig vs de-anonymized report",
            "rouge_l":                    "ROUGE-L                           — orig vs de-anonymized report",
            "entity_mapping_accuracy":    "Entity Mapping Accuracy           — % entities restored correctly",
            "semantic_drift":             "Semantic Drift                    — total pipeline drift (lower=better)",
        }
        for key, desc in labels.items():
            val = m.get(key)
            if val is not None:
                sections.append(f"  {desc}:  {val:.4f}")
            else:
                sections.append(f"  {desc}:  N/A")

    # Section 9: Head-to-head comparison
    sections.append("\n" + "=" * 80)
    sections.append("HEAD-TO-HEAD COMPARISON (Path A de-anonymized vs Path B baseline)")
    sections.append("=" * 80)
    if comparison:
        comp_labels = {
            "cosine_similarity": "Cosine Similarity   — semantic closeness of the two reports",
            "bert_score_f1":     "BERTScore F1        — token-level overlap",
            "rouge_1":           "ROUGE-1             — unigram overlap",
            "rouge_2":           "ROUGE-2             — bigram overlap",
            "rouge_l":           "ROUGE-L             — longest common subsequence",
        }
        for key, desc in comp_labels.items():
            val = comparison.get(key)
            if val is not None:
                sections.append(f"  {desc}:  {val:.4f}")
            else:
                sections.append(f"  {desc}:  N/A")
        sections.append("")
        cos = comparison.get("cosine_similarity", 0)
        if cos >= 0.85:
            verdict = "EXCELLENT — pipeline output is nearly indistinguishable from baseline"
        elif cos >= 0.70:
            verdict = "GOOD — pipeline output preserves most information"
        elif cos >= 0.50:
            verdict = "FAIR — noticeable information loss through the pipeline"
        else:
            verdict = "POOR — significant degradation from pseudonymization"
        sections.append(f"  Verdict: {verdict}")
    else:
        sections.append("  [Comparison unavailable — one or both LLM calls failed]")

    sections.append("\n" + "=" * 80)

    report = "\n".join(sections)
    Path("pipeline_report.txt").write_text(report)
    print(report)


if __name__ == "__main__":
    main()
