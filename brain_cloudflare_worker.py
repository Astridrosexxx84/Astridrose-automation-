"""Explicit, opt-in Cloudflare Workers AI relay worker.

This provider is never included in the default auto chain. It requires account ID
and API token to be stored as GitHub Actions secrets; no credentials are read from
task packets or written to output files. The model is fixed to a smoke-tested ID.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT_MD = Path("brain-relay-packet.md")
OUT_JSON = Path("brain-relay-packet.json")
LEDGER = Path("brain-relay-status.json")
MODEL = "@cf/meta/llama-3.2-1b-instruct"


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def call_cloudflare(account_id, token, prompt):
    url = "https://api.cloudflare.com/client/v4/accounts/" + account_id + "/ai/run/" + MODEL
    payload = {
        "messages": [
            {"role": "system", "content": (
                "You are one text-only worker in Brain App's sequential relay. "
                "Continue the actual artifact, do not restart completed work. You have no repository tools. "
                "Do not claim you edited, tested, committed, or deployed anything. "
                "Separate VERIFIED ACTIONS, PROPOSED CHANGES, and NEXT ACTION. Respect the strict $0-only rule."
            )},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 1200,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "User-Agent": "Brain-App-Relay/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Do not persist provider response bodies; they can contain sensitive detail.
        raise RuntimeError("Cloudflare Workers AI HTTP " + str(exc.code)) from None
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError("Cloudflare Workers AI network/timeout error: " + type(exc).__name__) from None
    result = data.get("result") or {}
    answer = result.get("response") or result.get("output") or ""
    if not data.get("success", False):
        raise RuntimeError("Cloudflare Workers AI request was not successful.")
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("Cloudflare Workers AI returned no usable text response.")
    return answer.strip()


def main():
    task = os.environ.get("AI_RELAY_TASK", "").strip()
    role = os.environ.get("AI_RELAY_ROLE", "continue").strip().lower()
    prior = os.environ.get("AI_RELAY_PRIOR_PACKET", "").strip()
    next_worker = os.environ.get("AI_RELAY_NEXT_WORKER", "").strip()
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not task:
        raise SystemExit("Task goal is required.")
    if role not in ("create", "continue", "review"):
        raise SystemExit("Role must be create, continue, or review.")
    if len(task) > 12000 or len(prior) > 24000:
        raise SystemExit("Task or prior packet is too long; reduce it and retry.")
    if not account_id or not token:
        raise SystemExit("Cloudflare is not configured: add CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN as GitHub Actions secrets.")
    role_text = {
        "create": "Create the first concrete artifact for the goal. Make it usable, specific and self-contained.",
        "continue": "Continue and improve the existing artifact. Preserve valid prior work; do not restart from scratch.",
        "review": "Review the actual artifact for correctness, missing pieces, risks and testability; provide corrected content where possible.",
    }[role]
    prompt = (
        "GOAL / DEFINITION OF DONE:\n" + task +
        "\n\nWORKER ROLE: " + role.upper() + "\n" + role_text +
        "\n\nPRIOR HANDOFF PACKET / ACTUAL WORK SO FAR:\n" + (prior or "(No prior packet: first turn.)") +
        "\n\nOUTPUT REQUIREMENTS:\n1. Return concrete work, not only advice.\n"
        "2. State evidence honestly.\n3. End with NEXT ACTION: and one specific action.\n"
        "4. Respect the $0 constraint; never suggest paid fallback.\n"
        "5. Never claim repository changes or tests you did not perform."
    )
    started = now()
    try:
        answer = call_cloudflare(account_id, token, prompt)
        outcome, error_category = "success", None
    except Exception as exc:
        answer, outcome = "", "error"
        error_category = str(exc)[:160]
    record = {
        "schema_version": 1, "task": task, "role": role, "provider": "cloudflare",
        "model": MODEL, "started_at": started, "finished_at": now(),
        "outcome": outcome, "error_category": error_category, "prior_packet": prior,
        "worker_output": answer, "next_worker": next_worker or "Choose the next suitable verified free worker",
        "next_action": "",
    }
    if answer:
        for line in reversed(answer.splitlines()):
            if line.strip().lower().startswith("next action:"):
                record["next_action"] = line.split(":", 1)[1].strip()
                break
    OUT_JSON.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Brain App — Portable AI Relay Packet", "",
        "- **Goal:** " + task, "- **Role:** " + role,
        "- **Worker:** cloudflare / " + MODEL, "- **Status:** " + outcome, "",
    ]
    if error_category:
        lines += ["## Blocker", error_category, "", "No paid fallback was attempted.", ""]
    else:
        lines += ["## Actual worker output", answer, ""]
    lines += ["## Next action", record["next_action"] or "Review the output and choose the next worker.", ""]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    LEDGER.write_text(json.dumps({
        "schema_version": 1, "updated_at": record["finished_at"],
        "provider": "cloudflare", "model": MODEL,
        "status": "AVAILABLE" if outcome == "success" else "ERROR",
        "outcome": outcome, "error_category": error_category,
        "quota_remaining": "not queried; check Cloudflare account usage",
        "free_route": "explicit opt-in; Workers AI free allocation applies subject to account limits",
    }, indent=2) + "\n", encoding="utf-8")
    print("Relay turn: " + outcome + "; provider=cloudflare; model=" + MODEL)
    if outcome != "success":
        sys.exit(1)


if __name__ == "__main__":
    main()
