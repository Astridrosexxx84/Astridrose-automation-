"""Coordinate several free-tier AI providers. Analysis only; never publishes."""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

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
    result = request_json(
        GEMINI_ENDPOINT,
        method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        payload={
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 1200},
        },
    )
    candidates = result.get("candidates", [])
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


def choose_free_openrouter_model():
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
    ]
    for model_id in preferred:
        if model_id in free_models:
            return model_id
    return sorted(free_models)[0]


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
    task = os.environ.get("AI_TEAM_TASK", "").strip()
    missing = [
        name for name, value in [
            ("GEMINI_API_KEY", gemini_key),
            ("OPENROUTER_API_KEY", openrouter_key),
            ("GROQ_API_KEY", groq_key),
        ] if not value
    ]
    if missing:
        raise SystemExit("Missing GitHub Actions secrets: " + ", ".join(missing) + ". Never paste keys into source code or chat.")
    if not task:
        task = "Design one practical $0-upfront experiment for the Astrid Rose creator business. Focus on a repeatable workflow, measurable demand, and free tools. Do not create or publish actual content."
    task = task[:4000]

    print("AI team starting: Gemini analysis, Groq challenge, OpenRouter challenge, Gemini synthesis.")
    first = gemini(
        "Analyze this $0-upfront creator automation task. Give the objective, assumptions, three options, best first experiment, risks, and measurable success criteria. Label facts needing current research. Do not publish anything.\n\nTASK:\n" + task,
        gemini_key,
    )
    print("Gemini first pass complete.")

    # A provider access error should not prevent the other free providers from contributing.
    # Keep the exact failure in the report so it can be diagnosed without exposing credentials.
    try:
        groq_model = choose_groq_model(groq_key)
        groq_answer = openai_compatible_chat(
            "https://api.groq.com/openai/v1/chat/completions",
            groq_key,
            groq_model,
            "Independently analyze the task. Challenge assumptions, find failure modes, and suggest a different high-value $0 experiment. Do not invent current facts or claim web research.\n\nTASK:\n" + task,
            "Astrid Rose AI Team - Groq",
        )
        print(f"Groq independent challenge complete: {groq_model}")
    except RuntimeError as exc:
        groq_model = "unavailable"
        groq_answer = "Groq contribution unavailable. Diagnostic: " + str(exc)
        print("Groq unavailable; continuing with other providers: " + str(exc))

    try:
        openrouter_model = choose_free_openrouter_model()
        openrouter_answer = openai_compatible_chat(
            "https://openrouter.ai/api/v1/chat/completions",
            openrouter_key,
            openrouter_model,
            "Independently analyze the task. Do not merely agree with other models. Offer another approach, challenge weak assumptions, and identify failure modes. Do not invent current facts or claim web research.\n\nTASK:\n" + task,
            "Astrid Rose AI Team - OpenRouter",
        )
        print(f"OpenRouter independent challenge complete: {openrouter_model}")
    except RuntimeError as exc:
        openrouter_model = "unavailable"
        openrouter_answer = "OpenRouter contribution unavailable. Diagnostic: " + str(exc)
        print("OpenRouter unavailable; continuing with other providers: " + str(exc))

    try:
        final = gemini(
            "You are the lead coordinator. Combine three independent analyses. Preserve useful disagreements, flag unsupported certainty, and produce a recommendation, rationale, next three actions, risks, cost safeguards, and success measures. Nothing may be published or changed in an external account. Use only the task and analyses below; flag facts needing verification.\n\nTASK:\n"
            + task + "\n\nGEMINI ANALYSIS:\n" + first
            + "\n\nGROQ ANALYSIS (" + groq_model + "):\n" + groq_answer
            + "\n\nOPENROUTER ANALYSIS (" + openrouter_model + "):\n" + openrouter_answer,
            gemini_key,
        )
        print("Gemini synthesis complete.")
        synthesis_status = "completed"
    except RuntimeError as exc:
        # Keep the completed independent work even if the final Gemini call is unavailable.
        final = (
            "Gemini final synthesis unavailable: " + str(exc) +
            "\n\nFallback summary: use the Gemini initial analysis below as the baseline, "
            "then compare it with the Groq and OpenRouter challenges. Prioritize only actions "
            "that remain consistent with the $0 budget and review-only safety constraints."
        )
        synthesis_status = "unavailable; fallback report generated"
        print("Gemini synthesis unavailable; generating fallback report: " + str(exc))


    report = f"""# Astrid Rose AI Team Report

Generated: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
Coordinator/researcher: Google {GEMINI_MODEL}
Independent challenger: Groq {groq_model}
Independent challenger: OpenRouter {openrouter_model}
Final synthesizer: Google {GEMINI_MODEL} ({synthesis_status})
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
- Groq uses a model listed as available to this API account. Groq limits are account/model-specific; keep billing disabled and stop if the console indicates paid usage is required.
- Gemini uses {GEMINI_MODEL}, listed in official pricing documentation as available on the free tier when this was prepared. Keep the project on the free tier and do not enable billing for this workflow.
- Free limits and model availability can change; failed requests stop the run.
- The task and intermediate analyses are sent to the providers. Do not include passwords, API keys, sensitive personal information, or confidential third-party data.
- This script only writes a report. It does not publish, comment, schedule, or modify external accounts.
"""
    with open("ai-team-report.md", "w", encoding="utf-8") as file:
        file.write(report)
    print("Report created: ai-team-report.md")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, KeyError) as exc:
        print(f"AI team stopped safely: {exc}", file=sys.stderr)
        raise SystemExit(1)
