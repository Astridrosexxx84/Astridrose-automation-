"""Coordinate several free-tier AI providers. Analysis only; never publishes."""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from ai_battery import empty_ledger, record_event, save_ledger, run_task_with_fallback

GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/" + GEMINI_MODEL + ":generateContent"


def request_json(url, method="GET", payload=None, headers=None, timeout=180):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request_headers = {"User-Agent": "AstridRoseAI-Team/1.0 (+https://github.com/Astridrosexxx84/Astridrose-automation-)"}
    request_headers.update(headers or {})
    request = urllib.request.Request(url, data=data, method=method, headers=request_headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1200]
        raise RuntimeError(f"API returned HTTP {exc.code}: {detail}") from exc
    except TimeoutError as exc:
        raise RuntimeError(f"API request timed out after {timeout} seconds.") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network request failed: {exc.reason}") from exc


def gemini(prompt, api_key):
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 1200},
    }
    result = None
    for attempt in range(3):
        try:
            result = request_json(
                GEMINI_ENDPOINT,
                method="POST",
                headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
                payload=payload,
                timeout=180,
            )
            break
        except RuntimeError as exc:
            message = str(exc)
            # A 429 is a quota/cooldown signal: do not hammer the same provider.\n            # Let the coordinator preserve this failure and use an eligible fallback.\n            transient = "HTTP 503" in message or "timed out" in message.lower()
            if not transient or attempt == 2:
                raise
            delay = 2 ** (attempt + 1)
            print(f"Gemini transient error; retrying in {delay}s (attempt {attempt + 2}/3): {message[:180]}")
            time.sleep(delay)
    candidates = result.get("candidates", []) if result else []
    if not candidates:
        raise RuntimeError("Gemini returned no answer.")
    parts = candidates[0].get("content", {}).get("parts", [])
    answer = "\n".join(p.get("text", "") for p in parts if p.get("text"))
    if not answer.strip():
        raise RuntimeError("Gemini returned an empty answer.")
    return answer.strip()


def openai_compatible_chat(url, api_key, model_id, prompt, title):
    result = request_json(
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Title": title,
        },
        payload={
            "model": model_id,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an independent analyst. Be candid and practical, respect the $0 budget, do not claim web research, and never publish content or change external accounts.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.6,
            "max_tokens": 1200,
        },
    )
    choices = result.get("choices", [])
    if not choices:
        raise RuntimeError(f"Model {model_id} returned no answer.")
    answer = choices[0].get("message", {}).get("content", "")
    if isinstance(answer, list):
        answer = "\n".join(item.get("text", "") for item in answer if isinstance(item, dict))
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError(f"Model {model_id} returned an empty answer.")
    return answer.strip()


def choose_free_openrouter_models(limit=3):
    """Return distinct models only when the live catalogue lists zero prices."""
    result = request_json("https://openrouter.ai/api/v1/models")
    free_models = []
    for model in result.get("data", []):
        model_id = model.get("id", "")
        pricing = model.get("pricing", {})
        try:
            is_free = (
                model_id.endswith(":free")
                and float(pricing.get("prompt", "1")) == 0
                and float(pricing.get("completion", "1")) == 0
            )
        except (TypeError, ValueError):
            is_free = False
        if is_free:
            free_models.append(model_id)
    if not free_models:
        raise RuntimeError("No listed zero-price :free OpenRouter model is available. Stopped rather than trying a paid model.")
    preferred = [
        "qwen/qwen3-4b:free",
        "google/gemma-3-27b-it:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "cohere/north-mini-code:free",
    ]
    chosen = [model_id for model_id in preferred if model_id in free_models]
    chosen.extend(model_id for model_id in sorted(free_models) if model_id not in chosen)
    return chosen[:max(1, limit)]

