# Topic selection and media viability gate

This is a required stage of the topic-agnostic YouTube pipeline. A detected trend is a candidate, not an automatic production decision.

## Required order

1. Discover candidates using free trend signals.
2. Research the subject and locate credible primary sources.
3. Inventory topic-specific media, supplementary free stock/audio, and potentially useful excerpts from existing published content.
4. Review exact asset pages and, for clips, the exact in/out timestamps, purpose, excerpt length and significance, original-work context, transformation/commentary, likely market impact, licence/permission basis, platform terms and third-party rights.
5. Compare candidates on audience opportunity, research depth, media coverage, rights readiness and production feasibility.
6. Record GO, CONDITIONAL or HOLD/RESELECT with reasons.
7. Only after the gate passes, write the storyline, script and storyboard against the verified inventory.
8. Produce and quality-check; require human approval before public publishing.
9. Measure performance and feed results back into future selection.

## Automated first-pass audit

Workflow: `.github/workflows/topic-viability-audit.yml`

Script: `topic_viability_audit.py`

With a manually entered topic, the workflow audits that topic. Leave the input blank to collect free Google Trends RSS signals and audit the top 10 unique candidates before ranking them for human review. The shortlist audit checks public Wikipedia, Wikimedia Commons and NASA Image and Video Library APIs. It makes no YouTube Search API calls, does not download or republish media, and does not publish or modify any channel. The shortlist ranking is a triage aid, not an automatic winner selection.

Artifacts:
- `shortlist-comparison.md/json` — comparison of up to 10 trending candidates, with no automatic winner selection.
- `candidates/<topic>/audit.json` and `media-inventory.csv` — per-candidate research and media leads.
- For a manually entered topic, `topic-audit.md/json` and `media-inventory.csv` — single-topic report and inventory.

## Scorecard

Each component is scored 0–5 and weighted to 100:
- Audience signal: 25%
- Research depth: 20%
- Media inventory: 30%
- Rights readiness: 15%
- Production feasibility: 10%

The first-pass score is only a triage tool. If a topic is entered manually, audience signal is unmeasured; do not treat media volume as evidence of popularity. API result counts do not establish that results are relevant, downloadable or reusable.

The current scripts never automatically approve a topic for storyboarding. The shortlist adds a weak keyword-overlap check to flag leads that may be more relevant, but this is not semantic verification and can miss good assets or retain false positives. A CONDITIONAL result means research and media leads exist but the team must verify relevance, video coverage, stock-media supply and item-level rights. HOLD/RESELECT means the available evidence is too thin to proceed. Do not spend scarce AI credits or begin full story production until a human has checked those gaps.

## Rights and editorial guardrails

- Prefer public-domain material and licences that permit the intended commercial use and adaptations.
- Record the exact source page, creator, licence, attribution text, download date and planned scene for each chosen asset.
- Review third-party material, music, logos, people, trademarks, and licence restrictions separately.
- Public availability is not a reuse licence. Attribution alone does not grant permission.
- Fair use and fair dealing are different, jurisdiction-specific exceptions. No fixed number of seconds is universally safe; attribution or a disclaimer is not a substitute for permission or a valid exception.
- Clipping existing content is an explicit sourcing route. Prefer native clipping/remix tools, licensed source files, public-domain/permissively licensed content, or excerpts with a documented legal basis. A simple compilation may still infringe copyright and may fail YouTube monetization rules even if copyright permission exists.
- Never bypass paywalls/access controls or treat public viewability as permission. Do not automate mass downloading/re-uploading as a default. Record the original URL, creator, exact timestamps, licence/permission or exception rationale, planned commentary/story purpose, and platform-policy risks for each clip.
- If rights are unclear, exclude the asset, obtain permission, or use an alternative. Human review is required before publication.

## Current implementation status

The first shortlist-audit version selected Helen Haines from the trend feed and surfaced weak research/media relevance. The single-topic audit now uses a MediaWiki API fallback and conservative scores. A shortlist comparator has been added to audit up to 10 unique trending candidates against research and topic-keyword-matched Wikimedia/NASA media leads before human review. Its keyword check is only a heuristic; stock-video coverage, actual asset usability, primary-source research and item-level rights still require manual verification. Run the workflow once with the topic field blank to test this updated comparison.


## Additional free-media sources (2026-10-20)
The audit now queries Openverse for openly licensed image leads, the Library of Congress catalog, and Internet Archive image/movie records, in addition to Wikimedia Commons and NASA. Candidate reports also link to Pexels and Pixabay stock-video searches. The Pexels/Pixabay API endpoints require keys, so they are not queried automatically. Openverse is image-only in this implementation; Internet Archive direct file resolution and real video playback checks are not yet implemented. Treat every returned record as a lead until the source page, licence, download/playback and commercial/adaptation terms have been reviewed.

## Existing-content clipping route
Clipping is now part of the planned sourcing layer, alongside licensed/public-domain media and original/AI-assisted assets. See `CLIP_SOURCING.md` for a per-clip review record and workflow. The current topic-audit scripts do not yet discover, timestamp, download, or assemble clips from existing videos; that is a future module, and must not be described as implemented until tested.
