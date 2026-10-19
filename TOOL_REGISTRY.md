# Astrid Production Tool Registry

Last reviewed: 2026-10-19
Operating constraint: $0 upfront. Prefer renewable free allowances. Never buy credits or trigger paid usage without explicit approval.

## Purpose
This registry is the coordination record for Astrid's production pipeline. Keep it updated when a tool is connected, its allowance is checked, or a workflow changes. Do not treat a directory listing as a connected account, or an advertised free tier as verified account access.

## Pipeline
1. Discover multiple candidate topics using Google Trends RSS / other free trend sources; use YouTube/vidIQ research only when it is available without consuming scarce quota.
2. Research the actual subject using credible primary and secondary sources; record verifiable claims and story angles.
3. Audit media availability before story writing: find topic-specific images/video, free stock/audio, and potentially useful clips from existing published content; record exact source links, creator, timestamps/duration, licence or permission basis, attribution and intended scene.
4. Assess rights and risk per asset. Public availability is not permission; fair use/fair dealing are context-specific, not blanket permissions. Clipping is a sourcing route, not automatic clearance: review each excerpt and platform rules. Prefer native clip/remix features, licensed downloads, public-domain/permissively licensed material, or excerpts with a documented legal basis.
5. Score and compare candidates on audience signal, research depth, media coverage, rights readiness and production feasibility. Record GO / CONDITIONAL / HOLD with reasons; change the topic/angle when usable media is insufficient.
6. Only after the decision gate passes, write the original story, script, hook, storyboard, titles, description and captions against the verified inventory.
7. Produce media: use the cheapest eligible generator only for genuine visual gaps; check licence and allowance first.
8. Assemble with free editing/rendering, captions and audio tools; retain source assets and final MP4.
9. Quality gate: check facts, asset rights, sound, captions, format, watermark and platform policy.
10. Obtain human approval before public publishing; never publish automatically from a topic audit.
11. Measure views, retention, engagement and audience signals; feed results into the next topic selection.
12. Track free credits, reset timing, watermark/export limits, commercial-use terms, and whether access is direct or manual.

## Connected tools and current status

| Tool | Role | Verified state / constraints | Next action |
|---|---|---|---|
| GitHub Actions + repository | Orchestration, rendering, publishing | Connected; repo is Astridrosexxx84/Astridrose-automation-. Existing public upload workflow succeeded once (run 39211048176, video 23HeRIIb2QU; returned visibility=public, independent playback not verified). Google Trends selector and single-topic viability audit have run; the new 10-candidate shortlist comparator is committed but not yet executed. | Run the topic viability workflow with its topic field blank and inspect the shortlist artifact; no publishing during this test. |
| YouTube Data API | Publish videos/playlists | Upload workflow exists. YouTube Search API previously hit quota 429. | Prefer Google Trends RSS / low-cost sources; avoid unnecessary search calls. |
| Runway | Image generation, speech, sound effects, editing | Live connection check confirms personal workspace “Astrid”, Free plan, 485 credits remaining, 0 purchased. Available image models: Nano Banana variants, Seedream 5 variants, Muse Image, Gen-4 image models. No video models available; sound effects available. Video generation/editing/multishot and image upscaling are plan-gated. | Reserve credits; use only when its strengths justify spending; no generation until we choose a test. |
| HeyGen | Talking avatar, speech and video | Live account check confirms Free plan. Premium and add-on credit balances are returned as null, so remaining allowance/reset timing cannot be verified from the account API. | Check in-app free video quota before generation; no generation yet. |
| vidIQ | Trend research, channel analysis, scripts, thumbnails, voiceover/compose tools | Live balance check: 0/150 renewable credits, 0 add-on; next reset 2026-11-16 06:11 UTC. Authorized channel is Astridrose84 (@astridrose84), 3 public videos, 10 lifetime views, 0 subscribers at check. | Use only zero-credit calls until reset; do not spend credits just to demonstrate tools. |
| Canva | Graphics, designs, image generation and assembly | Connected. Live Brand Kit check returned no visible kits; free allowance and export limits remain unverified. | Use no-credit design inspection first; verify quota before image/design generation. |
| Metricool | Scheduling and analytics | Live brand check confirms “Astrid Rose”; Instagram (@astridrose2026), YouTube (channel UCueCuFD7slmyp4daqdYNE-Q), and Facebook are connected; timezone Pacific/Auckland. Scheduling quota/plan and actual publishing permissions remain untested. | Check free scheduling limits and test a non-publishing read before scheduling anything. |
| Automations | Scheduled reminders/workflows | Available through ChatGPT tools; not yet configured as pipeline scheduler. | Use after the workflow is reliable, not as a substitute for a tested publishing pipeline. |

