"""One-turn AI relay worker for the Brain App.

Runs exactly one worker turn, saves the full handoff packet, and never publishes.
OpenRouter is eligible only when its live catalogue confirms a :free model with
zero prompt and completion prices. Gemini/Groq require explicit free-tier opt-in.
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


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def request_json(url, *, method="GET", payload=None, headers=None, timeout=90):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req_headers = {"User-Agent": "BrainApp-Relay/0.1"}
    req_headers.update(headers or {})
    req = urllib.request.Request(url, data=data, method=method, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Do not put raw provider bodies in the persistent packet or logs.
        raise RuntimeError("Provider HTTP " + str(exc.code)) from None
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError("Provider network/timeout error: " + type(exc).__name__) from None


def openrouter_model(key):
    catalog = request_json("https://openrouter.ai/api/v1/models")
    candidates = []
    for item in catalog.get("data", []):
        model_id = item.get("id", "")
        pricing = item.get("pricing") or {}
        try:
            free = model_id.endswith(":free") and float(pricing.get("prompt", "1")) == 0 and float(pricing.get("completion", "1")) == 0
        except (TypeError, ValueError):
            free = False
        if free:
            candidates.append(model_id)
    if not candidates:
        raise RuntimeError("No currently listed OpenRouter model has verified zero prompt and completion prices.")
    preferred = [
        "qwen/qwen3-4b:free",
        "google/gemma-3-27b-it:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "cohere/north-mini-code:free",
    ]
    ordered = [m for m in preferred if m in candidates] + sorted(m for m in candidates if m not in preferred)
    # Try a bounded number; fail over only within currently verified zero-price models.
    last_error = None
    for model in ordered[:3]:
        try:
            return model
        except Exception as exc:
            last_error = exc
    return ordered[0]


def call_openrouter(key, prompt):
    catalog = request_json("https://openrouter.ai/api/v1/models")
    candidates = []
    for item in catalog.get("data", []):
        mid = item.get("id", "")
        pricing = item.get("pricing") or {}
        try:
            if mid.endswith(":free") and float(pricing.get("prompt", "1")) == 0 and float(pricing.get("completion", "1")) == 0:
                candidates.append(mid)
        except (TypeError, ValueError):
            pass
    preferred = ["qwen/qwen3-4b:free", "google/gemma-3-27b-it:free", "meta-llama/llama-3.3-70b-instruct:free", "cohere/north-mini-code:free"]
    models = [m for m in preferred if m in candidates] + sorted(m for m in candidates if m not in preferred)
    if not models:
        raise RuntimeError("No currently listed zero-price OpenRouter model. Stopped without trying a paid route.")
    last_error = None
    for model in models[:3]:
        try:
            data = request_json(
                "https://openrouter.ai/api/v1/chat/completions",
                method="POST",
                headers={"Authorization": "Bearer " + key, "Content-Type": "application/json", "X-Title": "Brain App Relay"},
                payload={"model": model, "messages": [
                    {"role": "system", "content": "You are one worker in a sequential AI relay. Continue the actual artifact in the packet, do not restart completed work, follow constraints, report what you changed, and give one precise next action. Never claim tool actions you did not perform. Never publish or change external accounts."},
                    {"role": "user", "content": prompt},
                ], "temperature": 0.3, "max_tokens": 1800},
            )
            choices = data.get("choices", [])
            answer = choices[0].get("message", {}).get("content", "") if choices else ""
            if isinstance(answer, list):
                answer = "\n".join(x.get("text", "") for x in answer if isinstance(x, dict))
            if not isinstance(answer, str) or not answer.strip():
                raise RuntimeError("Provider returned an empty answer.")
            return model, answer.strip()
        except RuntimeError as exc:
            last_error = exc
            if str(exc) in ("Provider HTTP 402", "Provider HTTP 429"):
                continue
            if str(exc) in ("Provider HTTP 401", "Provider HTTP 403"):
                raise
            continue
    raise RuntimeError("All attempted zero-price OpenRouter routes failed: " + str(last_error or "unknown failure"))


def call_groq(key, prompt):
    models_data = request_json("https://api.groq.com/openai/v1/models", headers={"Authorization": "Bearer " + key})
    ids = [x.get("id", "") for x in models_data.get("data", []) if x.get("id")]
    prefs = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    model = next((x for x in prefs if x in ids), next(iter(sorted(ids)), None))
    if not model:
        raise RuntimeError("Groq returned no available models.")
    data = request_json("https://api.groq.com/openai/v1/chat/completions", method="POST",
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        payload={"model": model, "messages":[
            {"role":"system","content":"You are one worker in a sequential AI relay. Continue the actual artifact in the packet, do not restart completed work, follow constraints, report what you changed, and give one precise next action. Never claim tool actions you did not perform."},
            {"role":"user","content":prompt}], "max_tokens":1800, "temperature":0.3})
    choices=data.get("choices", [])
    answer=choices[0].get("message",{}).get("content","") if choices else ""
    if not isinstance(answer,str) or not answer.strip(): raise RuntimeError("Groq returned an empty answer.")
    return model,answer.strip()


def call_gemini(key, prompt):
    catalog = request_json("https://generativelanguage.googleapis.com/v1beta/models?pageSize=100", headers={"x-goog-api-key":key})
    models = []
    for item in catalog.get("models", []):
        name=item.get("name","")
        methods=item.get("supportedGenerationMethods",[])
        if name.startswith("models/") and "generateContent" in methods:
            models.append(name.removeprefix("models/"))
    prefs=["gemini-2.5-flash","gemini-2.0-flash"]
    model=next((x for x in prefs if x in models),next((x for x in models if "flash" in x.lower() and "preview" not in x.lower()),None))
    if not model: raise RuntimeError("No suitable Gemini generateContent model was listed.")
    data=request_json("https://generativelanguage.googleapis.com/v1beta/models/"+model+":generateContent",
        method="POST",headers={"x-goog-api-key":key,"Content-Type":"application/json"},
        payload={"contents":[{"role":"user","parts":[{"text":"You are one worker in a sequential AI relay. Continue the actual artifact in the packet, do not restart completed work, follow constraints, report what you changed, and give one precise next action. Never claim tool actions you did not perform.\n\n"+prompt}]}],"generationConfig":{"maxOutputTokens":1800}})
    candidates=data.get("candidates",[])
    parts=candidates[0].get("content",{}).get("parts",[]) if candidates else []
    answer="\n".join(p.get("text","") for p in parts if p.get("text"))
    if not answer.strip(): raise RuntimeError("Gemini returned an empty answer.")
    return model,answer.strip()


def main():
    provider=os.environ.get("AI_RELAY_PROVIDER","openrouter").strip().lower()
    role=os.environ.get("AI_RELAY_ROLE","continue").strip().lower()
    task=os.environ.get("AI_RELAY_TASK","").strip()
    prior=os.environ.get("AI_RELAY_PRIOR_PACKET","").strip()
    next_worker=os.environ.get("AI_RELAY_NEXT_WORKER","").strip()
    if provider not in ("openrouter","groq","gemini"): raise SystemExit("Provider must be openrouter, groq, or gemini.")
    if role not in ("create","continue","review"): raise SystemExit("Role must be create, continue, or review.")
    if not task: raise SystemExit("Task goal is required.")
    if len(task)>12000 or len(prior)>24000: raise SystemExit("Task or prior packet is too long; reduce it and retry.")
    keys={"openrouter":os.environ.get("OPENROUTER_API_KEY","").strip(),"groq":os.environ.get("GROQ_API_KEY","").strip(),"gemini":os.environ.get("GEMINI_API_KEY","").strip()}
    if provider in ("groq","gemini") and os.environ.get("ALLOW_"+provider.upper()+"_FREE_TIER_CALLS","").lower()!="true":
        raise SystemExit("Stopped: free-tier opt-in is not enabled for "+provider+".")
    if not keys[provider]: raise SystemExit("Stopped: secret for "+provider+" is not configured.")
    role_text={
      "create":"Create the first concrete artifact for the goal. Make it usable, specific and self-contained.",
      "continue":"Continue and improve the existing artifact in the packet. Preserve valid prior work; do not restart from scratch.",
      "review":"Review the actual artifact for correctness, missing pieces, risks and testability. Make a corrected version where possible and list specific findings."
    }[role]
    prompt="GOAL / DEFINITION OF DONE:\n"+task+"\n\nWORKER ROLE: "+role.upper()+"\n"+role_text+"\n\nPRIOR HANDOFF PACKET / ACTUAL WORK SO FAR:\n"+(prior or "(No prior packet: this is the first turn.)")+"\n\nOUTPUT REQUIREMENTS:\n1. Return the actual artifact or concrete continuation, not only advice.\n2. State what you did and any tests/evidence honestly.\n3. End with NEXT ACTION: and one specific action for the next worker.\n4. Respect the $0 constraint; do not suggest a paid route as fallback.\n5. Do not claim that you edited GitHub or ran tests unless the workflow actually did so."
    started=now()
    try:
        if provider=="openrouter": model,answer=call_openrouter(keys[provider],prompt)
        elif provider=="groq": model,answer=call_groq(keys[provider],prompt)
        else: model,answer=call_gemini(keys[provider],prompt)
        outcome="success"; error_category=None
    except Exception as exc:
        model="unavailable"; answer=""; outcome="error"
        error_category=str(exc)[:160]
    record={"schema_version":1,"task":task,"role":role,"provider":provider,"model":model,"started_at":started,"finished_at":now(),"outcome":outcome,"error_category":error_category,"prior_packet":prior,"worker_output":answer,"next_worker":next_worker or "Choose the next suitable verified free worker","next_action":""}
    if answer:
        for line in reversed(answer.splitlines()):
            if line.strip().lower().startswith("next action:"):
                record["next_action"]=line.split(":",1)[1].strip(); break
    OUT_JSON.write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    lines=["# Brain App — Portable AI Relay Packet","",f"- **Goal:** {task}",f"- **Role:** {role}",f"- **Worker:** {provider} / {model}",f"- **Status:** {outcome}",f"- **Started:** {started}",f"- **Finished:** {record['finished_at']}",f"- **Next worker:** {record['next_worker']}",""]
    if error_category: lines += ["## Blocker",error_category,"","No paid fallback was attempted.",""]
    else: lines += ["## Actual worker output",answer,""]
    lines += ["## Next action",record["next_action"] or "Inspect the output and choose the next worker.","","## Relay rules","Continue from the actual artifact; don't redo completed work. Keep secrets out of packets. Only use verified free routes."]
    OUT_MD.write_text("\n".join(lines)+"\n",encoding="utf-8")
    ledger={"schema_version":1,"updated_at":record["finished_at"],"provider":provider,"model":model,"status":"AVAILABLE" if outcome=="success" else "ERROR","outcome":outcome,"error_category":error_category,"quota_remaining":"not exposed","free_route":"verified_zero_price" if provider=="openrouter" and outcome=="success" else ("free-tier opt-in; remaining quota unknown" if provider in ("groq","gemini") else "unknown")}
    LEDGER.write_text(json.dumps(ledger,indent=2)+"\n",encoding="utf-8")
    print("Relay turn: "+outcome+"; provider="+provider+"; model="+model)
    print("Saved brain-relay-packet.md, brain-relay-packet.json, brain-relay-status.json")
    if outcome!="success": sys.exit(1)


if __name__=="__main__":
    main()
