# Topic-agnostic YouTube content automation plan

## Goal
Build a highly automated, $0-upfront YouTube content pipeline. Revenue is a hypothesis to validate, not a guarantee. No fixed niche: the system should discover opportunities from current trends and choose based on audience signal, research depth, relevant free media, rights readiness, and production feasibility.

## Required pipeline
1. Discover a shortlist from free trend sources.
2. Compare candidates before choosing one; do not equate the highest trend rank with the best video opportunity.
3. Research the subject using credible primary and secondary sources.
4. Inventory relevant topic-specific images/video, free stock, audio, and existing published content that may be clipped. Record source URL, creator, timestamp range, media type/duration, licence/permission basis and intended use.
5. Evaluate three acquisition routes: (a) public-domain/permissively licensed material, (b) clips from existing published content where permission or a valid jurisdiction-specific exception supports the exact use, and (c) original/AI-assisted assets for gaps. For clips, check the source, the precise excerpt, purpose, amount/substantiality, transformation/commentary, market impact, platform terms and any third-party music/material. Public availability, short duration, or attribution alone is not permission.
6. Make a documented GO / CONDITIONAL / HOLD decision. Do not storyboard from search-result counts alone.
7. Write an original storyline, script and storyboard based on verified available assets; identify gaps that actually require generated visuals.
8. Assemble, caption, narrate, render and quality-check using free tools first.
9. Obtain explicit approval before public publishing. Never publish automatically from topic discovery or an audit.
10. Measure performance and feed evidence back into future candidate selection.

## Current implementation
- Repository: Astridrosexxx84/Astridrose-automation-.
- `free_trend_selector.py` gathers English-market Google Trends RSS signals without YouTube Search API calls.
- `topic_viability_audit.py` audits one manually entered topic using public research and Wikimedia/NASA media leads.
- `topic_shortlist_audit.py` is newly added to compare up to 10 trend candidates using preliminary research/media signals and a weak keyword-overlap heuristic. It is not yet end-to-end tested.
- The latest known single-topic audit ran successfully but selected Helen Haines and showed why popularity-first selection is insufficient. No assets are automatically rights-cleared.
- The Zelda animatic and playlist-curation tests are separate prototypes, not proof that the complete original-video pipeline is finished.

## Operating rules
- $0 upfront. Prefer free search, public APIs, local tools and free stock licences.
- Do not buy credits, start paid trials or trigger paid usage without explicit approval.
- Clipping is an approved sourcing route, not a blanket permission to copy. Prefer platform-native clip/remix features where suitable, licensed downloads, public-domain/permissively licensed sources, or excerpts that have been reviewed for a valid legal exception. Do not bypass access controls or use automated downloading/re-uploading as the default. Keep source timestamps and a documented rights rationale for each excerpt.
- Keep credentials in GitHub Actions secrets; never put secrets in source code or chat.
- Work in small, clear steps when phone interaction is required.

## Next action
Open `.github/workflows/topic-viability-audit.yml`, run it with the topic field blank, and inspect `shortlist-comparison.md` plus the per-candidate inventories. This is the one remaining manual action needed to validate the new shortlist comparator. No generation or publishing should occur during that test.
