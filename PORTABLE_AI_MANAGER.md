# Portable Multi-AI Project Manager

Last updated: 2026-10-20
Repository: https://github.com/Astridrosexxx84/Astridrose-automation-

## Mission
Coordinate a topic-agnostic, $0-upfront content and automation business using whichever AI tools are currently accessible and suitable. Providers are replaceable workers, not the source of truth. Keep the project portable across ChatGPT, Gemini, Copilot, Groq, OpenRouter, and future providers.

## Source of truth
Before doing work, read in this order:
1. `PROJECT_STATUS.md` — latest known state and next action.
2. `TOOL_REGISTRY.md` — actual connected tools, quotas and blockers.
3. `AUTOMATION_PLAN.md` — overall architecture.
4. Relevant workflow, script, or content package files.
5. `AI_TEAM_SETUP.md` — current manual multi-provider analysis workflow.

After meaningful work, update the relevant files and add a dated entry to `PROJECT_STATUS.md`. Do not rely on chat history as the only record.

## Project objective and current direction
Build a free-first, largely automated pipeline that discovers audience opportunities across topics, researches candidates, audits relevant media and rights, creates original story/script/storyboard, assembles and quality-checks videos, requests human approval before public publishing, and measures audience response. Topic selection must remain dynamic; Zelda is an example, not a permanent niche. The near-term goal is a few strong public videos and initial audience growth, not immediate monetization. Monetization is a later decision informed by audience response and available resources.

The user works primarily from an Android phone and needs minimal manual UI steps. Give one actionable next step at a time when user intervention is necessary. Prefer direct connected-tool actions over instructions for the user to do them manually. Avoid needless rewrites/rebuilds; first inspect the existing implementation and test it.

## Operating constraints
- Budget is $0 upfront. Prefer free searches, public datasets, deterministic code and existing connected tools before generation credits.
- Never purchase, start a paid trial, enable billing, or trigger paid usage without explicit user approval.
- Do not evade provider quotas by rotating accounts. Route work to a genuinely available free allowance or deterministic alternative.
- Never place secrets, tokens, passwords, or private account data in repository files, artifacts, prompts, or chat. Refer to required secret names only.
- Public uploads, social posts, comments, playlist changes, scheduling, or other externally visible actions require user approval unless the user has explicitly authorized that specific bounded action.
- Treat search results as leads, not proof. Verify facts, media availability, item-level licence/rights, platform rules and output quality.
- Do not claim a provider ran a task unless it actually returned a result. Do not claim a workflow passed until its run/result has been inspected.
- Do not treat a file, workflow, integration listing or advertised free tier as proof of working access.

## Multi-AI task routing
Choose providers dynamically per task using the current registry and a fresh capability/access check where practical. Compare: (1) usable access now, (2) task fit, (3) free quota/cost, (4) ability to work with GitHub/files, (5) output quality, (6) privacy and licence terms.
- Coding/repository edits: prefer an AI with direct GitHub write access or a code agent that can inspect, test and commit changes.
- Research/trend discovery: prefer free web search, public APIs and deterministic scripts first; use a research-capable AI to interpret evidence.
- Script/storyboard/creative development: use a capable text/creative model after the topic and media gate passes.
- Image/video generation: use the tool with verified free credits, export rights and acceptable resolution/watermark; reserve scarce credits for real gaps.
- Independent review: use a second model to challenge assumptions, test claims, or review a patch. Avoid duplicating expensive work.
- Workflow automation: prefer GitHub Actions and ordinary scripts for repeatable tasks; use AI for decisions that benefit from judgment.
- Provider failure/quota exhausted: record the blocker, choose the next suitable provider or deterministic fallback, and continue where possible.

Providers do not automatically share memory, tools, credentials or permissions. Exchange work through repository artifacts, task briefs, patches, workflow artifacts and explicit result reports. Each provider must connect to GitHub independently and receive only the permissions needed.

## Task lifecycle
1. Read project status and relevant files.
2. Identify the single highest-value next task and state the intended outcome.
3. Inspect current code/workflow before changing it.
4. Prefer a small, reversible change. Use tests or a non-publishing workflow first.
5. Run the narrowest useful test. Inspect logs and artifacts.
6. Record what changed, evidence of success/failure, unresolved risks, resource cost, and next action.
7. Update `PROJECT_STATUS.md`, `TOOL_REGISTRY.md` if access/quota changed, and the relevant queue/report.
8. Do not stop at advice if the connected tools permit safely doing the work directly.

## Required task report
For each meaningful task, record:
- Goal and files/workflows touched
- Actions actually performed
- Test run and observed result (link or run ID where possible)
- Cost/credits consumed, or state "none verified"
- Known limitations and blockers
- Next recommended action
- Whether user approval is needed

## Current high-priority work
Start from the latest `PROJECT_STATUS.md`; its dated next action supersedes this summary. As last recorded on 2026-10-20, the topic shortlist/media-source expansion has not yet been validated end-to-end. Run the manual topic-viability workflow with the topic blank, inspect the artifact and logs, then fix any errors. This should not spend AI credits, call YouTube Search API, or publish. Continue with production improvements only after the shortlist is evidence-based and the media/rights gate is satisfied.

## Portability / handover
When a new AI takes over:
1. Open this file, `PROJECT_STATUS.md`, `TOOL_REGISTRY.md`, and `README.md`.
2. Confirm which repositories and files it can read/write.
3. Confirm available integrations and actual free limits without triggering paid use.
4. Inspect the latest commits and workflow runs; do not trust status text alone when a fresh check is possible.
5. Report capability gaps and the first concrete next action.
6. Make all meaningful work persistent in GitHub so another provider can resume.

## Security and safety
Use least-privilege repository access. Keep secrets in GitHub Actions Secrets or the relevant provider's secure secret store. Avoid sending confidential material to multiple providers. Review diffs before merging broad or destructive changes. Never delete project assets or rewrite the default branch history as a shortcut.


## Battery meter and collaborative switchboard

See AI_BATTERY_SYSTEM.md for the target design. Treat providers as interchangeable workers with observable, honest status—not fixed job titles. Share task briefs and evidence through GitHub; let suitable providers propose, challenge, and review one another's work. Track only quota information actually exposed by the provider; otherwise report it as unknown. Switch to another legitimately available free route on a limit or service failure, and use deterministic work when possible. Never rotate accounts or use paid routes to bypass a limit. The current Gemini/Groq/OpenRouter workflow is a first collaboration prototype, not yet a universal router.
