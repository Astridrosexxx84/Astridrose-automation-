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
