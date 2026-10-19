#!/usr/bin/env python3
"""Compare a shortlist of free trend candidates before choosing a video topic.

Uses public unauthenticated APIs only. This is triage, not automated rights clearance.
No YouTube Search API, media downloads, AI generation, playlist changes, or publishing.
"""
import csv
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import topic_viability_audit as audit

SCORECARD = Path("topic-discovery-scorecard.txt")
OUT = Path("topic-audit")
MAX_CANDIDATES = 10
STOPWORDS = {"about", "after", "again", "against", "among", "because", "before", "being",
             "between", "could", "first", "from", "have", "into", "more", "most", "other",
             "over", "same", "some", "than", "that", "their", "there", "these", "they",
             "this", "those", "through", "under", "very", "what", "when", "where", "which",
             "while", "with", "would", "your", "live", "news", "official"}

def tokens(value):
    words = re.findall(r"[a-z0-9]{3,}", unicodedata.normalize("NFKD", value.casefold()))
    return {w for w in words if w not in STOPWORDS}

def read_candidates():
    if not SCORECARD.exists():
        raise RuntimeError("Trend scorecard missing; run free_trend_selector.py first.")
    candidates = []
    for line in SCORECARD.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^(\d+)\.\s*(.*?)\s*\|\s*markets=([^|]+)\s*\|\s*score=(\d+)", line)
        if not match:
            continue
        rank, topic, markets, raw_score = match.groups()
        if topic and all(c["topic"].casefold() != topic.casefold() for c in candidates):
            candidates.append({"trend_rank": int(rank), "topic": topic,
                               "markets": [m.strip() for m in markets.split(",") if m.strip()],
                               "trend_raw_score": int(raw_score)})
        if len(candidates) >= MAX_CANDIDATES:
            break
    if not candidates:
        raise RuntimeError("No candidate topics could be parsed from the trend scorecard.")
    return candidates

def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", value.casefold())).strip("-")
    return slug[:70] or "topic"

def audit_candidate(candidate):
    topic = candidate["topic"]
    research = audit.wikipedia_research(topic)
    commons, commons_error = audit.commons_media(topic, limit=10)
    nasa, nasa_error = audit.nasa_media(topic, limit=10)
    openverse, openverse_error = audit.openverse_media(topic, limit=8)
    loc, loc_error = audit.loc_media(topic, limit=8)
    archive, archive_error = audit.internet_archive_media(topic, limit=8)
    assets = commons + nasa + openverse + loc + archive
    topic_terms = tokens(topic)
    relevant = []
    for asset in assets:
        searchable = " ".join(str(asset.get(k, "")) for k in ("title", "description", "creator"))
        overlap = sorted(topic_terms & tokens(searchable))
        asset["topic_keyword_overlap"] = ", ".join(overlap)
        asset["relevance_status"] = "KEYWORD_MATCH_REVIEW_REQUIRED" if overlap else "RELEVANCE_NOT_ESTABLISHED"
        if overlap:
            relevant.append(asset)

    research_chars = len(research.get("extract", "").strip())
    research_score = 2 if research["status"] == "found" and research_chars >= 250 else (1 if research_chars else 0)
    media_score = 0 if not relevant else (1 if len(relevant) <= 2 else 2)
    rights_score = 0 if not assets else 1
    feasibility_score = 3 if relevant and research_chars >= 250 else (2 if relevant or research_chars else 0)
    market_count = len(candidate["markets"])
    rank = candidate["trend_rank"]
    trend_score = 5 if market_count >= 4 and rank <= 5 else 4 if market_count >= 3 and rank <= 10 else 3 if market_count >= 2 else 2 if market_count >= 1 else 0
    weighted = round((trend_score * 25 + research_score * 20 + media_score * 30 + rights_score * 15 + feasibility_score * 10) / 5)
    decision = "CONDITIONAL_REVIEW" if relevant and research_chars >= 250 else "HOLD_OR_RESELECT"
    reason = ("Research and keyword-matched media leads exist, but relevance, usable video coverage, stock-media supply and item-level rights still require human review."
              if decision == "CONDITIONAL_REVIEW" else
              "Automated evidence is currently thin: research extract and/or topic-keyword-matched media leads are insufficient.")
    record = {
        **candidate, "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision, "decision_reason": reason, "score_out_of_100": weighted,
        "score_components_0_to_5": {"audience_signal": trend_score, "research_depth": research_score,
            "media_inventory": media_score, "rights_readiness": rights_score, "production_feasibility": feasibility_score},
        "research": research,
        "media_counts": {"commons_search_results": len(commons),
            "commons_with_licence_metadata": sum(1 for x in commons if x.get("license") and x.get("license_url")),
            "nasa_search_results": len(nasa), "openverse_image_results": len(openverse),
            "loc_results": len(loc), "internet_archive_results": len(archive), "keyword_matched_leads": len(relevant),
            "automatically_cleared_assets": 0},
        "errors": {"commons": commons_error, "nasa": nasa_error, "openverse": openverse_error, "loc": loc_error, "internet_archive": archive_error},
        "assets": assets,
        "search_links": audit.search_links(topic),
        "limitations": ["Keyword overlap is a weak relevance heuristic, not semantic verification.",
            "Search results are leads, not proof that assets are usable, downloadable or reusable.",
            "Openverse adds image discovery only; it is not a video source in this pipeline.",
            "Library of Congress and Internet Archive records may have unclear rights or downloadability; review each item.",
            "Stock-video libraries and playable/downloadable video coverage are not yet audited.",
            "Licence metadata is not legal clearance; every selected asset needs item-level review.",
            "No candidate is automatically approved for scripting or storyboarding."]
    }
    folder = OUT / "candidates" / slugify(topic)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "audit.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    with (folder / "media-inventory.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["source", "title", "page_url", "file_url", "file_name", "preview_url", "mime", "runtime", "retrieval_status", "media_type",
                  "creator", "license", "license_url", "date_created", "topic_keyword_overlap",
                  "relevance_status", "rights_status", "rights_note"]
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(assets)
    return record

