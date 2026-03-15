# PseudoPipe

A pseudonymization pipeline that lets you use external LLMs on sensitive documents without exposing private data.

## How It Works

```
Sensitive Document
       │
       ▼
 ┌─ DETECT ──────────────────────────────────────────────┐
 │  spaCy NER + regex find all entities:                 │
 │  names, orgs, money, locations, emails, etc.          │
 └───────────────────────────────────────────────────────┘
       │
       ▼
 ┌─ PSEUDONYMIZE ───────────────────────────────────────┐
 │  "John Harrison" → "Casey Liu"                       │
 │  "ToyMakers Inc." → "Apex Dynamics"                  │
 │  "$42M" → "$44.1M"  (scaled 0.7x–1.3x)              │
 │  "rtorres@toymakers.com" → "user714@example.com"     │
 │                                                       │
 │  Two-pass marker replacement prevents collisions.     │
 │  Mapping stored for later reversal.                   │
 └───────────────────────────────────────────────────────┘
       │
       ▼
 ┌─ LLM ────────────────────────────────────────────────┐
 │  Claude receives sanitized text only.                 │
 │  It analyzes "Apex Dynamics" — never sees the real    │
 │  company, names, or financials.                       │
 └───────────────────────────────────────────────────────┘
       │
       ▼
 ┌─ DE-ANONYMIZE ───────────────────────────────────────┐
 │  Reverse the mapping in Claude's response:            │
 │  "Casey Liu" → "John Harrison"                       │
 │  "Apex Dynamics" → "ToyMakers Inc."                  │
 │  "$44.1M" → "$42M"                                   │
 └───────────────────────────────────────────────────────┘
       │
       ▼
  Final Report
  (real names restored, private data never left your machine)
```

The result is a report that is **93.5% identical** (BERTScore) to what the LLM would produce on the raw original. See [REPORT.md](REPORT.md) for the full evaluation.

## Setup

**Requirements:** Python 3.11+, [uv](https://docs.astral.sh/uv/) (recommended) or pip, and the [Claude CLI](https://docs.anthropic.com/en/docs/claude-cli) installed and authenticated.

### Quick Start

```bash
# Clone and install
git clone <repo-url> && cd information-hiding
make install        # installs package + spaCy model

# Or with uv directly
uv sync
uv run python -m spacy download en_core_web_sm
```

### Development

```bash
make dev            # install with dev dependencies
make test           # run test suite (63 tests)
make lint           # check code style
make format         # auto-format
```

### Optional: Local LLM (Ollama + Qwen)

For LLM-generated pseudonyms (culturally matched names, contextual replacements) instead of deterministic fallbacks:

```bash
# Install Ollama: https://ollama.com/download
ollama pull qwen3.5:2b
```

The pipeline works fully without Ollama — it falls back to built-in name lists.

## Usage

### CLI

```bash
# Full pipeline: pseudonymize → Claude → de-anonymize
python -m pseudopipe sample_data/toymakers_memo.txt

# Local-only (skip Claude, just pseudonymize)
python -m pseudopipe sample_data/toymakers_memo.txt --skip-claude

# NER-only detection (no Qwen prompt detection)
python -m pseudopipe sample_data/toymakers_memo.txt --no-prompt-detection

# Save the entity mapping to a file
python -m pseudopipe sample_data/toymakers_memo.txt --mapping-output mappings.json

# Verbose logging
python -m pseudopipe sample_data/toymakers_memo.txt -v
```

### Comparative Report

Run the head-to-head evaluation (same input through pipeline vs direct to Claude):

```bash
python generate_report.py
```

This produces `pipeline_report.txt` with both paths side-by-side and comparison metrics.

### As a Library

```python
from pathlib import Path
from pseudopipe.pipeline import run_pipeline

text = Path("my_confidential_memo.txt").read_text()

result = run_pipeline(
    text,
    use_prompt_detection=False,   # skip Qwen-based detection
    rewrite_fluency=False,        # skip Qwen-based fluency rewrite
    skip_claude=False,            # set True to pseudonymize only
    mapping_output_path=Path("mapping.json"),
)

print(result.pseudonymized_text)      # sanitized version
print(result.deanonymized_report)     # final report with real names restored
print(result.metrics.to_dict())       # evaluation metrics
```

## Project Structure

```
src/pseudopipe/
├── config.py          # thresholds, model names, fallback lists
├── detection.py       # entity detection (spaCy NER + regex emails)
├── generation.py      # pseudonym generation (Qwen or fallback)
├── replacement.py     # two-pass marker-based text replacement
├── similarity.py      # cosine similarity QA gate
├── external_llm.py    # Claude CLI subprocess wrapper
├── deanonymizer.py    # reverse mapping with numeric boundary guards
├── mapping.py         # bidirectional mapping store (JSON serializable)
├── metrics.py         # PRR, PPS, BERTScore, ROUGE, semantic drift
├── pipeline.py        # orchestrator wiring all stages together
└── __main__.py        # CLI entrypoint

tests/                 # 63 tests covering all modules
sample_data/           # example confidential memo
generate_report.py     # head-to-head evaluation script
REPORT.md              # full evaluation report with results
```

## Tests

```bash
make test
# or
uv run pytest tests/ -v
```

63 tests cover entity detection, pseudonym generation, replacement collision prevention, de-anonymization, mapping persistence, similarity checking, and all evaluation metrics.
