# AI Control Room — $0-first mobile app blueprint

## Product goal
A phone-first app for running projects with interchangeable AI coordinators and workers. The app, not any model provider, owns durable project state. When a provider reaches a free-tier limit, work is checkpointed and another available provider resumes from the same state.

## Core user experience
1. Open app and choose or create a project.
2. Select a coordinator from configured providers.
3. Assign worker roles: research, planning, writing, code, QA, media discovery.
4. Add a free provider using guided connector setup; show API-ready, needs credentials, rate-limited, or unavailable.
5. See a shared task board, decisions, files, outputs, provider health, and cooldown status.
6. On limit/error, save a checkpoint and offer Switch worker or Switch coordinator. The replacement receives a compact project brief plus latest checkpoint.
7. Review and approve consequential actions (publishing, deleting, spending, changing credentials) before execution.

## Non-negotiable $0 policy
- Use only routes explicitly identified as free-tier/free models.
- Never require a credit card or enable paid fallback automatically.
- Keep spend controls at zero where providers expose them; quotas and rate limits are variable, not guaranteed.
- Never store API keys in project files, logs, prompts, or Git commits. Use secure device storage or server-side secrets.
- Show which provider/model was used and why a handoff occurred.

## Durable project memory owned by the app
Each project stores:
- project_brief: goal, constraints, acceptance criteria, current plan.
- decisions: decision, rationale, date, and reversibility.
- tasks: status, owner/provider, inputs, outputs, dependencies, retry count.
- artifacts: file references and version history.
- checkpoint: completed work, current work, next exact action, open questions, known failures, relevant context.
- provider_events: provider/model, timestamp, outcome, latency, and rate-limit metadata (never secrets).
- approvals: pending or completed user confirmations.

A handoff packet includes: (1) objective and constraints, (2) current task and acceptance criteria, (3) decisions/facts not to re-litigate, (4) completed work and artifact locations, (5) attempts and failures, (6) exact next action, and (7) expected output format.

## Provider adapter design
Every provider implements list_models(), health_check(), generate(messages, model, limits), and normalizes outcomes to success, rate_limited, auth_error, quota_exhausted, provider_error, or unknown_error. It reports whether the route is known free; unknown-cost routes are rejected under the $0 policy.

Initial candidates: OpenRouter free models, Gemini API free tier, and Groq developer/free access where available. Quotas and eligible models can change, so verify current configuration; a key alone does not prove a route is free. Copilot is a separate integration question; installation alone does not provide a general-purpose API worker.

## Handoff policy
- Rate limit/quota exhaustion: persist partial output and checkpoint, mark provider cooling down, choose the next eligible free provider, resume from the handoff packet.
- Auth error: do not loop; mark connector as needing attention.
- Ambiguous failure: retry once if safe, then checkpoint and ask or switch.
- All free providers unavailable: save everything and pause cleanly. Never silently use a paid service.
- Avoid duplicate side effects with idempotent steps; require approval for external publication or deletion.

## Practical architecture
**Phase 1 — reuse existing GitHub backend:** use GitHub Actions and the existing coordinator as a test harness; stabilize adapters, checkpoint schema, and handoff logic before UI.
**Phase 2 — phone UI:** responsive installable web app (PWA) with project list, team selector, task board, outputs, and provider status. It can be added to the Android home screen without app-store fees.
**Phase 3 — persistence:** use a free-tier database only if current limits and account requirements fit $0; otherwise start with versioned project files, without secrets or private data.
**Phase 4 — end-to-end proof:** one project, one coordinator, two workers; simulate a rate limit and prove the checkpoint survives and another model continues.
**Phase 5 — connect content pipeline:** use the same project/task interface for trends, research, free-media search, scripting, storyboards, editing, QA, and publishing.

## MVP acceptance test
A phone user creates a project, chooses an eligible free coordinator, assigns two workers, sees each provider result, triggers a simulated quota failure, switches providers, and finishes without losing decisions/progress or making a paid request.

## Next engineering steps
1. Inspect and document the current coordinator and workflow flags.
2. Make Gemini/Groq free-route enablement explicit and auditable without changing billing or secrets.
3. Normalize provider errors and produce one machine-readable report of every attempted provider and outcome.
4. Persist a checkpoint before each handoff.
5. Test handoff with simulated quota exhaustion.
6. Build the PWA around the proven backend.
