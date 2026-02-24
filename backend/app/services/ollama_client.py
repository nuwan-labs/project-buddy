"""
Ollama HTTP client for DeepSeek R1 end-of-day analysis.

All functions are synchronous (run in the scheduler background thread or
called directly from an async FastAPI route via a thread executor).
"""
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import requests

from app.config import get_settings

if TYPE_CHECKING:
    from app.models import ActivityLog

logger   = logging.getLogger(__name__)
settings = get_settings()


# ─────────────────────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────────────────────

def check_ollama_health() -> dict:
    """Test connectivity and model availability.  Never raises — always returns a dict."""
    base = settings.ollama_base_url
    try:
        r = requests.get(f"{base}/api/version", timeout=5)
        if r.status_code != 200:
            return {"available": False, "error": f"HTTP {r.status_code}"}
        version = r.json().get("version", "unknown")

        r2     = requests.get(f"{base}/api/tags", timeout=5)
        models = [m.get("name", "") for m in r2.json().get("models", [])]
        model_ok = any(settings.ollama_model in m for m in models)

        return {
            "available":    True,
            "version":      version,
            "model":        settings.ollama_model,
            "model_loaded": model_ok,
            "models":       models,
        }
    except requests.exceptions.ConnectionError:
        return {"available": False, "error": "Cannot connect to Ollama"}
    except Exception as exc:
        return {"available": False, "error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# Prompt formatting
# ─────────────────────────────────────────────────────────────────────────────

def _format_logs(logs: list[ActivityLog]) -> str:
    parts = []
    for log in logs:
        project  = log.project.name  if log.project  else "Unknown Project"
        activity = log.activity.name if log.activity else "Ad-hoc / Unplanned"
        parts.append(
            f"  {log.timestamp[:16]}  |  {project} → {activity}\n"
            f"    Comment:  {log.comment}\n"
            f"    Duration: {log.duration_minutes} min"
        )
    return "\n\n".join(parts)


_PROMPT_TEMPLATE = """\
You are analyzing a bioinformatics researcher's daily work log. Today is {date}.

Work Log:
{logs}

Analyze the work log and respond with ONLY valid JSON — no markdown fences, \
no preamble, no text outside the JSON object.

JSON format:
{{
  "summary": "2-3 sentence overview of today's accomplishments",
  "blockers": [
    {{"issue": "description", "frequency": 1, "suggestion": "how to resolve"}}
  ],
  "highlights": [
    "key accomplishment 1",
    "key accomplishment 2"
  ],
  "suggestions": [
    {{"project": "project name", "next_step": "recommended action", "rationale": "why"}}
  ],
  "patterns": [
    "observed work pattern 1"
  ]
}}
"""


# ─────────────────────────────────────────────────────────────────────────────
# Response parsing
# ─────────────────────────────────────────────────────────────────────────────

_EMPTY_RESULT: dict = {
    "summary":     "",
    "blockers":    [],
    "highlights":  [],
    "suggestions": [],
    "patterns":    [],
}


def _parse_response(text: str) -> dict:
    """Extract and parse JSON from DeepSeek's response.

    DeepSeek R1 sometimes wraps its output in <think>…</think> tags.
    We strip those before looking for the JSON object.
    """
    # Remove <think>…</think> reasoning block if present
    if "<think>" in text and "</think>" in text:
        end_tag = text.rfind("</think>")
        text = text[end_tag + len("</think>"):]

    # Find outermost JSON object
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start == -1 or end <= start:
        raise ValueError("No JSON object found in Ollama response")

    return json.loads(text[start:end])


# ─────────────────────────────────────────────────────────────────────────────
# Main analysis function
# ─────────────────────────────────────────────────────────────────────────────

def analyze_daily_logs(analysis_date: str, logs: list[ActivityLog]) -> dict:
    """Send today's activity logs to DeepSeek R1 and return structured analysis.

    Args:
        analysis_date: ISO 8601 date string (YYYY-MM-DD).
        logs:          List of ActivityLog ORM objects for that date
                       (must have ``.project`` and ``.activity`` relationships loaded).

    Returns:
        Dict with keys: ``summary``, ``blockers``, ``highlights``,
        ``suggestions``, ``patterns``.

    Raises:
        requests.exceptions.ConnectionError  if Ollama is unreachable.
        requests.exceptions.Timeout          if the request exceeds the configured timeout.
        Exception                            for other unexpected errors.
    """
    if not settings.ollama_analysis_enabled:
        logger.info("Ollama analysis disabled — skipping.")
        return {**_EMPTY_RESULT, "summary": "Analysis is disabled in configuration."}

    if not logs:
        return {**_EMPTY_RESULT, "summary": f"No activity logs for {analysis_date}."}

    prompt = _PROMPT_TEMPLATE.format(
        date=analysis_date,
        logs=_format_logs(logs),
    )

    logger.info("Sending %d log(s) to Ollama (%s) for date %s …",
                len(logs), settings.ollama_model, analysis_date)

    response = requests.post(
        f"{settings.ollama_base_url}/api/generate",
        json={
            "model":  settings.ollama_model,
            "prompt": prompt,
            "stream": False,
        },
        timeout=settings.ollama_timeout,
    )
    response.raise_for_status()

    raw_text = response.json().get("response", "")
    logger.debug("Raw Ollama response (%d chars): %.200s …", len(raw_text), raw_text)

    try:
        result = _parse_response(raw_text)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Could not parse Ollama JSON: %s — returning raw summary.", exc)
        return {
            **_EMPTY_RESULT,
            "summary": raw_text[:1000] if raw_text else "Analysis complete (unparseable response).",
        }

    logger.info("Ollama analysis for %s completed successfully.", analysis_date)
    return result
