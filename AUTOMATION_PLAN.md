# Topic-agnostic YouTube content automation plan

## Goal
Build a highly automated, $0-upfront YouTube content pipeline. Revenue is a hypothesis to validate, not a guarantee. No fixed niche: the system should discover opportunities from current trends and choose based on audience signal, research depth, relevant free media, rights readiness, and production feasibility.

## Required pipeline
1. Discover a shortlist from free trend sources.
2. Compare candidates before choosing one; do not equate the highest trend rank with the best video opportunity.
3. Research the subject using credible primary and secondary sources.
4. Inventory relevant topic-specific images and video plus free stock media. Record source URLs, creator, media type/duration, licence and intended use where available.
5. Review relevance, real download/playback availability, commercial/adaptation terms, attribution and third-party rights. Public availability is not permission.
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
- Do not download/re-upload other creators' YouTube videos as a shortcut.
- Keep credentials in GitHub Actions secrets; never put secrets in source code or chat.
- Work in small, clear steps when phone interaction is required.

## Next action
Open `.github/workflows/topic-viability-audit.yml`, run it with the topic field blank, and inspect `shortlist-comparison.md` plus the per-candidate inventories. This is the one remaining manual action needed to validate the new shortlist comparator. No generation or publishing should occur during that test.
