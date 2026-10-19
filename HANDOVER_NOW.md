# Handover Now — Multi-AI Project

Updated: 2026-10-20

## Start here
Repository: https://github.com/Astridrosexxx84/Astridrose-automation-
Default branch: `main`
Management rules: `PORTABLE_AI_MANAGER.md`
Current project status: `PROJECT_STATUS.md`
Tool access/quota ledger: `TOOL_REGISTRY.md`

## What the project is
A phone-first, $0-upfront effort to build a topic-agnostic, mostly automated content pipeline and grow an audience before deciding on monetization. The pipeline should detect interesting topics, research them, find relevant free/rights-cleared topic media plus stock media, create an original storyline and storyboard, use AI only where needed, assemble and quality-check a video, request approval before public posting, then measure audience response. Do not assume a permanent niche based on one trend result.

## Architecture already present
The repository is not a blank slate. It contains:
- A topic/trend selection and viability audit system, including `free_trend_selector.py`, `topic_viability_audit.py`, and `topic_shortlist_audit.py`.
- GitHub Actions workflows for topic viability, YouTube keyword search, playlist management and other automation.
- Free-media discovery sources recently expanded to Wikimedia Commons, NASA, Openverse, Library of Congress and Internet Archive catalogue search, plus manual stock-search links.
- Video editing/rendering prototypes and content package artifacts, including a Zelda Ocarina of Time remake concept. Zelda is a test topic, not the permanent project niche.
- A manual multi-provider analysis workflow described in `AI_TEAM_SETUP.md`; it uses Gemini, Groq and OpenRouter free-model routing if the corresponding Actions secrets exist and free quotas are available. This is an analysis/report workflow, not a universal agent that can operate every connected app.

## Verified versus unverified state
Read the dated details in `PROJECT_STATUS.md` and `TOOL_REGISTRY.md`. Important current caveat: on 2026-10-20, the new shortlist comparator and expanded media sources were committed but had not yet been validated end-to-end after those changes. The Zelda MP4 mentioned in status is a visual animatic/proof of assembly with placeholder narration, not a finished production video and not uploaded. A previous public YouTube upload was reported, but independent playback was not verified.

## Immediate next task
Run `.github/workflows/topic-viability-audit.yml` with its topic input blank. Inspect the run log and resulting shortlist artifact; confirm the new media-source expansion works and scores are sensible. This is a research/test run only: no generation credits, no playlist mutation, and no public publishing. Record the actual result in `PROJECT_STATUS.md`.

## Rules for the incoming AI
- Read `PORTABLE_AI_MANAGER.md` first and follow its task lifecycle.
- Do not ask the user to restate the project before inspecting these files and the latest code/run evidence.
- Prefer directly executing tasks through the tools actually available to you.
- If GitHub write access is unavailable, prepare a complete patch/file and give the user the smallest possible step to apply it.
- Never ask for API keys or tokens in chat. Check only whether the expected secret names exist if the platform allows safe metadata inspection; do not expose secret values.
- Keep the user in control of public-facing changes. A test workflow that only researches and creates an artifact is the preferred first verification.
- If a better free AI/tool becomes available, update `TOOL_REGISTRY.md` and route that task there. Providers are replaceable; GitHub project files remain the shared memory.
