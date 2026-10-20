#!/usr/bin/env python3
"""Create early storyboard hypotheses before research/media comparison."""
import json
import re
from pathlib import Path

scorecard = Path("topic-discovery-scorecard.txt")
out = Path("preliminary-storyboards")
out.mkdir(exist_ok=True)
if not scorecard.exists():
    raise SystemExit("Missing trend scorecard.")
rows = []
for line in scorecard.read_text(encoding="utf-8").splitlines():
    m = re.match(r"^(\d+)\.\s*(.*?)\s*\|\s*markets=([^|]+)\|\s*score=(\d+)(.*)$", line)
    if not m:
        continue
    rank, topic, markets, score, extra = m.groups()
    rows.append({"trend_rank": int(rank), "topic": topic.strip(),
                 "markets": [x.strip() for x in markets.split(",") if x.strip()],
                 "trend_score": int(score)})
    if len(rows) >= 8:
        break
if not rows:
    m = re.search(r"^Selected topic:\s*(.+)$", scorecard.read_text(encoding="utf-8"), re.M)
    if m:
        rows = [{"trend_rank": 1, "topic": m.group(1).strip(), "markets": [], "trend_score": 0}]
if not rows:
    raise SystemExit("No topics parsed from trend scorecard.")
for item in rows:
    topic = item["topic"]
    safe = re.sub(r"[^a-z0-9]+", "-", topic.casefold()).strip("-")[:65] or "topic"
    plan = {
        "topic": topic, "trend_rank": item["trend_rank"], "markets": item["markets"],
        "trend_score": item["trend_score"],
        "status": "EARLY HYPOTHESIS — not researched, not fact-checked, no media or rights verified",
        "story_angle": "Find the most surprising, useful or entertaining verified detail; do not assume a viral angle.",
        "audience_promise": "In under a minute, explain one specific question viewers are likely to care about.",
        "scenes": [
            {"scene": 1, "seconds": 3, "purpose": "Hook", "draft": "The question or unexpected detail that makes this topic worth watching.", "visual_need": "A specific visual that immediately signals the topic."},
            {"scene": 2, "seconds": 8, "purpose": "Context", "draft": "What viewers need to understand before the reveal.", "visual_need": "Relevant establishing footage, image or simple graphic."},
            {"scene": 3, "seconds": 12, "purpose": "Evidence and reveal", "draft": "The most interesting fact, conflict or change—TBD after research.", "visual_need": "A visual directly supporting the verified detail."},
            {"scene": 4, "seconds": 8, "purpose": "Payoff", "draft": "Explain why the reveal matters and what it changes.", "visual_need": "Comparison, demonstration or sourced image."},
            {"scene": 5, "seconds": 4, "purpose": "Close", "draft": "One specific question to invite meaningful comments.", "visual_need": "Clear end card."}],
        "validation_questions": ["Can the hook be supported by reliable evidence?", "Can the story be told clearly in 30–60 seconds?", "Are there enough relevant visuals to make it competitive?", "Can assets be used lawfully at $0?", "Is there a distinctive angle beyond repeating existing videos?"]
    }
    (out / f"{item['trend_rank']:02d}-{safe}.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
(out / "index.md").write_text("# Preliminary storyboard hypotheses\n\nThese are hypotheses created before research and media comparison. They are not scripts.\n\n" + "\n".join(f"- Rank {x['trend_rank']}: {x['topic']}" for x in rows) + "\n", encoding="utf-8")
print(f"Created {len(rows)} preliminary storyboard hypotheses.")
