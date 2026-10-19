# Existing-content clipping: sourcing and review design

## Purpose
Treat clipping as one of the pipeline's raw-material routes alongside open/licensed catalogues, stock footage, and original/AI-assisted assets. The goal is to find relevant moments efficiently and use them only when the intended use has a defensible legal basis and fits platform rules.

## Candidate discovery
For each trend/topic, discover potentially useful source videos such as interviews, official briefings, public talks, documentaries, podcasts, streams, news reports, explainers and creator videos. Prefer in this order:
1. Public-domain or openly licensed source material with terms that permit the intended use.
2. Source files licensed for reuse, direct permission, or platform-native clipping/remix features whose terms cover the intended use.
3. A short excerpt only where the use has been reviewed for an applicable copyright exception (for example, criticism/review, quotation, parody or other locally recognized categories). Do not assume an exception applies just because the clip is short.

Use official APIs or permitted search/browsing routes to discover sources. Do not bypass access controls, paywalls or technical restrictions. The current audit does not yet implement this discovery module.

## Per-clip record
Store one row per proposed excerpt:
- Topic and planned scene
- Original title, creator/channel and canonical source URL
- In-point and out-point (timestamps); excerpt duration
- What the excerpt actually demonstrates or contributes
- Intended purpose and the original commentary/narration that surrounds it
- Licence/permission and evidence URL, OR a written jurisdiction-specific exception rationale
- Whether music, graphics, footage, people or other third-party material appears inside the clip
- Attribution text and any licence conditions
- Source access/download method and terms checked
- YouTube copyright/Content ID risk and separate reused-content monetization assessment
- Reviewer decision: APPROVED, PERMISSION_NEEDED, REPLACE, or HOLD_FOR_REVIEW

## Clip-level decision questions
- Is the exact excerpt necessary for the commentary/story, rather than merely decorative?
- Is the use covered by a licence/permission, or does it plausibly fit an applicable exception in the relevant jurisdiction?
- Is the amount taken proportionate to that purpose, including whether the excerpt captures the “heart” of the source?
- Does the edit add substantive original context, analysis, criticism, explanation, or narrative rather than just repackaging?
- Could the clip substitute for the original or harm its normal market?
- Are embedded music, logos, performers, guests, and other rights separately accounted for?
- Do source-platform terms permit the planned retrieval and use?
- Could YouTube's reused-content policy prevent monetization even if copyright permission exists?

No universal “safe seconds” rule applies. Attribution, a disclaimer, cropping, subtitles, speed changes or adding background music do not by themselves make a use lawful. A valid copyright exception is fact-specific and differs by jurisdiction. For New Zealand publishing, check the applicable New Zealand copyright rules rather than assuming the US fair-use doctrine applies.

## YouTube-specific operational note
YouTube's monetization rules assess reused content separately from copyright. A clip-based video needs meaningful original commentary, criticism, explanation or entertainment value; minimal edits or compilations may be ineligible even if permission exists. Copyright claims can still occur for short excerpts, including music. Check current official YouTube policies before publishing.

## Implementation phases
1. **Discovery index:** collect candidate source URLs and metadata from free/official search routes; no downloads.
2. **Timestamp review:** identify candidate in/out points from available transcripts, captions, chapters or manual review. Treat auto-generated transcript matches as leads, not truth.
3. **Rights review:** generate the per-clip record and require a human decision before any excerpt enters the edit.
4. **Assembly:** use permitted source files/native platform features or approved excerpts; preserve source and attribution records.
5. **QA:** inspect the final cut for source context, rights, attribution, Content ID/copyright risk, reused-content value, and platform policies.
6. **Measure:** track claims, blocks, monetization outcomes and audience retention to improve future sourcing decisions.

## Official policy starting points
- YouTube reused-content and monetization policy: https://support.google.com/youtube/answer/1311392
- YouTube fair-use overview (US law; not a substitute for local law): https://support.google.com/youtube/answer/9783148
- New Zealand legislation: https://www.legislation.govt.nz/
