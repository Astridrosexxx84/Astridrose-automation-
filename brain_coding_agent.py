"""Guarded code-building worker for Vision. Opens a PR; never merges or deploys."""
import base64, json, os, re, subprocess, sys, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from brain_relay_worker import call_groq, call_gemini, call_openrouter

ALLOWED = {"brain-app/app.js", "brain-app/index.html", "brain-app/styles.css"}

def run(args, check=True):
    r = subprocess.run(args, text=True, capture_output=True, check=False)
    if check and r.returncode:
        raise RuntimeError("Local validation failed: " + " ".join(args[:3]))
    return r

def patch_paths(patch):
    paths = []
    for line in patch.splitlines():
        if line.startswith("+++ "):
            p = line[4:].split("\t", 1)[0].strip()
            paths.append(p[2:] if p.startswith("b/") else p)
    return paths

def validate_patch(patch):
    if not patch.startswith("diff --git ") or len(patch) > 120000:
        raise ValueError("No valid bounded unified diff was returned.")
    paths = patch_paths(patch)
    if not paths or any(p not in ALLOWED for p in paths) or len(set(paths)) > 3:
        raise ValueError("Patch targets files outside the guarded UI allowlist.")
    if re.search(r"(gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|sb_secret_[A-Za-z0-9_-]{20,}|service_role)", patch, re.I):
        raise ValueError("Patch appears to contain a credential or privileged key.")
    return sorted(set(paths))

def ask_provider(prompt):
    candidates = [
        ("groq", os.getenv("GROQ_API_KEY", "").strip(), call_groq),
        ("gemini", os.getenv("GEMINI_API_KEY", "").strip(), call_gemini),
        ("openrouter", os.getenv("OPENROUTER_API_KEY", "").strip(), call_openrouter),
    ]
    selected = os.getenv("AI_RELAY_PROVIDER", "auto").strip().lower()
    if selected == "cloudflare":
        raise RuntimeError("Build mode needs a code-capable free route. Choose Auto, Groq, Gemini, or OpenRouter; Cloudflare's configured small model is not used for code changes.")
    if selected in ("groq", "gemini", "openrouter"):
        candidates.sort(key=lambda item: 0 if item[0] == selected else 1)
    errors = []
    for name, key, call in candidates:
        if not key:
            continue
        if name in ("groq", "gemini") and os.getenv("ALLOW_" + name.upper() + "_FREE_TIER_CALLS", "").lower() != "true":
            continue
        try:
            model, answer = call(key, prompt)
            answer = answer.strip()
            fence = chr(96) * 3
            if answer.startswith(fence):
                lines = answer.splitlines()
                answer = "\n".join(lines[1:-1] if lines[-1].strip() == fence else lines[1:])
            start = answer.find("diff --git ")
            if start < 0:
                raise ValueError("Provider did not return a unified diff.")
            patch = answer[start:].strip()
            validate_patch(patch)
            return name, model, patch
        except Exception as exc:
            errors.append(name + ":" + type(exc).__name__)
    raise RuntimeError("No configured free provider returned a safe patch. " + ", ".join(errors))

