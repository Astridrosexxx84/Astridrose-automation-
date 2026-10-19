#!/usr/bin/env python3
"""Turn the rights-review CSV into an edit-plan template. Never approves or downloads media."""
import csv, json
from pathlib import Path

queue = Path("topic-audit/footage-review-queue.csv")
out = Path("footage-edit-plan.json")
if not queue.exists():
    raise SystemExit("Missing topic-audit/footage-review-queue.csv; run the topic viability audit first.")
clips = []
with queue.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        # Only include candidates with explicit licence metadata as leads; human review still required.
        if "HUMAN_REVIEW_REQUIRED" not in row.get("status", ""):
            continue
        clips.append({
            "candidate_title": row.get("title", ""),
            "direct_url": row.get("file_url", ""),
            "source_url": row.get("item_page", ""),
            "license": row.get("license", ""),
            "license_url": row.get("license_url", ""),
            "creator": row.get("creator", ""),
            "attribution": "",
            "start_seconds": 0,
            "duration_seconds": 5,
            "approved_for_reuse": False,
            "review_notes": "Inspect the source page, exact licence, commercial/adaptation permissions, audio, people, trademarks, and topic relevance. Do not set approved_for_reuse true until reviewed."
        })
plan = {
    "topic": "Review candidates and enter the selected topic",
    "narration": "",
    "clips": clips,
    "notice": "Generated from candidate metadata only. No clip is cleared, downloaded, or approved. Human review required."
}
out.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"plan_template": str(out), "candidate_count": len(clips), "approved_by_script": 0,
                  "note": "All entries remain approved_for_reuse=false. Fill missing fields and review rights manually."}))
