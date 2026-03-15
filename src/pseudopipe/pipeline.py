"""Pipeline orchestrator: wires all stages together."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from pseudopipe import config
from pseudopipe.detection import detect_entities, Entity
from pseudopipe.generation import generate_pseudonyms
from pseudopipe.replacement import replace_entities
from pseudopipe.mapping import MappingStore
from pseudopipe.similarity import compute_similarity
from pseudopipe.external_llm import send_to_claude
from pseudopipe.deanonymizer import deanonymize
from pseudopipe.metrics import compute_all_metrics, MetricsReport

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    original_text: str
    entities: list[Entity]
    pseudonymized_text: str
    similarity: dict
    mapping: MappingStore
    claude_response: str | None = None
    deanonymized_report: str | None = None
    metrics: MetricsReport | None = None


def run_pipeline(
    input_text: str,
    *,
    task_prompt: str | None = None,
    use_prompt_detection: bool = True,
    rewrite_fluency: bool = True,
    skip_claude: bool = False,
    mapping_output_path: Path | None = None,
) -> PipelineResult:
    """Run the full pseudonymization pipeline.

    Args:
        input_text: Raw sensitive text to pseudonymize.
        task_prompt: Task instruction for Claude. Defaults to config.DEFAULT_TASK_PROMPT.
        use_prompt_detection: Whether to use Qwen for supplementary entity detection.
        rewrite_fluency: Whether to rewrite sentences for fluency after replacement.
        skip_claude: If True, skip sending to Claude (useful for testing).
        mapping_output_path: Optional path to save the mapping JSON.
    """
    # --- Stage 1: Detection ---
    logger.info("Stage 1: Detecting entities...")
    entities = detect_entities(input_text, use_prompt=use_prompt_detection)
    logger.info("Detected %d entities", len(entities))
    for e in entities:
        logger.debug("  %s [%s] @ %d-%d", e.text, e.label, e.start_char, e.end_char)

    # --- Stage 2: Generation ---
    logger.info("Stage 2: Generating pseudonyms...")
    mapping = MappingStore()
    mapping = generate_pseudonyms(entities, mapping)
    logger.info("Generated %d mappings", len(mapping.mappings))

    # --- Stage 3: Replacement ---
    logger.info("Stage 3: Replacing entities...")
    pseudonymized_text = replace_entities(input_text, mapping, rewrite_fluency=rewrite_fluency)

    # --- QA Gate: Similarity Check ---
    logger.info("QA Gate: Computing similarity...")
    similarity = compute_similarity(input_text, pseudonymized_text)
    logger.info(
        "Similarity: mean=%.3f, min=%.3f, passes=%s",
        similarity["mean_similarity"],
        similarity["min_similarity"],
        similarity["passes_threshold"],
    )

    # Save mapping
    if mapping_output_path:
        mapping.save(mapping_output_path)
        logger.info("Mapping saved to %s", mapping_output_path)

    result = PipelineResult(
        original_text=input_text,
        entities=entities,
        pseudonymized_text=pseudonymized_text,
        similarity=similarity,
        mapping=mapping,
    )

    # --- Send to Claude ---
    if not skip_claude:
        logger.info("Sending pseudonymized text to Claude...")
        try:
            claude_response = send_to_claude(pseudonymized_text, task_prompt)
            result.claude_response = claude_response

            # --- De-anonymize ---
            logger.info("De-anonymizing Claude's response...")
            result.deanonymized_report = deanonymize(claude_response, mapping)
        except Exception as e:
            logger.error("Claude interaction failed: %s", e)
            result.claude_response = None
            result.deanonymized_report = None

    # --- Metrics ---
    logger.info("Computing metrics...")
    result.metrics = compute_all_metrics(
        original_text=input_text,
        pseudonymized_text=pseudonymized_text,
        deanonymized_text=result.deanonymized_report,
        mapping=mapping,
    )

    return result
