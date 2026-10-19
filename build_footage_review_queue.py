#!/usr/bin/env python3
"""Make a conservative footage queue from audit JSON. Never downloads or clears clips."""
import csv, json, re
from pathlib import Path

ROOT = Path("topic-audit")
OUT = ROOT / "footage-review-queue.csv"
VIDEO_EXTS = (".mp4", ".m4v", ".webm", ".ogv", ".mov")
VIDEO_MIMES = ("video/", "mpeg4", "h.264", "quicktime", "webm", "ogg")

def is_video(asset):
    mime = str(asset.get("mime") or asset.get("media_type") or "").casefold()
    name = str(asset.get("file_name") or asset.get("title") or "").casefold()
    url = str(asset.get("file_url") or "").split("?", 1)[0].casefold()
    return any(x in mime for x in VIDEO_MIMES) or name.endswith(VIDEO_EXTS) or url.endswith(VIDEO_EXTS)

def explicit_license(asset):
    lic = str(asset.get("license") or "").strip().casefold()
    url = str(asset.get("license_url") or "").strip()
    # Exclude generic/unknown labels. This is only a lead for human review, not clearance.
    known = ("cc0", "public domain", "cc by", "cc by-sa", "creative commons attribution")
    return bool(url and any(lic == x or lic.startswith(x + " ") or lic.startswith(x + "-") for x in known))

def main():
    rows = []
    for path in sorted(ROOT.glob("**/audit.json")):
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        topic = report.get("topic") or path.parent.name
        for asset in report.get("assets", []):
            if not is_video(asset):
                continue
            licensed = explicit_license(asset)
            rows.append({
                "topic": topic,
                "source": asset.get("source", ""),
                "title": asset.get("title", ""),
                "item_page": asset.get("page_url", ""),
                "file_url": asset.get("file_url", ""),
                "mime": asset.get("mime", ""),
                "creator": asset.get("creator", ""),
                "license": asset.get("license", ""),
                "license_url": asset.get("license_url", ""),
                "keyword_overlap": asset.get("topic_keyword_overlap", ""),
                "status": "HUMAN_REVIEW_REQUIRED — licence metadata present" if licensed else "REJECT_FOR_AUTOMATED_USE — no explicit reusable licence metadata"
            })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = ["topic","source","title","item_page","file_url","mime","creator","license","license_url","keyword_overlap","status"]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    summary = {
        "video_file_candidates": len(rows),
        "explicit_license_leads_for_human_review": sum("HUMAN_REVIEW_REQUIRED" in r["status"] for r in rows),
        "rejected_for_automated_use_missing_explicit_license": sum("REJECT_FOR_AUTOMATED_USE" in r["status"] for r in rows),
        "automatically_cleared": 0,
        "report": str(OUT),
        "note": "File extension/MIME and search relevance do not prove a clip is playable, relevant, downloadable or reusable. Human must inspect item page and exact licence. No clip was downloaded."
    }
    (ROOT / "footage-review-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary))
if __name__ == "__main__":
    main()
