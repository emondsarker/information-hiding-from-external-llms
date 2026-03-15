"""CLI entry point: python -m pseudopipe <file>"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from pseudopipe.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pseudopipe",
        description="Pseudonymization pipeline for privacy-preserving LLM interactions.",
    )
    parser.add_argument("input_file", type=Path, help="Path to the input text file")
    parser.add_argument(
        "--skip-claude", action="store_true",
        help="Skip sending to Claude (local pseudonymization only)",
    )
    parser.add_argument(
        "--no-prompt-detection", action="store_true",
        help="Disable Qwen-based prompt detection (NER only)",
    )
    parser.add_argument(
        "--no-fluency-rewrite", action="store_true",
        help="Disable Qwen-based fluency rewriting",
    )
    parser.add_argument(
        "--mapping-output", type=Path, default=None,
        help="Path to save the mapping JSON file",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if not args.input_file.exists():
        print(f"Error: File not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    input_text = args.input_file.read_text()

    result = run_pipeline(
        input_text,
        use_prompt_detection=not args.no_prompt_detection,
        rewrite_fluency=not args.no_fluency_rewrite,
        skip_claude=args.skip_claude,
        mapping_output_path=args.mapping_output,
    )

    # --- Output ---
    print("\n" + "=" * 70)
    print("PSEUDONYMIZATION PIPELINE RESULTS")
    print("=" * 70)

    print(f"\nEntities detected: {len(result.entities)}")
    print(f"Mappings created: {len(result.mapping.mappings)}")

    print("\n--- Entity Mappings ---")
    for entry in result.mapping.mappings:
        extra = f" (scale={entry.scale_factor:.2f})" if entry.scale_factor else ""
        print(f"  [{entry.label}] {entry.original!r} → {entry.pseudonym!r}{extra}")

    print("\n--- Similarity QA Gate ---")
    print(f"  Mean similarity: {result.similarity['mean_similarity']:.3f}")
    print(f"  Min similarity:  {result.similarity['min_similarity']:.3f}")
    print(f"  Passes threshold ({result.similarity.get('passes_threshold', 'N/A')})")

    print("\n--- Pseudonymized Text ---")
    print(result.pseudonymized_text)

    if result.claude_response:
        print("\n--- Claude Response (Pseudonymized) ---")
        print(result.claude_response[:2000])

    if result.deanonymized_report:
        print("\n--- De-anonymized Report ---")
        print(result.deanonymized_report[:2000])

    if result.metrics:
        print("\n--- Metrics ---")
        for key, value in result.metrics.to_dict().items():
            if value is not None:
                print(f"  {key}: {value:.4f}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
