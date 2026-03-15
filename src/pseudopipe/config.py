"""Configuration constants, thresholds, and model names."""

from __future__ import annotations

# --- NER Configuration ---
SPACY_MODEL = "en_core_web_sm"
NER_ENTITY_LABELS = {"PERSON", "ORG", "MONEY", "CARDINAL", "PERCENT", "GPE", "LOC"}

# Domain-specific entities that no general NER will detect
CUSTOM_ENTITIES: dict[str, str] = {
    "Project Moonbeam": "PROJECT",
    "TurboMold 3000": "MACHINE",
}

# Regex patterns for financial metrics (matched by EntityRuler)
FINANCIAL_PATTERNS = [
    {"label": "MONEY", "pattern": [{"TEXT": {"REGEX": r"^\$\d+(\.\d+)?$"}}, {"LOWER": {"IN": ["m", "b", "k", "million", "billion", "thousand"]}}]},
    {"label": "FINANCIAL_METRIC", "pattern": [{"LOWER": {"IN": ["arr", "mrr", "ebitda"]}}]},
]

# --- Qwen / Ollama Configuration ---
OLLAMA_MODEL = "qwen3.5:2b"
OLLAMA_HOST = "http://localhost:11434"

# --- Generation Configuration ---
MONEY_SCALE_RANGE = (0.7, 1.3)

# Fallback fictional names when Ollama is unavailable
FALLBACK_PERSON_NAMES = [
    "Alex Morgan", "Jordan Rivera", "Casey Liu", "Taylor Brooks",
    "Morgan Ellis", "Jamie Santos", "Riley Chen", "Avery Walsh",
]
FALLBACK_ORG_NAMES = [
    "Brightline Corp.", "Meridian Industries", "Apex Dynamics",
    "Summit Solutions", "Pinnacle Group", "Evergreen Ltd.",
]
FALLBACK_PROJECT_NAMES = [
    "Project Starlight", "Project Aurora", "Project Catalyst",
    "Project Horizon", "Project Velocity",
]
FALLBACK_MACHINE_NAMES = [
    "HyperForge X1", "NovaCast 500", "PrecisionMax 2000",
    "UltraPress 750", "FlexForm 100",
]
FALLBACK_LOCATION_NAMES = [
    "Silverton", "Clearwater", "Maple Ridge", "Ironbridge",
    "Westbrook", "Ashford", "Pinehaven", "Stonewall",
]

# --- Similarity / QA Gate ---
SIMILARITY_MODEL = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.65

# --- Metrics ---
METRICS_EMBEDDING_MODEL = "all-mpnet-base-v2"

# --- Claude CLI ---
CLAUDE_SYSTEM_PROMPT = (
    "You are a business analyst. Generate a concise executive summary report "
    "based on the provided memo. Focus on financial performance, strategic "
    "initiatives, and key risks. Use professional tone."
)
CLAUDE_MAX_BUDGET = 0.50
CLAUDE_TIMEOUT = 180
CLAUDE_MAX_INPUT_BYTES = 90_000

# --- Pipeline ---
DEFAULT_TASK_PROMPT = (
    "Analyze the following internal memo and produce a structured executive summary "
    "with sections: Financial Overview, Strategic Initiatives, Key Risks, and Outlook."
)