def main():
    candidates = read_candidates()
    results = []
    for i, candidate in enumerate(candidates, 1):
        print(f"[{i}/{len(candidates)}] Auditing: {candidate['topic']}", flush=True)
        try:
            results.append(audit_candidate(candidate))
        except Exception as exc:
            results.append({**candidate, "decision": "AUDIT_ERROR", "score_out_of_100": 0,
                            "decision_reason": f"{type(exc).__name__}: {exc}",
                            "score_components_0_to_5": {}, "media_counts": {}, "errors": {"audit": str(exc)}})
            print(f"Candidate audit error for {candidate['topic']}: {type(exc).__name__}: {exc}", file=sys.stderr)
    results.sort(key=lambda x: (x.get("score_out_of_100", 0), -x["trend_rank"]), reverse=True)
    payload = {"audited_at_utc": datetime.now(timezone.utc).isoformat(),
               "candidates_audited": len(results), "automatic_winner_selection": False,
               "results": results,
               "selection_rule": "Use scores to prioritise human review only. Do not storyboard until relevant media, stock coverage and item-level rights are checked."}
    (OUT / "shortlist-comparison.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["# Trend shortlist: research and free-media viability", "",
        f"- Audited at (UTC): {payload['audited_at_utc']}",
        f"- Candidates audited: {len(results)}",
        "- **No automatic winner is selected.** Scores only prioritise human review.",
        "- All assets remain uncleared. Topic-specific and stock-video coverage and exact rights need human verification.", "",
        "## Comparison", "",
        "| Review priority | Trend rank | Topic | Score / 100 | Decision | Markets | Research | Commons | NASA | Openverse | LOC | Internet Archive | Keyword-matched leads |",
        "|---:|---:|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for priority, r in enumerate(results, 1):
        research_status = r.get("research", {}).get("status", "error")
        counts = r.get("media_counts", {})
        lines.append(f"| {priority} | {r['trend_rank']} | {r['topic'].replace('|', '/')} | {r.get('score_out_of_100', 0)} | {r.get('decision', 'AUDIT_ERROR')} | {', '.join(r.get('markets', []))} | {research_status} | {counts.get('commons_search_results', 0)} | {counts.get('nasa_search_results', 0)} | {counts.get('openverse_image_results', 0)} | {counts.get('loc_results', 0)} | {counts.get('internet_archive_results', 0)} | {counts.get('keyword_matched_leads', 0)} |")
    lines += ["", "## Interpretation and next gate", "",
        "A high trend rank does not automatically make a good video. The shortlist compares audience signal with a shallow research check and early media leads; keyword overlap is only a rough relevance hint.",
        "Before story writing, open each candidate's audit.json and media-inventory.csv, inspect the exact source pages, find credible primary sources, verify downloadable/playable footage and free stock coverage, and review item-level licences and third-party rights.",
        "If a candidate has weak or irrelevant media, reject it or change the angle. Do not spend AI credits or storyboard from search-result counts alone.", "",
        "## Per-candidate files", ""]
    for r in results:
        lines.append(f"- candidates/{slugify(r['topic'])}/audit.json and media-inventory.csv — {r['topic']}")
        links = r.get("search_links", {})
        for label in ("Official and primary sources", "Openverse openly licensed images", "Library of Congress", "Internet Archive movies and images", "Pexels videos", "Pixabay videos"):
            if label in links:
                lines.append(f"  - [{label}]({links[label]})")
    (OUT / "shortlist-comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Shortlist complete: {len(results)} candidates. No automatic winner selected.")
    print("Saved shortlist-comparison.md, shortlist-comparison.json, and per-candidate inventories.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: shortlist audit failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