## External candidates (not yet connected or account-verified)

| Tool | Potential role | Free allowance evidence | Status |
|---|---|---|---|
| Google Flow | Image/video generation, characters, scene building | Official help lists 50 Flow credits per day for non-subscribers; peak-time video generation may be unavailable. | Test access and NZ account eligibility; manual website until an API/connector is confirmed. |
| Adobe Firefly | Image/video/audio generation and creative finishing | Official Adobe help says free users get a limited daily number of generations; exact free video allowance depends on account/features, and premium video features may require a plan. | Strong licensing-oriented candidate; verify account meter, video access and commercial terms before counting it as production capacity. |
| PixVerse | Short video generation, image-to-video | Official FAQ: 30 daily credits for non-members, 60 for members; daily credits expire at UTC midnight. Output limits and watermark terms must be checked in-account. | Strong daily-credit candidate; verify signup, generation cost, download and commercial terms. |
| Viggle | Character motion / animation | Official pricing lists 5 free videos/day; one generation at a time and 7-day storage on Free; watermark-free is not included. | Candidate for motion tests; verify rights and whether watermark is acceptable. |
| PixVerse | Short video generation, image-to-video | Official app FAQ/pricing lists 30 daily credits on Basic free tier (60 for members); free output is capped at 540p and may carry watermark. | Strong candidate; verify signup, generation cost, download and commercial terms. |
| Viggle | Character motion / animation | Official pricing lists 5 free videos/day; assets stored 7 days and watermark-free is not included on Free. | Candidate for motion tests; verify rights and workflow. |
| Explain Video Generator | Narrated explainers and diagrams | ChatGPT listing describes a free starting route; exact current allowance/account access not independently verified. | Candidate for non-avatar content. |
| LTX Studio | Storyboards / multi-scene planning | Official help says free account is mainly exploration; some users receive one-time credits and free-credit outputs are personal-use only. | Do not use for monetizable content unless license changes. |
| Higgsfield | Image/video generation, character references, voiceover | Listed in ChatGPT app directory but not installed/connected. Free allowance not verified. | Connection required; assess free quota and licensing before use. |
| OpenArt, fal, sync. labs, ElevenLabs, Creative Claw, Pollo AI | Image/video, lip sync, audio and editing | Free allowance / commercial terms not verified for this account. | Research candidates; do not count as available capacity yet. |

## Resource and licensing rules
- Track renewable credits separately from one-off welcome credits and free trials.
- Record actual per-generation credit cost and output dimensions before batching.
- Do not use a tool for monetizable publishing until its commercial-use terms are checked.
- Prefer original scripts/commentary and licensed/owned or public-domain/permissively licensed assets. Existing-content clips may be used only after clip-level review of the legal basis, excerpt amount/significance, purpose, transformation, market impact, third-party rights and platform rules. Copyright legality and YouTube monetization eligibility are separate checks.
- Do not trigger paid usage, subscriptions, top-ups, or paid API calls without explicit approval.
- Do not claim a video is published until the YouTube upload result confirms a public URL / video ID.

## Status labels
- CONNECTED: authenticated account usable from ChatGPT.
- AVAILABLE: app/site exists, but user account or access not verified.
- VERIFIED FREE: actual free allowance and usable export confirmed.
- BLOCKED: permission, quota, plan, region or workflow prevents use.
- NEEDS TEST: plausible but not yet verified.

Update this file as the source of truth when account checks and pipeline tests change.


## Topic audit implementation
- Workflow: `.github/workflows/topic-viability-audit.yml` (manual dispatch; blank topic uses the free Trends RSS selector).
- Script: `topic_viability_audit.py`; outputs `topic-audit.md`, `topic-audit.json`, and `media-inventory.csv` as an artifact.
- Research sources: Wikipedia REST summary, Wikimedia Commons API, NASA Image and Video Library API; Pexels/Pixabay search links are provided for additional manual sourcing.
- This is a first-pass inventory and scoring gate, not automatic legal clearance. No media is counted as cleared automatically; every asset must be checked individually. First workflow run remains unverified.

- Free-media discovery: Wikimedia Commons + NASA APIs; newly expanded with Openverse images, Library of Congress catalog, and Internet Archive image/movie catalog. Pexels/Pixabay stock video are linked for manual searches; their APIs require keys and are not automated yet. Added 2026-10-20; pending workflow validation.