def choose_groq_model(api_key):
    result = request_json(
        "https://api.groq.com/openai/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    available = [item.get("id", "") for item in result.get("data", []) if item.get("id")]
    if not available:
        raise RuntimeError("Groq returned no available models.")
    preferred = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    for model_id in preferred:
        if model_id in available:
            return model_id
    return sorted(available)[0]


def main():
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    # Gemini/Groq stay disabled unless free-tier-only access is explicitly confirmed.
    allow_gemini = os.environ.get("ALLOW_GEMINI_FREE_TIER_CALLS", "").strip().lower() == "true"
    allow_groq = os.environ.get("ALLOW_GROQ_FREE_TIER_CALLS", "").strip().lower() == "true"
    task = os.environ.get("AI_TEAM_TASK", "").strip()
    # OpenRouter is gated separately by a live zero-price :free model listing.
    usable_count = sum((bool(openrouter_key), bool(gemini_key and allow_gemini), bool(groq_key and allow_groq)))
    report_only_mode = not usable_count
    if report_only_mode:
        print("No provider route is enabled. Continuing in report-only mode; no external AI calls will be made.")
    missing = [
        name for name, value in [
            ("GEMINI_API_KEY", gemini_key),
            ("GROQ_API_KEY", groq_key),
            ("OPENROUTER_API_KEY", openrouter_key),
        ] if not value
    ]
    if missing:
        print("Optional providers not configured; continuing without them: " + ", ".join(missing))
    if gemini_key and not allow_gemini:
        print("Gemini key detected but calls are disabled until free-tier-only access is confirmed.")
    if groq_key and not allow_groq:
        print("Groq key detected but calls are disabled until free-tier-only access is confirmed.")
    if not task:
        task = "Design one practical $0-upfront experiment for the Astrid Rose creator business. Focus on a repeatable workflow, measurable demand, and free tools. Do not create or publish actual content."
    task = task[:4000]

    print("AI team starting: Gemini analysis, Groq challenge, OpenRouter challenge, Gemini synthesis.")
    battery = empty_ledger()
    for provider, key in (("gemini", gemini_key), ("groq", groq_key), ("openrouter", openrouter_key)):
        if not key:
            record_event(battery, provider, "missing_config", configured=False, free_route="unknown")
        else:
            # A configured key is not evidence of remaining quota or a healthy connection.
            battery["providers"][provider] = {
                "status": "UNKNOWN", "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "last_outcome": "not_tested", "last_success_at": None, "model": None,
                "http_or_error_category": None, "reset_at": None, "free_route": "unknown",
                "configured": True, "quota_remaining": "not exposed",
                "note": "Credentials are configured; provider health and remaining quota have not yet been verified.",
            }
    battery["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if gemini_key and allow_gemini:
        try:
            first = gemini(
                "Analyze this $0-upfront creator automation task. Give the objective, assumptions, three options, best first experiment, risks, and measurable success criteria. Label facts needing current research. Do not publish anything.\n\nTASK:\n" + task,
                gemini_key,
            )
            record_event(battery, "gemini", "success", model=GEMINI_MODEL, free_route="unknown", configured=True)
            print("Gemini first pass complete.")
        except RuntimeError as exc:
            record_event(battery, "gemini", "unknown_error", error=str(exc), model=GEMINI_MODEL, free_route="unknown", configured=True)
            first = "Gemini initial analysis unavailable: " + str(exc)
            print("Gemini unavailable; continuing with other providers: " + str(exc))
    else:
        first = "Gemini skipped: no API key configured." if not gemini_key else "Gemini skipped: free-tier-only calls are not explicitly enabled."

    # A provider access error should not prevent the other free providers from contributing.
    # Keep the exact failure in the report so it can be diagnosed without exposing credentials.
    groq_model = "unavailable"
    if groq_key and allow_groq:
        try:
            groq_model = choose_groq_model(groq_key)
            groq_answer = openai_compatible_chat(
                "https://api.groq.com/openai/v1/chat/completions",
                groq_key,
                groq_model,
                "Independently analyze the task. Challenge assumptions, find failure modes, and suggest a different high-value $0 experiment. Do not invent current facts or claim web research.\n\nTASK:\n" + task,
                "Astrid Rose AI Team - Groq",
            )
            record_event(battery, "groq", "success", model=groq_model, free_route="unknown", configured=True)
            print(f"Groq independent challenge complete: {groq_model}")
        except RuntimeError as exc:
            record_event(battery, "groq", "unknown_error", error=str(exc), free_route="unknown", configured=True)
            groq_model = "unavailable"
            groq_answer = "Groq contribution unavailable. Diagnostic: " + str(exc)
            print("Groq unavailable; continuing with other providers: " + str(exc))
    else:
        groq_answer = "Groq skipped: no API key configured." if not groq_key else "Groq skipped: free-tier-only calls are not explicitly enabled."

    openrouter_models = []
    openrouter_model = "unavailable"
    openrouter_answers = []
    if openrouter_key:
        try:
            openrouter_models = choose_free_openrouter_models(limit=3)
            for model_id in openrouter_models:
                try:
                    answer = openai_compatible_chat(
                        "https://openrouter.ai/api/v1/chat/completions",
                        openrouter_key,
                        model_id,
                        "Independently analyze the task. Do not merely agree with other models. Offer another approach, challenge weak assumptions, and identify failure modes. Do not invent current facts or claim web research.\\n\\nTASK:\\n" + task,
                        "Astrid Rose AI Team - Independent model",
                    )
                    openrouter_answers.append((model_id, answer))
                    record_event(battery, "openrouter", "success", model=model_id, free_route="verified_zero_price", configured=True)
                    print(f"OpenRouter independent challenge complete: {model_id}")
                except RuntimeError as exc:
                    print(f"OpenRouter model unavailable; trying another verified free model: {model_id} ({str(exc)[:160]})")
            if openrouter_answers:
                openrouter_model = openrouter_answers[0][0]
                openrouter_answer = "\\n\\n".join(f"### {model_id}\\n{answer}" for model_id, answer in openrouter_answers)
            else:
                raise RuntimeError("All listed zero-price OpenRouter models failed to respond.")
        except RuntimeError as exc:
            record_event(battery, "openrouter", "unknown_error", error=str(exc), free_route="unknown", configured=True)
            openrouter_model = "unavailable"
            openrouter_answer = "OpenRouter contribution unavailable. Diagnostic: " + str(exc)
            print("OpenRouter unavailable; continuing with other providers: " + str(exc))
    else:
        openrouter_answer = "OpenRouter skipped: no API key configured."

    # Route synthesis only through an explicitly verified zero-price model.
    # Gemini's price/quota state is not verified by this run, so it is not an eligible route.
    synthesis_prompt = (
        "Synthesize the independent analyses into one actionable recommendation. "
        "Preserve disagreements, flag unverified claims, list next actions and risks. "
        "Respect $0 spending, do not publish, and use only the supplied material.\n\n"
        "TASK:\n" + task + "\n\nGEMINI ANALYSIS:\n" + first
        + "\n\nGROQ CHALLENGE:\n" + groq_answer
        + "\n\nOPENROUTER CHALLENGE:\n" + openrouter_answer
    )
    final = None
    synthesis_status = "AI synthesis unavailable; deterministic fallback report generated"
    try:
        provider, final = run_task_with_fallback(
            "final synthesis",
            ["openrouter"],
            {
                "openrouter": lambda: openai_compatible_chat(
                    "https://openrouter.ai/api/v1/chat/completions",
                    openrouter_key,
                    openrouter_model,
                    synthesis_prompt,
                    "Astrid Rose AI Team - OpenRouter synthesis",
                )
            },
            battery,
            free_only=True,
        )
        synthesis_status = "OpenRouter verified zero-price route"
        print(f"Final synthesis complete via {provider} ({openrouter_model}).")
    except RuntimeError as exc:
        print("No verified zero-price synthesis route completed; preserving partial work: " + str(exc))
    if final is None:
        final = (
            "No verified zero-price synthesis route completed. This deterministic fallback preserves the "
            "independent analyses below for review. Compare them manually and choose only actions consistent "
            "with the $0 budget and review-only safety constraints. No paid fallback was attempted."
        )


    report = f"""# Astrid Rose AI Team Report

Generated: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
Coordinator/researcher: Gemini {GEMINI_MODEL} (only if free-tier opt-in enabled)
Independent challenger: Groq {groq_model} (only if free-tier opt-in enabled)
Independent challenger: OpenRouter {openrouter_model}
Independent free-model panel: {", ".join(model for model, _ in openrouter_answers) or "none available"}\nFinal synthesizer: OpenRouter verified-zero-price route ({synthesis_status})
Scope: analysis only; no posts, comments, account changes, or publishing.

## Task

{task}

## Final team recommendation

{final}

## Gemini independent analysis

{first}

## Groq independent challenge

{groq_answer}

## OpenRouter independent challenge

{openrouter_answer}

## Cost and safety notes

- OpenRouter is restricted to listed models whose IDs end in :free and whose prompt/completion prices are zero. If none is available, the run stops rather than trying a paid model.
- Gemini and Groq API calls are disabled by default. Their `ALLOW_GEMINI_FREE_TIER_CALLS` / `ALLOW_GROQ_FREE_TIER_CALLS` flags must only be set to `true` after the account holder confirms the intended route is free and billing is disabled. These flags are an acknowledgement, not independent proof of zero cost.
- Free limits and model availability can change; failed requests stop the run.
- The task and intermediate analyses are sent to the providers. Do not include passwords, API keys, sensitive personal information, or confidential third-party data.
- This script only writes a report. It does not publish, comment, schedule, or modify external accounts.
"""
    save_ledger(battery)
    with open("ai-battery-status.md", "w", encoding="utf-8") as file:
        from ai_battery import render_markdown
        file.write(render_markdown(battery))
    with open("ai-team-report.md", "w", encoding="utf-8") as file:
        file.write(report)
    print("Report created: ai-team-report.md")
    print("Battery dashboard created: ai-battery-status.md")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, KeyError) as exc:
        print(f"AI team stopped safely: {exc}", file=sys.stderr)
        raise SystemExit(1)
