"""Small, dependency-free battery ledger and router primitives for AI providers.

This module never calls a provider, never reads secret values, and never assumes
quota percentages are available. Callers pass only observed outcomes.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LEDGER_PATH = Path(os.environ.get("AI_BATTERY_LEDGER", "ai-battery-status.json"))
PROVIDERS = ("gemini", "groq", "openrouter")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def classify_error(message: str) -> tuple[str, str | None]:
    """Return (status, HTTP code); only infer what the error explicitly says."""
    text = str(message or "")
    match = re.search(r"HTTP\s+(\d{3})", text, re.IGNORECASE)
    code = match.group(1) if match else None
    lowered = text.lower()
    if code in {"429", "402"} or any(x in lowered for x in ("rate limit", "quota exceeded", "resource exhausted")):
        return "LOW_OR_COOLDOWN", code
    if code in {"401", "403"} or any(x in lowered for x in ("invalid api key", "unauthorized", "permission denied")):
        return "DISCONNECTED", code
    if "timed out" in lowered or "timeout" in lowered or code in {"500", "502", "503", "504"}:
        return "ERROR", code
    return "ERROR", code


def empty_ledger() -> dict[str, Any]:
    return {"schema_version": 1, "updated_at": None, "providers": {}}


def load_ledger(path: Path = LEDGER_PATH) -> dict[str, Any]:
    if not path.exists():
        return empty_ledger()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("schema_version") != 1 or not isinstance(value.get("providers"), dict):
            return empty_ledger()
        return value
    except (OSError, ValueError, TypeError):
        return empty_ledger()


def record_event(
    ledger: dict[str, Any],
    provider: str,
    outcome: str,
    *,
    model: str | None = None,
    error: str | None = None,
    reset_at: str | None = None,
    free_route: str = "unknown",
    configured: bool | None = None,
    now: str | None = None,
) -> dict[str, Any]:
    """Update one provider without persisting secrets or raw error bodies."""
    if provider not in PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")
    valid = {"success", "quota", "auth_error", "timeout", "service_error", "missing_config", "unknown_error"}
    if outcome not in valid:
        raise ValueError(f"Unsupported outcome: {outcome}")
    status_map = {
        "success": "AVAILABLE",
        "quota": "LOW_OR_COOLDOWN",
        "auth_error": "DISCONNECTED",
        "timeout": "ERROR",
        "service_error": "ERROR",
        "missing_config": "DISCONNECTED",
        "unknown_error": "ERROR",
    }
    previous = ledger.setdefault("providers", {}).get(provider, {})
    safe_error = None
    if error:
        # Never persist raw provider bodies: retain only a short category-like message.
        status, http_code = classify_error(error)
        if outcome == "unknown_error":
            status_map[outcome] = status
        safe_error = f"HTTP {http_code}" if http_code else status.lower().replace("_", " ")
    item = {
        "status": status_map[outcome],
        "checked_at": now or utc_now(),
        "last_outcome": outcome,
        "last_success_at": (now or utc_now()) if outcome == "success" else previous.get("last_success_at"),
        "model": model or previous.get("model"),
        "http_or_error_category": safe_error,
        "reset_at": reset_at,
        "free_route": free_route,
        "configured": configured if configured is not None else previous.get("configured", "unknown"),
        "quota_remaining": "not exposed",
        "note": "AVAILABLE means a recent call succeeded; remaining quota may still be unknown.",
    }
    ledger["providers"][provider] = item
    ledger["updated_at"] = now or utc_now()
    return ledger


def route_candidates(
    candidates: list[str],
    ledger: dict[str, Any],
    *,
    free_only: bool = True,
) -> list[str]:
    """Prefer recently usable providers; exclude known cooldown/disconnected/paid routes."""
    allowed = []
    providers = ledger.get("providers", {})
    for name in candidates:
        if name not in PROVIDERS:
            continue
        item = providers.get(name, {})
        status = item.get("status", "UNKNOWN")
        free_route = item.get("free_route", "unknown")
        if status in {"LOW_OR_COOLDOWN", "DISCONNECTED", "PAID_ROUTE_BLOCKED"}:
            continue
        if free_only and free_route != "verified_zero_price":
            continue
        allowed.append(name)
    # Keep caller's suitability ranking; this helper only removes ineligible options.
    return allowed



def run_task_with_fallback(
    task_name: str,
    candidates: list[str],
    handlers: dict[str, Any],
    ledger: dict[str, Any],
    *,
    free_only: bool = True,
) -> tuple[str, Any]:
    """Run one task on the first eligible provider; fail over once per candidate.

    Handlers are callables that accept no arguments. Their provider/model configuration
    must already be verified by the caller. Exceptions are reduced to safe categories
    in the ledger; raw exception text is not persisted.
    """
    eligible = route_candidates(candidates, ledger, free_only=free_only)
    failures: list[str] = []
    for provider in eligible:
        handler = handlers.get(provider)
        if not callable(handler):
            continue
        try:
            result = handler()
            record_event(
                ledger, provider, "success",
                model=ledger.get("providers", {}).get(provider, {}).get("model"),
                free_route=ledger.get("providers", {}).get(provider, {}).get("free_route", "unknown"),
            )
            return provider, result
        except Exception as exc:
            status, code = classify_error(str(exc))
            outcome = {
                "LOW_OR_COOLDOWN": "quota",
                "DISCONNECTED": "auth_error",
                "ERROR": "unknown_error",
            }[status]
            record_event(
                ledger, provider, outcome, error=str(exc),
                model=ledger.get("providers", {}).get(provider, {}).get("model"),
                free_route=ledger.get("providers", {}).get(provider, {}).get("free_route", "unknown"),
            )
            failures.append(f"{provider}: {status}" + (f" (HTTP {code})" if code else ""))
    detail = "; ".join(failures) if failures else "no eligible configured handlers"
    raise RuntimeError(f"No eligible provider completed task '{task_name}': {detail}")

def save_ledger(ledger: dict[str, Any], path: Path = LEDGER_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def render_markdown(ledger: dict[str, Any]) -> str:
    lines = [
        "# AI Battery Status",
        "",
        f"Updated: {ledger.get('updated_at') or 'not checked'}",
        "",
        "> Quota percentages are intentionally omitted unless a provider exposes reliable values.",
        "",
        "| Provider | Status | Last checked | Last success | Model | Free route | Quota remaining | Reset |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name in PROVIDERS:
        item = ledger.get("providers", {}).get(name, {})
        lines.append(
            "| {name} | {status} | {checked} | {success} | {model} | {free} | {quota} | {reset} |".format(
                name=name,
                status=item.get("status", "UNKNOWN"),
                checked=item.get("checked_at", "not checked"),
                success=item.get("last_success_at", "unknown"),
                model=item.get("model", "unknown"),
                free=item.get("free_route", "unknown"),
                quota=item.get("quota_remaining", "not exposed"),
                reset=item.get("reset_at") or "unknown",
            )
        )
    lines.extend(["", "No provider was called to generate this report. Status reflects only recorded observations.", ""])
    return "\n".join(lines)


def main() -> None:
    ledger = load_ledger()
    # Show configuration presence only; never read or print secret values.
    for name, env_name in (
        ("gemini", "GEMINI_API_KEY"),
        ("groq", "GROQ_API_KEY"),
        ("openrouter", "OPENROUTER_API_KEY"),
    ):
        if name not in ledger.get("providers", {}):
            configured = bool(os.environ.get(env_name, "").strip())
            record_event(
                ledger, name, "unknown_error" if configured else "missing_config",
                error="not tested" if configured else None,
                configured=configured,
                free_route="unknown",
            )
            # Configured is not the same as healthy or quota-available.
            if configured:
                ledger["providers"][name]["status"] = "UNKNOWN"
                ledger["providers"][name]["last_outcome"] = "not_tested"
                ledger["providers"][name]["http_or_error_category"] = None
    save_ledger(ledger)
    report = render_markdown(ledger)
    Path("ai-battery-status.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
