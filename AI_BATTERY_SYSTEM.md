# AI Battery Meter and Collaborative Switchboard

Last updated: 2026-10-20

## Purpose

The project must keep progressing when one AI provider reaches a free-tier limit, becomes unavailable, or is unsuitable for the current task. The project repository—not a particular provider or chat session—is the shared memory and source of truth.

This is legitimate failover across providers' available free allowances, not account rotation or quota evasion. Never create extra accounts, bypass rate limits, enable billing, buy credits, or silently trigger paid use to keep the pipeline running.

## The four parts

1. **Battery meter** — tracks provider connection, last successful call, recent errors, any explicit rate-limit response, known reset time, task suitability, and cost tier.
2. **Connection switchboard** — selects an eligible provider for the current task; tries the next suitable provider after a quota/service failure; stops if no verified free route remains.
3. **Collaboration loop** — gives contributors the same scoped task brief and shared evidence. One proposes; others independently critique or add value; a coordinator resolves disagreements and identifies unsupported claims.
4. **Persistent handoff** — records outputs, decisions, changed files, test evidence, resource cost, unresolved questions, and next action in GitHub so a different provider can continue without repeating work.

## Battery status vocabulary

Do not invent a numeric percentage when the provider does not expose one.

- AVAILABLE: a recent successful request and no known current block. This does not mean the remaining quota is known.
- LOW_OR_COOLDOWN: provider explicitly returned a rate-limit/quota signal, or a documented reset time is active.
- UNKNOWN: no reliable quota information is exposed or no recent check was made.
- DISCONNECTED: missing credentials or access is not configured.
- ERROR: provider is temporarily failing or returned an operational error.
- PAID_ROUTE_BLOCKED: only a paid route is available; never use it without explicit user approval.
- COOLING_DOWN: wait until a confirmed reset time if available; otherwise use another eligible provider or a non-AI fallback.

Where supported, retain the HTTP status, provider error category, checked-at timestamp, and reset-after value. Never store API keys, authorization headers, raw secrets, or sensitive prompt content in the status log. Treat reset times as estimates unless the provider explicitly supplies them.

## Task routing

For each task, rank options by:
1. Can it be done with deterministic code, free public data, or an existing workflow without using AI quota?
2. Which currently connected provider is suitable for the task?
3. Is a genuinely zero-price route confirmed, with billing not required?
4. Does the provider have the needed tool permissions (GitHub, web research, files, media generation)?
5. Is a second independent review valuable enough to justify the extra requests?
6. Can the output be verified with tests, source checks, or human review?

A task can be split into stages. For example, a free script can gather trend and media evidence; one model can interpret it; a second can challenge the recommendation; deterministic tests can check output shape. Do not call every model for every trivial step. Collaboration means useful independent contributions and review, not duplicated requests for the sake of using more providers.

## Failover rules

- On explicit quota/rate-limit response: mark the provider LOW_OR_COOLDOWN; respect any reset information; route to the next suitable free provider.
- On timeout or transient service failure: retry only a small, bounded number of times, then switch.
- On missing key, permission denial, or unavailable model: mark disconnected/error and continue only with other configured providers.
- On no eligible provider: preserve partial work, record the blocker, and continue deterministic work where possible. Never fall back to a paid model.
- On return after cooldown: allow a small health check or next suitable task; do not assume the whole quota has reset unless confirmed.
- If providers disagree: retain the disagreement and supporting evidence; do not automatically treat a synthesis as fact.
- Never claim work was completed by a provider unless its output was received and recorded.

## Shared work packet

Every non-trivial task should have:
- unique task name or ID and goal;
- relevant repository files and evidence links;
- constraints and definition of done;
- current owner/provider, if any;
- status: queued, in_progress, blocked, review, or done;
- output path(s);
- tests and observed results;
- providers attempted and status category (not credentials);
- verified cost/credits used, or unknown/not exposed;
- next action and any approval needed.

The handoff should be small enough that another AI can pick it up from GitHub without relying on the previous chat.

## Battery dashboard minimum viable version

The first dashboard can be a Markdown or JSON report generated by GitHub Actions; no paid dashboard service is needed. For each provider show:

| Field | Meaning |
|---|---|
| Provider / model | Exact service and model used |
| Connection | configured, missing, or failed |
| Last successful call | timestamp if known |
| Last observed result | success, quota limit, timeout, auth failure, other error |
| Quota remaining | number only if the provider supplies a reliable value; otherwise not exposed |
| Reset | exact provider-reported time if available; otherwise unknown |
| Free route verified | yes / no / unknown |
| Eligible tasks | text, code, research, image, video, etc. |
| Next action | use, wait, reconnect, or use fallback |

The dashboard is an observed status snapshot, not a promise that a free quota is unlimited or that a provider will stay available.

## Current implementation baseline

The repository already contains ai_team_coordinator.py and .github/workflows/ai-team-coordinator.yml. The current script runs Gemini analysis, a Groq challenge, an OpenRouter challenge restricted to listed zero-price :free models, and Gemini synthesis. It records unavailable contributions and continues when a provider fails. This is a useful first collaborative loop, but it is not yet a general battery-aware router: it is limited to three configured API providers, does not maintain a durable provider health ledger, and does not automatically route all project tasks to different AI/app tools.

The workflow is manual and report-only. Keep it that way until provider costs, quota behavior, task persistence, and failure recovery are verified.

## Recommended build order

1. Observe before automating: inspect recent workflow runs, verify current code and secrets are configured without exposing secret values, and confirm what has actually run.
2. Add a provider status ledger: record outcomes, explicit quota signals, timestamps, and known reset data without pretending to know hidden quota percentages.
3. Add bounded failover: each provider call should be replaceable; stop rather than spending money.
4. Make tasks portable: use a small task queue and shared work packets in the repository.
5. Add collaborative review: independent proposal + critique + synthesis, with a deterministic check wherever possible.
6. Connect tools dynamically: include direct GitHub coding agents and existing creative/research apps only after actual access, permissions, free allowance, and output rights are verified.
7. Run non-publishing tests: test provider failures, missing credentials, rate-limit signals, no-free-provider conditions, and resume-from-handoff behavior.
8. Update project status: every meaningful run must record what happened and the next action.

## Security and approval boundaries

- Keep credentials in provider secret stores or GitHub Actions Secrets.
- Never send secrets or sensitive personal information to multiple models.
- Do not evade quotas with account rotation or automated account creation.
- Never enable billing, buy credits, start paid trials, or silently use a paid endpoint.
- Keep public posts, uploads, comments, scheduling, playlist mutations, and account changes behind explicit user approval unless the user has authorized that exact bounded action.
- Prefer least-privilege permissions and review code changes before broad/destructive edits.
