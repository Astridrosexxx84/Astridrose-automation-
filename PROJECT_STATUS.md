# Project Coordinator Handover

Last checked: 2026-10-19

## Active goal — supersedes earlier DBZ-only scope
Build a topic-agnostic, $0-upfront YouTube content pipeline. A trend detector selects the topic; the pipeline researches it, finds relevant rights-cleared topic media and free stock media, develops an original storyline/script/storyboard, uses AI generation only for genuine visual gaps, assembles and quality-checks a video, then asks for approval before public publishing. Zelda is the current example topic, not the permanent niche. Do not revert to DBZ-only work unless the user changes scope again.

Phone-first support: give one small next step at a time. Prefer free searches and tools; reuse existing workflows rather than rebuilding without cause. Do not buy credits, start paid trials, or trigger paid usage without explicit approval. Public upload needs approval.

## Repository
- Repository: Astridrosexxx84/Astridrose-automation-
- Default branch: main
- Public repository; connected GitHub integration can read and write.
- Existing files include README.md, AI_TEAM_SETUP.md, AUTOMATION_PLAN.md, ai_team_coordinator.py, youtube_keyword_search.py, youtube_playlist_manager.py, and GitHub Actions workflows.

## Current production package
- `content-packages/zelda-ocarina-of-time-remake-2026.md`: original short-form concept, draft narration, storyboard, rights checklist, metadata and QA gate.
- `content-packages/zelda-assets-shortlist.md`: specific candidate free stock clips and official Nintendo reference URLs.
- These are planning artifacts. Two Pexels stock clips have been imported into Canva (asset IDs listed below); no local stock downloads, final timeline, video render, or upload yet. The rough-cut edit decision list is `content-packages/zelda-ocarina-of-time-remake-edit-decision-list.md`.
- Primary topic source: Nintendo Australia official overview and game page. Confirm current facts against official sources before editing/publishing.
- Rights rule: official Nintendo promotional material may only be used consistently with Nintendo's current game-content guidelines and with original creative input/commentary; do not repost a trailer or other creators' gameplay. Free stock licences must be checked per asset and recorded.

## Trend discovery
- `free_trend_selector.py` reads Google Trends RSS across US, UK, Canada, Australia, New Zealand and Ireland, ranks recurring/high-position topics, and writes `topic-discovery-scorecard.txt`.
- It makes zero YouTube Search API calls during discovery, helping avoid quota use.
- Discovery workflow ran successfully on 2026-10-19, but selected Helen Haines, whose Wikipedia summary lookup failed. Audit scoring was too generous for unverified media leads. `topic_viability_audit.py` now uses a MediaWiki API fallback, conservative preliminary scores, and no automatic storyboard approval; this updated code still needs a fresh run.

