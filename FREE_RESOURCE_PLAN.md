# Free-resource operating plan

Last reviewed: 2026-10-19

## Rule zero

Do not spend a limited AI credit or run a manual workflow just to test something that already works. Draft and plan first; generate only after the concept is approved. Prefer reusable templates, ordinary editing, and free research over paid or credit-metered generation.

## App roles

| Tool | Best role | Resource policy |
|---|---|---|
| ChatGPT | Planning, research synthesis, scripts, titles, descriptions, shot lists, checklists | Use for the thinking and drafting stage; avoid generating media until the brief is settled. |
| YouTube Data API + GitHub Actions | Weekly trend discovery and private research playlists | Keep the existing weekly schedule. Do not manually rerun successful workflows without a specific reason. Check the run summary before changing code. |
| vidIQ | YouTube keyword/outlier research, trend validation, title/thumbnail analysis | Check the live balance before use. If the balance is depleted, pause credit-consuming tools until renewal; prefer research features only when their cost is confirmed as zero. |
| Canva | Thumbnail/layout design, captions, reusable templates, simple edits and resizing | Use free editing/templates first. AI design and video generation have limited usage; spend those only on a final chosen concept, not on exploratory variations. |
| Runway | Selected AI images, occasional visual assets, sound effects or voice when allowed by the connected plan | Check the live balance and available models before use. Treat credits as scarce; do not generate batches. Prefer one approved key visual if needed. Re-check balance before generation. |
| HeyGen | Presenter/avatar video for a polished final script | Connected account reports Free plan, but the current video quota is not exposed by the connection. Public plan documentation says availability is limited (typically 1–3 free videos depending on region). Do not use for test videos; reserve for a high-value final asset. |
| Metricool | Scheduling and reviewing performance across connected social accounts | Connected Astrid Rose brand has YouTube, Instagram and Facebook linked. Public Free plan currently allows one brand and up to 20 scheduled posts/month; verify the in-account limit before relying on it. Keep AI text generation for rare cases; create copy with ChatGPT first. |
| Pexels | Free stock photos/video when genuinely useful | Free commercial use is allowed under its license, subject to restrictions. Keep a record of the source and license; do not imply endorsement or simply re-upload stock as if it were original work. |
| YouTube Audio Library | Background music and sound effects | Prefer tracks whose YouTube Audio Library license does not require attribution; if a track requires Creative Commons attribution, include it exactly as instructed. |

## YouTube API budget

The weekly selector makes one `search.list` request for each of 10 seed topics, plus one `videos.list` batch per topic. The playlist stage makes two more searches, one video-statistics batch, one playlist creation, and up to five playlist-item insertions.

Current Google documentation describes `search.list` as a separate daily bucket (default 100 calls/day) and the general API pool as 10,000 units/day. Read/list requests usually cost 1 unit; playlist creation and each playlist-item insertion cost 50 units. Based on the current workflow, that is about 12 search calls per run and about 311 units in the general pool (10 selector statistics calls + 1 playlist statistics call + 6 writes), before any retries. Check the Google Cloud quota page for the project's actual limits and usage; quotas can change.

## Production workflow

1. Discover topics once per week.
2. Compare the report and choose a direction; do not automatically commit to the highest score without reviewing audience/language fit.
3. Draft the script and storyboard with ChatGPT.
4. Choose only the necessary assets: Pexels/other properly licensed media first, Canva for layout, then Runway or HeyGen only if their limited generation materially improves the result.
5. Edit with free editing features; avoid repeated AI regeneration.
6. Publish only original, licensed, or meaningfully transformative material. A private playlist of other people's videos is for research, not a substitute for making publishable content.
7. Use Metricool scheduling only after a content batch is ready, and reserve the monthly post slots for planned posts.
8. Record what was used, any credit cost, the resulting asset, and performance so we don't repeat low-value experiments.

## Important cautions

- Free-plan features and limits can change and may vary by account or region. Re-check before a high-cost action.
- A connected app does not mean all its features are free. A tool may be connected but its generation feature may be paid-only.
- Do not spend a credit just to learn whether a model works; inspect available models and the balance first.
- Never upload or republish other creators' videos just because they are popular. Use trend research to guide original content and check licenses for any third-party assets.
