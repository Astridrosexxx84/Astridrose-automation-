#!/usr/bin/env python3
"""Create a human-review queue for source assets; never grants rights clearance."""
import csv
import json
from pathlib import Path

ROOT = Path("topic-audit")
OUT = ROOT / "rights-review-queue.csv"

FIELDS = [
    "topic", "source", "title", "page_url", "file_url", "creator",
    "license", "license_url", "audit_relevance", "initial_gate",
    "commercial_use_checked", "adaptation_checked", "attribution_checked",
    "playback_checked", "editorial_purpose", "alternative", "human_decision",
    "reviewer", "review_date", "notes"
]

def gate(asset):
    licence = str(asset.get("license") or "").strip().casefold()
    licence_url = str(asset.get("license_url") or "").strip()
    if not licence or licence in {"unknown", "n/a", "none", "not provided", "see item metadata"}:
        return "AMBER — no licence/permission established"
    if "public domain" in licence or "cc0" in licence:
        return "GREEN CANDIDATE — verify original item page/source"
    if "cc by" in licence or "creative commons" in licence:
        return "GREEN CANDIDATE — verify exact terms, attribution, adaptations/share-alike"
    return "AMBER — inspect exact terms; do not assume reuse permission"

def main():
    if not ROOT.exists():
        raise SystemExit("topic-audit directory is missing")
    reports = list(ROOT.glob("topic-audit.json")) + list(ROOT.glob("candidates/*/audit.json"))
    rows = []
    for path in reports:
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        topic = report.get("topic") or path.parent.name
        for asset in report.get("assets") or []:
            rows.append({
                "topic": topic,
                "source": asset.get("source", ""),
                "title": asset.get("title", ""),
                "page_url": asset.get("page_url", ""),
                "file_url": asset.get("file_url", ""),
                "creator": asset.get("creator", ""),
                "license": asset.get("license", ""),
                "license_url": asset.get("license_url", ""),
                "audit_relevance": asset.get("relevance_status", "REVIEW REQUIRED"),
                "initial_gate": gate(asset),
                "commercial_use_checked": "NO",
                "adaptation_checked": "NO",
                "attribution_checked": "NO",
                "playback_checked": "NO",
                "editorial_purpose": "",
                "alternative": "",
                "human_decision": "PENDING",
                "reviewer": "",
                "review_date": "",
                "notes": "Search result metadata is not legal clearance. Check the original item page."
            })
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} asset rows to {OUT}; none are automatically cleared.")

if __name__ == "__main__":
    main()