def open_pr(branch):
    repo = os.getenv("GITHUB_REPOSITORY", "")
    token = os.getenv("GITHUB_TOKEN", "")
    if not repo or not token:
        raise RuntimeError("GitHub PR permissions are unavailable.")
    body = {
        "title": "Vision AI builder: proposed app improvement",
        "head": branch,
        "base": "main",
        "body": "AI-proposed Brain App UI change. The guarded builder ran local syntax, UI wiring, and regression checks. Review the diff and require all GitHub Actions checks to pass. This PR was not merged or deployed automatically."
    }
    req = urllib.request.Request("https://api.github.com/repos/" + repo + "/pulls",
        data=json.dumps(body).encode(), method="POST",
        headers={"Authorization":"Bearer " + token, "Accept":"application/vnd.github+json",
                 "X-GitHub-Api-Version":"2022-11-28", "Content-Type":"application/json",
                 "User-Agent":"Vision-Guarded-Code-Builder"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode()).get("html_url", "")
    except urllib.error.HTTPError as exc:
        raise RuntimeError("GitHub refused the proposed PR (HTTP " + str(exc.code) + ").") from None

def main():
    task = os.getenv("AI_RELAY_TASK", "").strip()
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    provider, model, pr_url, outcome = "none", "unavailable", "", "error"
    try:
        if not task or len(task) > 8000:
            raise ValueError("A private task goal under 8,000 characters is required.")
        html = Path("brain-app/index.html").read_text(encoding="utf-8")
        app = Path("brain-app/app.js").read_text(encoding="utf-8")
        css = Path("brain-app/styles.css").read_text(encoding="utf-8")
        context = ("FILE brain-app/index.html\n" + html[:18000] +
                   "\nFILE brain-app/app.js\n" + app[:30000] +
                   "\nFILE brain-app/styles.css\n" + css[:12000])
        prompt = (
            "You are Vision's code-building worker. Fulfil this goal with one focused, useful app improvement.\n"
            "GOAL:\n" + task + "\n\nCURRENT SOURCE:\n" + context + "\n\n"
            "Return ONLY a standard unified git diff starting with diff --git. No prose or markdown fences.\n"
            "Only edit existing files brain-app/app.js, brain-app/index.html, brain-app/styles.css.\n"
            "Do not edit workflows, backend functions, migrations, credentials, or deployment config.\n"
            "Preserve existing features, private-data boundaries, accessibility, and mobile-first simplicity.\n"
            "Never add secrets, never include this prompt in the code, and do not claim tests were run.\n"
            "Prefer a focused safe change. Do not refactor unrelated code."
        )
        provider, model, patch = ask_provider(prompt)
        validate_patch(patch)
        patch_file = Path("/tmp/vision-agent.patch")
        patch_file.write_text(patch + "\n", encoding="utf-8")
        run(["git", "apply", "--check", str(patch_file)])
        run(["git", "apply", str(patch_file)])
        changed = run(["git", "diff", "--name-only"]).stdout.splitlines()
        if not changed or any(p not in ALLOWED for p in changed):
            raise RuntimeError("Changed files exceeded the UI allowlist.")
        run(["git", "diff", "--check"])
        run(["node", "--check", "brain-app/app.js"])
        run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"])
        run([sys.executable, "-m", "py_compile", "brain_relay_worker.py", "brain_relay_chain.py", "brain_cloudflare_worker.py", "brain_coding_agent.py"])
        ids = set(re.findall(r'\bid=["\']([^"\']+)["\']', Path("brain-app/index.html").read_text(encoding="utf-8")))
        refs = set(re.findall(r'\$\(["\']([^"\']+)["\']\)', Path("brain-app/app.js").read_text(encoding="utf-8")))
        if refs - ids:
            raise RuntimeError("UI wiring check found missing element IDs.")
        run(["git", "checkout", "-b", "vision-ai-build-" + os.getenv("GITHUB_RUN_ID", "run")])
        run(["git", "config", "user.name", "github-actions[bot]"])
        run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"])
        run(["git", "add"] + changed)
        run(["git", "commit", "-m", "Vision AI builder: guarded app improvement"])
        token = os.getenv("GITHUB_TOKEN", "")
        auth = "AUTHORIZATION: basic " + base64.b64encode(("x-access-token:" + token).encode()).decode()
        run(["git", "config", "--local", "http.https://github.com/.extraheader", auth])
        branch = run(["git", "branch", "--show-current"]).stdout.strip()
        run(["git", "push", "origin", branch])
        pr_url = open_pr(branch)
        if not pr_url:
            raise RuntimeError("GitHub returned no pull request URL.")
        outcome = "success"
        output = "A guarded AI-generated patch passed preflight checks and was opened for review: " + pr_url + "\nNothing was merged or deployed. Review the diff and wait for all GitHub Actions checks before merging."
    except Exception as exc:
        output = "CODE BUILD BLOCKED SAFELY: " + str(exc)[:220] + "\nNo model-authored code was merged or deployed."
    finished = datetime.now(timezone.utc).isoformat(timespec="seconds")
    record = {"schema_version":1, "task":task, "task_id":os.getenv("AI_RELAY_TASK_ID",""),
        "project_id":os.getenv("AI_RELAY_PROJECT_ID",""), "overall_outcome":outcome,
        "successful_turns":1 if outcome=="success" else 0, "total_turns":1,
        "turns":[{"provider":provider,"model":model,"outcome":"success" if outcome=="success" else "error",
          "error_category":None if outcome=="success" else "guarded_code_build_blocked",
          "worker_output":output,"next_action":"Review the PR and wait for all checks before merging." if pr_url else "Inspect the blocker and retry only after understanding the cause."}],
        "next_action":"Review the PR and wait for all checks before merging." if pr_url else "Inspect the blocker and retry only after understanding the cause.",
        "started_at":started,"finished_at":finished}
    Path("brain-relay-packet.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path("brain-relay-packet.md").write_text("# Vision guarded code builder\n\n" + output + "\n", encoding="utf-8")
    Path("brain-relay-status.json").write_text(json.dumps({"schema_version":1,"updated_at":finished,
        "provider":provider,"model":model,"status":"AVAILABLE" if outcome=="success" else "ERROR",
        "outcome":outcome,"quota_remaining":"not exposed","free_route":"free-provider policy; no paid fallback"}, indent=2) + "\n", encoding="utf-8")
    print("Vision code builder: " + outcome + "; private result prepared; task text and patch omitted from logs.")
    if outcome != "success":
        sys.exit(1)

if __name__ == "__main__":
    main()
