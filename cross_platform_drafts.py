"""Turn the 30-day calendar into platform-specific draft packs. Never publishes."""
import re
from pathlib import Path

SOURCE = Path("30_DAY_CONTENT_CALENDAR.md")
OUTPUT = Path("cross-platform-draft-pack.md")
PLATFORMS = {
    "Bluesky": "Keep it conversational; use a short standalone post and at most one relevant hashtag.",
    "Threads": "Use a conversational opener; invite a genuine response without engagement bait.",
    "X": "Keep the hook concise and self-contained; avoid repetitive hashtags.",
    "Instagram": "Use as a caption for an original image or Reel; add alt text to media and only relevant hashtags.",
    "Facebook": "Use a friendly, slightly fuller caption; publish only to a profile/page where this content is welcome.",
    "TikTok": "Use as a spoken/video hook or caption; pair with original video, not text-only reposts pretending to be video.",
    "YouTube Shorts": "Use as a short-video concept or opening line; add a clear title and accurate description.",
    "Pinterest": "Turn the idea into a useful visual/story pin; write a descriptive title and destination only when relevant.",
    "LinkedIn": "Use only for creator-business/process insights; skip flirtatious drafts that do not fit professional context.",
    "Reddit": "Rewrite for the specific community, disclose promotion where required, and post only where the rules allow it.",
}

def read_calendar():
    rows = []
    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("|---") or "| Day |" in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 5 and cells[0].isdigit():
            rows.append({"day": cells[0], "format": cells[1], "copy": cells[2], "goal": cells[3], "measure": cells[4]})
    return rows

def main():
    rows = read_calendar()
    if not rows:
        raise SystemExit("No calendar rows found; refusing to create an empty draft pack.")
    out = [
        "# Cross-platform draft pack", "",
        f"Generated from {len(rows)} calendar entries. Drafts only: nothing is published or scheduled by this script.", "",
        "## Important", "",
        "Use one idea as the source, but adapt it to the platform instead of blindly duplicating posts. Follow platform rules for adult themes, automation, and promotion. Add links only where permitted. For video platforms, these are hooks/concepts—not finished videos.", "",
    ]
    for row in rows:
        out.extend([f"## Day {row['day']} — {row['format']}", "", f"**Source idea:** {row['copy']}", "", f"**Goal:** {row['goal']} | **Measure:** {row['measure']}", ""])
        for name, guidance in PLATFORMS.items():
            copy = row["copy"]
            if name == "YouTube Shorts":
                copy = f"Short idea/title: {copy}"
            elif name == "TikTok":
                copy = f"Video hook: {copy}"
            elif name == "Pinterest":
                copy = f"Pin concept: {copy}"
            elif name == "LinkedIn" and row["format"] not in ("Behind the scenes", "Process", "Weekly recap", "Review"):
                copy = "[Skip unless reframed as a relevant creator-business lesson.]"
            elif name == "Reddit":
                copy = "[Rewrite to fit the chosen community; do not paste promotional copy unchanged.]"
            out.extend([f"### {name}", copy, f"*Adaptation note: {guidance}*", ""])
    OUTPUT.write_text("\n".join(out), encoding="utf-8")
    print(f"Created {OUTPUT}: {len(rows)} ideas across {len(PLATFORMS)} platforms.")

if __name__ == "__main__":
    main()
