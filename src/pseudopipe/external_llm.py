"""Claude CLI (claude -p) subprocess wrapper."""

from __future__ import annotations

import json
import logging
import subprocess

from pseudopipe import config

logger = logging.getLogger(__name__)


def send_to_claude(pseudonymized_text: str, task_prompt: str | None = None) -> str:
    """Send pseudonymized text to Claude via `claude -p` and return the response.

    Args:
        pseudonymized_text: The pseudonymized memo text.
        task_prompt: Optional task instruction. Defaults to config.DEFAULT_TASK_PROMPT.

    Returns:
        Claude's generated report text.

    Raises:
        ValueError: If input exceeds size limit.
        RuntimeError: If claude CLI fails.
    """
    if task_prompt is None:
        task_prompt = config.DEFAULT_TASK_PROMPT

    input_text = f"{task_prompt}\n\n---\n\n{pseudonymized_text}"

    # Size check
    if len(input_text.encode("utf-8")) > config.CLAUDE_MAX_INPUT_BYTES:
        raise ValueError(
            f"Input too large: {len(input_text.encode('utf-8'))} bytes "
            f"(max {config.CLAUDE_MAX_INPUT_BYTES})"
        )

    cmd = [
        "claude", "-p",
        "--system-prompt", config.CLAUDE_SYSTEM_PROMPT,
        "--output-format", "json",
        "--max-budget-usd", str(config.CLAUDE_MAX_BUDGET),
    ]

    logger.info("Sending %d bytes to Claude CLI", len(input_text.encode("utf-8")))

    try:
        result = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=config.CLAUDE_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Claude CLI timed out after {config.CLAUDE_TIMEOUT}s")
    except FileNotFoundError:
        raise RuntimeError("Claude CLI not found. Ensure 'claude' is installed and on PATH.")

    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI failed (rc={result.returncode}): {result.stderr[:500]}")

    try:
        response = json.loads(result.stdout)
        return response["result"]
    except (json.JSONDecodeError, KeyError) as e:
        # If JSON parsing fails, try returning raw stdout
        logger.warning("Failed to parse Claude JSON output: %s", e)
        if result.stdout.strip():
            return result.stdout.strip()
        raise RuntimeError(f"Could not parse Claude response: {e}")
