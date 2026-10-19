#!/usr/bin/env python3
"""Build a zero-cost original-video brief from the weekly discovery results.

This creates a production brief only. It does not download, copy, or upload other
creators' videos. The creator should use original narration, commentary, visuals,
or assets they have permission to use.
"""
import os
from pathlib import Path

topic = os.getenv("DISCOVERY_TOPIC", "topic to validate").strip()
result_path = Path("discovery-playlist-result.txt")
result = result_path.read_text(encoding="utf-8") if result_path.exists() else ""
lines = result.splitlines()
video_titles = []
for line in lines:
    if line.startswith("Title:") or line.startswith("Topic:") or line.startswith("Playlist:") or line.startswith("Privacy:") or line.startswith("Videos added:") or line.startswith("Views:") or not line.strip():
        continue
    if line.startswith("http") or line == "FAILED":
        continue
    if line.startswith("ERROR:"):
        continue
    # Keep likely video-title lines only when followed by a YouTube URL.
    idx = lines.index(line) if line in lines else -1
    if idx >= 0 and idx + 1 < len(lines) and lines[idx + 1].startswith("https://www.youtube.com/watch?v="):
        video_titles.append(line)

video_titles = list(dict.fromkeys(video_titles))[:5]
safe_topic = topic[:1].upper() + topic[1:] if topic else "Topic"

brief = f"""# Original-video opportunity brief: {safe_topic}

**Status:** research brief only — no video has been produced or uploaded  
**Budget:** $0  
**Source topic:** {topic}

## What the discovery test found
The automated workflow selected **{topic}** as this cycle's topic. The public playlist contains {len(video_titles)} selected reference videos (when available). Views-per-day figures are rough lifetime averages, not proof of current trend velocity.

"""
if video_titles:
    brief += "\n".join(f"- {title}" for title in video_titles) + "\n"
else:
    brief += "The playlist result did not provide a usable list of video titles. Check the workflow summary before deciding whether to proceed.\n"

brief += f"""
## Original concept to test
Create a short, original explainer or commentary video about **{topic}**. Do not simply compile, re-upload, or narrate the reference videos. The angle should add a clear new value: an explanation, comparison, ranking with stated criteria, myth check, useful guide, or original comedic take.

## Draft structure (45–75 seconds)
1. **0–3s — Hook:** State a surprising question or promise connected to {topic}.
2. **3–12s — Context:** Explain why a viewer should care; avoid claiming a trend is current unless separately verified.
3. **12–45s — Three original points:** Give useful facts, observations, or a clearly labelled opinion. Verify factual claims before recording.
4. **45–60s — Payoff:** Deliver the answer, twist, comparison, or takeaway promised in the hook.
5. **Final 5–10s — Engagement:** Ask one specific question viewers can answer in comments.

## Free production plan
- **Script:** draft and revise in ChatGPT.
- **Visuals:** use self-created text/graphics, your own footage, or assets whose licence permits the intended use.
- **Editing:** use a free mobile editor and simple captions; avoid credit-limited AI generation for the first test.
- **Audio:** use your own voice or properly licensed audio; check attribution requirements.
- **Publishing:** keep as a draft until a human has checked the facts, rights, captions, and final export.

## Rights and quality gate
- [ ] The script adds original commentary or information; it is not a lightly altered copy.
- [ ] Every visual and audio element is owned, licensed, or used with a valid permission/legal basis.
- [ ] No unlicensed source video or music is re-uploaded.
- [ ] Claims are checked and the opening matches the actual payoff.
- [ ] Title and thumbnail are accurate, not misleading.
- [ ] Human review completed before upload.

## Test measurement
Record results at 24 hours and 7 days: impressions, click-through rate (if available), views, average view duration/retention, comments, and subscribers gained. Compare the result with the channel's own baseline; one video is not enough to establish a winner.

## Next decision
Only produce the full video after reviewing the topic scorecard and confirming that the idea can be made distinctly original with free resources. This workflow does not publish videos automatically.
"""
Path("original-content-brief.md").write_text(brief, encoding="utf-8")
print("Created original-content-brief.md")
