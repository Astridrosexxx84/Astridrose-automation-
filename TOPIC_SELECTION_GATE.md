# Topic selection and media viability gate

This is a required stage of the topic-agnostic YouTube pipeline. A detected trend is a candidate, not an automatic production decision.

## Required order

1. Discover candidates using free trend signals.
2. Research the subject and locate credible primary sources.
3. Inventory topic-specific media and supplementary free stock media.
4. Review exact asset pages, licences, attribution, adaptation/commercial terms and third-party rights.
5. Compare candidates on audience opportunity, research depth, media coverage, rights readiness and production feasibility.
6. Record GO, CONDITIONAL or HOLD/RESELECT with reasons.
7. Only after the gate passes, write the storyline, script and storyboard against the verified inventory.
8. Produce and quality-check; require human approval before public publishing.
9. Measure performance and feed results back into future selection.

## Automated first-pass audit

Workflow: `.github/workflows/topic-viability-audit.yml`

Script: `topic_viability_audit.py`

With a manually entered topic, the workflow audits that topic. Leave the input blank to run the existing Google Trends RSS detector first. The workflow uses public Wikipedia, Wikimedia Commons and NASA Image and Video Library APIs. It makes no YouTube Search API calls, does not download or republish media, and does not publish or modify any channel.

Artifacts:
- `topic-audit.md` — readable summary, score and recommendation.
- `topic-audit.json` — structured research, score, source links, inventory and errors.
- `media-inventory.csv` — individual media leads, creators/licence metadata where available, source URLs and rights-review flags.

## Scorecard

Each component is scored 0–5 and weighted to 100:
- Audience signal: 25%
- Research depth: 20%
- Media inventory: 30%
- Rights readiness: 15%
- Production feasibility: 10%

The first-pass score is only a triage tool. If a topic is entered manually, audience signal is unmeasured; do not treat media volume as evidence of popularity. API result counts do not establish that results are relevant, downloadable or reusable.

The current script never automatically approves a topic for storyboarding. A CONDITIONAL result means research and media leads exist but the team must verify relevance, video coverage, stock-media supply and item-level rights. HOLD/RESELECT means the available evidence is too thin to proceed. Do not spend scarce AI credits or begin full story production until a human has checked those gaps.

## Rights and editorial guardrails

- Prefer public-domain material and licences that permit the intended commercial use and adaptations.
- Record the exact source page, creator, licence, attribution text, download date and planned scene for each chosen asset.
- Review third-party material, music, logos, people, trademarks, and licence restrictions separately.
- Public availability is not a reuse licence. Attribution alone does not grant permission.
- Fair use and fair dealing are different, jurisdiction-specific exceptions. A clip compilation or superficial edit is not automatically lawful or monetizable.
- Do not build a pipeline that downloads and repackages other creators' videos as a default strategy.
- If rights are unclear, exclude the asset, obtain permission, or use an alternative. Human review is required before publication.

## Current implementation status

The first GitHub Actions run succeeded, but the selected topic (Helen Haines) had no usable Wikipedia summary, and the report exposed overly generous preliminary scoring. The audit script has now been updated to use a MediaWiki API fallback, lower scores when research is unavailable, treat licence metadata as unverified, and prevent automatic storyboard approval. These changes still need a fresh workflow run. The workflow remains discovery-only and does not write a story or publish a video.
