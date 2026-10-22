"""Run a sequential free-provider relay in one GitHub Actions invocation.

Each successful worker hands its packet to the next worker. Provider failures are
recorded and skipped; no paid fallback is used. The final artifact preserves all turns.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

PACKET_MD = Path("brain-relay-packet.md")
PACKET_JSON = Path("brain-relay-packet.json")
STATUS_JSON = Path("brain-relay-status.json")
PROVIDERS = ("groq", "gemini", "openrouter")


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def stage_for_turn(index, total, has_packet, requested_role):
    """Return the stage and provider role for this council turn."""
    if not has_packet:
        return ("primary" if index == 0 else "recovery", requested_role)
    if index == total - 1 and index > 0:
        return "integrator", "continue"
    if index > 0:
        return "critic", "review"
    return "primary", requested_role


def main():
    task = os.environ.get("AI_RELAY_TASK", "").strip()
    selected = os.environ.get("AI_RELAY_PROVIDER", "auto").strip().lower()
    role = os.environ.get("AI_RELAY_ROLE", "continue").strip().lower()
    prior = os.environ.get("AI_RELAY_PRIOR_PACKET", "").strip()
    task_id = os.environ.get("AI_RELAY_TASK_ID", "").strip()
    project_id = os.environ.get("AI_RELAY_PROJECT_ID", "").strip()
    if not task:
        raise SystemExit("Task goal is required.")
    if selected == "auto":
        order = list(PROVIDERS)
    elif selected == "cloudflare":
        # Explicit selection only: don't consume Workers AI quota during default auto runs.
        order = ["cloudflare"]
    elif selected in PROVIDERS:
        order = [selected] + [p for p in PROVIDERS if p != selected]
    else:
        raise SystemExit("Provider must be auto, openrouter, groq, gemini, or cloudflare.")

    turns = []
    successful_packet = prior
    for index, provider in enumerate(order):
        env = os.environ.copy()
        # Distinct builder / critic / integrator roles make the providers
        # collaborate rather than repeat the same generic continuation.
        stage, stage_role = stage_for_turn(index, len(order), bool(successful_packet), role)
        env.update({
            "AI_RELAY_TASK": task,
            "AI_RELAY_PROVIDER": provider,
            "AI_RELAY_ROLE": stage_role,
            "AI_RELAY_STAGE": stage,
            "AI_RELAY_PRIOR_PACKET": successful_packet,
            "AI_RELAY_NEXT_WORKER": order[index + 1] if index + 1 < len(order) else "Final quality check and acceptance-criteria verification",
        })
        # Remove the previous turn's packet so an early worker exit (for example,
        # missing credentials) cannot be mistaken for this provider's result.
        for output_path in (PACKET_MD, PACKET_JSON, STATUS_JSON):
            try:
                output_path.unlink()
            except FileNotFoundError:
                pass
        worker_script = "brain_cloudflare_worker.py" if provider == "cloudflare" else "brain_relay_worker.py"
        completed = subprocess.run([sys.executable, worker_script], env=env, check=False)
        record = read_json(PACKET_JSON)
        if not record or record.get("provider") != provider:
            record = {
                "provider": provider,
                "outcome": "error",
                "error_category": "Worker exited without producing its own readable packet (exit code " + str(completed.returncode) + ")",
                "worker_output": "",
            }
        turns.append(record)
        print("Chain turn: provider=" + provider + "; outcome=" + str(record.get("outcome", "unknown")))
        if record.get("outcome") == "success":
            successful_packet = PACKET_MD.read_text(encoding="utf-8") if PACKET_MD.exists() else json.dumps(record, ensure_ascii=False)
        # Keep going after provider failures; each provider is attempted at most once.

    successes = [t for t in turns if t.get("outcome") == "success"]
    final = {
        "schema_version": 1,
        "task": task,
        "task_id": task_id,
        "project_id": project_id,
        "chain_order": order,
        "overall_outcome": "success" if len(successes) == len(turns) else ("partial" if successes else "error"),
        "successful_turns": len(successes),
        "total_turns": len(turns),
        "turns": turns,
        "next_action": next((t.get("next_action") for t in reversed(turns) if t.get("next_action")), "Inspect provider errors and retry only the blocked provider."),
    }
    sections = [
        "# Brain App — Sequential AI Relay",
        "",
        "- **Goal:** " + task,
        "- **Provider order:** " + " → ".join(order),
        "- **Overall status:** " + final["overall_outcome"],
        "- **Successful turns:** " + str(len(successes)) + "/" + str(len(turns)),
        "",
        "Each worker received the last successful packet. Failed providers were recorded and skipped; no paid fallback was used.",
        "",
    ]
    for i, turn in enumerate(turns, 1):
        sections += [
            "## Turn " + str(i) + ": " + str(turn.get("provider", "unknown")) + " / " + str(turn.get("model", "unavailable")),
            "",
            "- **Status:** " + str(turn.get("outcome", "unknown")),
        ]
        if turn.get("error_category"):
            sections += ["- **Blocker:** " + str(turn["error_category"])]
        if turn.get("worker_output"):
            sections += ["", str(turn["worker_output"])]
        sections += [""]
    sections += ["## Next action", "", str(final["next_action"]), ""]
    PACKET_MD.write_text("\n".join(sections), encoding="utf-8")
    PACKET_JSON.write_text(json.dumps(final, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    STATUS_JSON.write_text(json.dumps({
        "schema_version": 1,
        "status": "AVAILABLE" if successes else "ERROR",
        "outcome": final["overall_outcome"],
        "successful_turns": len(successes),
        "total_turns": len(turns),
        "providers": order,
        "quota_remaining": "not exposed by providers",
        "free_route": "provider free-tier opt-in; OpenRouter models individually verified zero-price",
    }, indent=2) + "\n", encoding="utf-8")
    print("Relay chain complete: " + str(len(successes)) + "/" + str(len(turns)) + " successful.")
    if not successes:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
