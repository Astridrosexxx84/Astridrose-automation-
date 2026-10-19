# Astrid Production Tool Registry

Last reviewed: 2026-10-19
Operating constraint: $0 upfront. Prefer renewable free allowances. Never buy credits or trigger paid usage without explicit approval.

## Purpose
This registry is the coordination record for Astrid's production pipeline. Keep it updated when a tool is connected, its allowance is checked, or a workflow changes. Do not treat a directory listing as a connected account, or an advertised free tier as verified account access.

## Pipeline
1. Discover topics: Google Trends RSS / other free trend sources; use YouTube/vidIQ research only when available without consuming scarce quota.
2. Validate opportunity: compare recency, audience demand, competition, and whether we can make an original contribution.
3. Write: create a concise original script, hook, scene list, title, description, and captions.
4. Produce media: use the cheapest eligible generator for each asset; preserve Astrid's character references and voice notes.
5. Assemble: use free editing/rendering, captions, and audio tools; retain source assets and final MP4.
6. Quality gate: check factual claims, copyright, sound, captions, format, watermark, licensing, and platform policy.
7. Publish: use the existing GitHub Actions / YouTube upload workflow after its trend-selector path is verified; no unapproved paid API calls.
8. Measure: read views, retention, engagement, and audience signals; feed results into the next topic selection.
9. Track resources: record free credits, reset timing, watermark/export limits, commercial-use terms, and whether access is direct or manual.

## Connected tools and current status

| Tool | Role | Verified state / constraints | Next action |
|---|---|---|---|
| GitHub Actions + repository | Orchestration, rendering, publishing | Connected; repo is Astridrosexxx84/Astridrose-automation-; YouTube credentials are configured. Trend-selector workflow still needs a successful end-to-end verification. | Verify workflow, logs and public video result before scaling. |
| YouTube Data API | Publish videos/playlists | Upload workflow exists. YouTube Search API previously hit quota 429. | Prefer Google Trends RSS / low-cost sources; avoid unnecessary search calls. |
| Runway | Image generation, speech, sound effects, editing | Connected Free workspace. 485 of 500 account credits remain. Video generation/editing/multishot and image upscaling are gated in this workspace; image models and sound effects are available. | Reserve credits; use only for assets that need its strengths. |
| HeyGen | Talking avatar, speech and video | Connected; account reports Free plan. Exact remaining video allowance was not exposed by account check. | Check usable free video limit before generation; use only when identity/avatar is needed. |
| vidIQ | Trend research, channel analysis, scripts, thumbnails, voiceover/compose tools | Connected. Current credit response: 0 credits available; renewable bucket maximum 150, next reset reported 2026-11-16. | Use only tools confirmed free/no-credit; recheck balance after reset. |
| Canva | Graphics, designs, image generation and assembly | Connected; free allowance not yet verified. | Check current limits before generation; use for layout and finishing where free. |
| Metricool | Scheduling and analytics | Connected; account/brand and free-plan limits not yet audited. | Inspect connected brands, supported platforms and free scheduling limits. |
| Automations | Scheduled reminders/workflows | Available through ChatGPT tools; not yet configured as pipeline scheduler. | Use after the workflow is reliable, not as a substitute for a tested publishing pipeline. |

## External candidates (not yet connected or account-verified)

| Tool | Potential role | Free allowance evidence | Status |
|---|---|---|---|
| Google Flow | Image/video generation, characters, scene building | Official help lists 50 Flow credits per day for non-subscribers; peak-time video generation may be unavailable. | Test access and NZ account eligibility; manual website until an API/connector is confirmed. |
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
- Prefer original scripts, commentary, licensed/owned media, and public-domain or permissively licensed assets. Do not build the channel around unaltered copyrighted reuploads.
- Do not trigger paid usage, subscriptions, top-ups, or paid API calls without explicit approval.
- Do not claim a video is published until the YouTube upload result confirms a public URL / video ID.

## Status labels
- CONNECTED: authenticated account usable from ChatGPT.
- AVAILABLE: app/site exists, but user account or access not verified.
- VERIFIED FREE: actual free allowance and usable export confirmed.
- BLOCKED: permission, quota, plan, region or workflow prevents use.
- NEEDS TEST: plausible but not yet verified.

Update this file as the source of truth when account checks and pipeline tests change.