## Existing YouTube automation
- YouTube keyword-search workflow: `.github/workflows/youtube-keyword-search.yml`; uses `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, and `YOUTUBE_REFRESH_TOKEN` secrets.
- YouTube playlist-manager workflow: `.github/workflows/youtube-playlist-manager.yml`; do not run without selected video URLs and explicit approval.
- Latest previously verified keyword-search run #5 succeeded on 2026-10-18 and uploaded the `dbz-video-candidates` artifact. This verified OAuth refresh and YouTube search at that time, but the run used an older generic fallback. Check current code and latest run before assuming current behavior.
- A public YouTube upload was previously reported successful (video ID `23HeRIIb2QU`); returned visibility was public, but independent playback was not verified.
- Do not repeat OAuth setup unless a new run proves authentication is broken. Secret values are not readable through the connector; never ask the user to paste keys or tokens into chat.
- GitHub connector has no confirmed workflow-dispatch action; if manual triggering is required, explain the single mobile-friendly step.

## Free-tool/resource policy
- Existing tool registry: `TOOL_REGISTRY.md`. Read it before spending any generation credits.
- Current registry records Runway connected/free with 485 credits at last check but no video generation models available; HeyGen Free with quota unverified; vidIQ at 0/150 renewable credits until 2026-11-16 06:11 UTC; Canva connected with export limits unverified; PixVerse listed as a candidate needing account/quota/export/licence verification. Do not assume advertised allowances equal usable access.
- Prioritize free media search and deterministic tools before AI generation. Use AI only where needed, and verify commercial-use rights and export constraints first.

## Coordination rules
- Read this file and `TOOL_REGISTRY.md` before acting.
- User explicitly wants all available AIs to contribute to shared project coordination when legitimately available; do not claim a service reviewed anything unless it actually did.
- Respect real free-tier limits; do not evade quotas via account rotation.
- Record meaningful decisions, evidence, blockers, and completed work in repository artifacts.
- Keep credentials out of commits, reports and chat.
- Keep user in control of public-facing changes and publishing.

## Next action
Run `.github/workflows/topic-viability-audit.yml` once with the topic field blank. The workflow now compares up to 10 unique Google Trends candidates against research and topic-keyword-matched Wikimedia/NASA media leads, then produces a ranked review shortlist rather than blindly treating the top trend as the winner. Inspect `shortlist-comparison.md` and the per-candidate inventories. This is still preliminary: keyword overlap is a weak heuristic; verify primary sources, real downloadable/playable video coverage, free stock supply, and item-level rights before scripting or storyboarding. Keep generation spending at zero and do not publish without approval.

## Latest production progress (2026-10-19)
- Verified Pexels stock video pages and imported two actual MP4 assets into the connected Canva media library:
  - Misty forest landscape, Pexels 6656520 — Canva asset ID `VAHYcMR-y2g`, 1920×810, 49 seconds.
  - Forest walk with sun rays, Pexels 31381734 — Canva asset ID `VAHYcKYcwI4`, 1920×1080, 15 seconds.
- Updated `content-packages/zelda-assets-shortlist.md` with asset IDs and licence/source notes.
- Added draft timed captions at `content-packages/zelda-ocarina-of-time-remake-captions.srt`.
- Generated a free local eSpeak narration timing draft (80.04 seconds); the WAV is a placeholder voice, not final production narration. Script file: `zelda_ocarina_voiceover.txt`.
- Not yet completed: a video timeline/design, selected official Nintendo visuals, final narration performance, rendering/export, final rights review, or public upload. Do not imply the video is already made.
- Free-source policy remains: avoid paid generation; only consider AI after the first assembly shows a specific gap. Pexels says its videos are free for commercial use under its licence, but final usage still needs current licence and third-party-rights review.


## Local rough-cut prototype (2026-10-19)
- Rendered a real H.264/AAC MP4 animatic locally: 1080×1920 (9:16), 25 fps, 80.04 seconds, ~1.8 MB.
- Includes the current eSpeak placeholder narration and burned-in captions, with original abstract forest/fantasy-themed title cards.
- The MP4 is a **visual animatic/proof of assembly only**, not the final video: it does not yet include the two imported Pexels clips or official Nintendo reference footage, and the placeholder voice is not final. It is not uploaded to YouTube.
- Local artifact: `/mnt/data/zelda_ocarina_animatic_draft.mp4` in the current ChatGPT work session.
- Next: replace appropriate cards with rights-checked topic-specific official reference visuals and licensed stock footage, check caption/audio sync, then render and review a production cut before asking for publishing approval.


## Topic viability gate added (2026-10-19)
- Added `topic_viability_audit.py`, which researches a candidate topic using Wikipedia's public summary API and inventories leads from Wikimedia Commons and NASA's Image and Video Library, including available licence metadata and explicit rights-review flags.
- Added `.github/workflows/topic-viability-audit.yml`. It accepts a topic or runs the existing free Google Trends RSS selector when the input is blank. It uploads a Markdown report, structured JSON and CSV media inventory as a 14-day artifact.
- Added `TOPIC_SELECTION_GATE.md` documenting the required order: trend discovery → subject research → media inventory → rights assessment → candidate scoring/go-no-go → story/script/storyboard → production/QA → human approval → measurement.
- The new workflow does not call YouTube Search API, download/re-upload media, spend generation credits, change playlists, or publish videos.
- Status: code and workflow committed; first GitHub Actions run and score calibration still need verification. API search results are leads, not cleared assets. Human review of facts and each asset's licence/rights is mandatory before story writing and publication.


## Shortlist comparison update (2026-10-19)
- Added `topic_shortlist_audit.py` to compare up to 10 unique trending topics before choosing what to produce.
- Blank-topic workflow runs free Google Trends RSS discovery, then creates per-candidate JSON/CSV inventories and an overall Markdown/JSON comparison report.
- Candidates are ranked for human review using trend signal, research availability, media leads and a rough keyword-overlap relevance hint. No automatic winner is selected and no topic is cleared for storyboarding.
- Manual topic input still uses the single-topic audit.
- Not yet verified end-to-end; next step is one blank-topic workflow run. No AI credits or publishing are involved.


## Free-media source expansion (2026-10-20)
- Added Openverse image search, Library of Congress catalog search, and Internet Archive image/movie catalogue search to both single-topic and shortlist audits.
- Reports include source-specific result counts and retain each source's rights-review caveats. Internet Archive file URLs are not yet resolved automatically; LOC rights are item-specific; Openverse results point back to source pages.
- Added direct search links for Openverse, LOC, Internet Archive, Pexels videos, and Pixabay videos. Pexels/Pixabay APIs need keys, so no new secrets or API keys were added.
- Increased workflow timeout to 20 minutes to allow more free API checks across up to 10 candidates.
- Not yet run after these code changes; syntax and API compatibility must be confirmed by the next workflow run. No media was downloaded, no AI credits used, and nothing published.


## Collaborative AI battery architecture (2026-10-20)

- Added `AI_BATTERY_SYSTEM.md` defining the battery meter, dynamic provider switchboard, collaborative proposal/challenge/synthesis loop, portable work packets, honest quota states, failover rules, and a phased build plan.
- Updated `PORTABLE_AI_MANAGER.md` to make the battery/switchboard model part of the project manager's operating rules.
- Verified the existing `ai_team_coordinator.py` and `.github/workflows/ai-team-coordinator.yml`: they already support a limited collaborative pass (Gemini analysis, Groq challenge, OpenRouter zero-price model challenge, Gemini synthesis) and preserve partial contributions when one provider fails. This is not yet a general router or live battery meter.
- A fresh Actions run list shows topic-viability runs #27 and #28 completed successfully, but those were push-triggered runs from 2026-10-19, not proof that the newest free-media expansion has been run manually end-to-end. No new AI-provider request was made during this review.
- Important design rule: provider quotas are often not exposed as a reliable live percentage. Record observed success/errors and provider-reported limits/reset times; show quota as unknown when it cannot be measured. Do not invent battery percentages.
- Next: build the smallest useful status ledger and bounded provider failover into the existing coordinator, then test its routing logic without sending paid requests. Keep the coordinator manual and report-only until this is validated. Separately, run the topic-viability workflow with blank topic when a manual workflow dispatch is available, then inspect its artifact.


## AI battery implementation milestone (2026-10-20)

- Added `ai_battery.py`: dependency-free status ledger, conservative error classification, safe JSON persistence, Markdown dashboard output, and free-route eligibility filtering.
- Added `tests/test_ai_battery.py`: checks quota/auth classification, no invented quota percentages, blocked-provider filtering, persistence without raw provider error bodies, and invalid-provider rejection.
- Added `.github/workflows/ai-battery-tests.yml` to run these checks on relevant changes and manual dispatch.
- GitHub Actions run #1 for AI battery logic tests: the test step completed successfully. Run link: https://github.com/Astridrosexxx84/Astridrose-automation-/actions/runs/39341674095
- Current limitation: these are tested building blocks, not yet integrated into `ai_team_coordinator.py`; the dashboard only reflects recorded observations and configured-secret presence. It does not probe provider APIs or expose actual remaining quota. The current coordinator still does not dynamically switch providers for each task.
- Next implementation: wire provider call outcomes into the persistent ledger, add bounded failover between eligible free providers, and keep the report useful when any/all providers fail. Test routing with mocked failures before any live provider call. Keep billing and publishing disabled.


## Battery ledger integrated into AI team workflow (2026-10-20)

- Integrated provider outcome recording into `ai_team_coordinator.py`: observed successes and failures for Gemini, Groq, and OpenRouter now update a persistent `ai-battery-status.json` ledger.
- The coordinator now generates `ai-battery-status.md` with explicit quota-unknown states and includes the ledger/dashboard in the review artifact.
- OpenRouter is marked as a verified zero-price route only when the coordinator selects a model whose current model listing says both prompt and completion pricing are zero and the model ID ends in `:free`. Gemini/Groq free-route eligibility stays unknown in the ledger rather than being assumed.
- Expanded the battery CI workflow to compile both Python modules and run the unit tests. No live provider calls were made to test this integration, so provider API behavior and artifact upload still require a later manual run.
- Next: add bounded, task-level provider fallback and test it with mock providers; only then run the live manual workflow if configured free access is confirmed. No paid route, publishing, or account changes are allowed.


## First synthesis failover added (2026-10-20)

- The AI coordinator now attempts a single fallback synthesis using the already-selected OpenRouter model only when Gemini's final synthesis fails. It uses OpenRouter only if the model was selected from the live listing as zero prompt/completion price and `:free`; if that fails too, it preserves all completed analyses and generates a deterministic fallback report.
- The battery ledger records the fallback outcome. No new live provider call was made for this code change.
- Updated the battery CI trigger to run syntax/tests when `ai_team_coordinator.py` changes. Next check is the resulting CI run; only after it passes should we consider a manual live run. Broader per-task dynamic routing across additional AI apps remains future work.

## Battery CI verification and cooldown behaviour (2026-10-20)

- Confirmed GitHub Actions run #3 passed: Python syntax compilation and all battery classification/routing/persistence tests succeeded. Run: https://github.com/Astridrosexxx84/Astridrose-automation-/actions/runs/39341838266
- Updated the Gemini request retry policy: HTTP 429 is treated as a quota/cooldown signal and is no longer retried against the same provider. HTTP 503 and timeouts remain eligible for bounded retries. This avoids needlessly repeating requests when a provider explicitly says to slow down.
- The latest retry-policy edit will trigger the battery CI workflow; its result must be checked before calling this change verified.
- Next architecture milestone remains a general task-level router that can hand a task to another provider only when its route is confirmed zero-price and usable. The current coordinator still has fixed analysis roles and only one specific synthesis fallback; this is not yet universal dynamic switching. No live AI requests, paid actions, publishing, or account changes were performed for this edit.

## Generic task-level fallback primitive (2026-10-20)

- Added `run_task_with_fallback()` to `ai_battery.py`. It tries handlers in caller-specified order, skips routes that are not verified zero-price when free-only mode is enabled, stops retrying a provider after its handler fails, records a safe failure category, and tries the next eligible provider. It never invents quota percentages or stores raw exception bodies.
- Added mocked tests for switching from a simulated HTTP 429 to a verified-free backup, and for refusing a route whose free-price status is unknown. No real provider is called by these tests.
- These are reusable routing primitives; the existing production coordinator has not yet been refactored to use this helper for all task types. Live provider eligibility remains conservative: a configured key or model listing alone does not prove remaining quota or zero cost. Awaiting CI confirmation for this commit before the next integration step.

## Generic router CI verification (2026-10-20)

- Confirmed AI battery logic tests run #6 passed after the generic fallback helper and mock-provider tests were committed. The run includes Python syntax compilation and the unit-test suite: https://github.com/Astridrosexxx84/Astridrose-automation-/actions/runs/39342236284
- The mocked test verifies a 429 from the first eligible route records cooldown and hands the task to the next verified-zero-price route; another test verifies that an unverified-price route is not called in free-only mode.
- Next: integrate this helper into the coordinator's actual task execution in a bounded way, then test provider selection with mocks. Do not call live services until free-price eligibility is clear for each route. Current coordinator still has fixed roles and is not yet fully dynamic.


## Coordinator routing integration (2026-10-20)

- Integrated `run_task_with_fallback()` into the real coordinator's final-synthesis step.
- Final synthesis now only attempts OpenRouter after its model listing confirms a `:free` model with zero prompt and completion prices. Gemini is not used for synthesis unless its route is explicitly verified; no paid fallback is attempted.
- If the verified route is unavailable or fails, the coordinator preserves the independent analyses and emits a deterministic review report.
- Commit: `453ff3ba583850e955dadd9dcb85afe04591342b`. AI battery CI run #7 is pending verification: https://github.com/Astridrosexxx84/Astridrose-automation-/actions/runs/39342620323
- This is a bounded integration, not yet full dynamic routing for every analysis task. The analysis calls and requirement for all three provider secrets remain to be simplified in the next pass.
