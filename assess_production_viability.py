#!/usr/bin/env python3
"""Conservative post-storyboard production gate. Scores evidence quality, not guaranteed virality."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("topic-audit")
STORYBOARDS = Path("storyboard-drafts")
OUT_JSON = ROOT / "production-viability.json"
OUT_MD = ROOT / "production-viability.md"

def tokens(value):
    return {w for w in re.findall(r"[a-z0-9]{3,}", str(value or "").casefold())
            if w not in {"the", "and", "for", "with", "from", "into", "this", "that", "news"}}

def candidate_check(row):
    topic = str(row.get("topic", "")).strip()
    research = row.get("research") or {}
    title = str(research.get("title", ""))
    extract = str(research.get("extract", ""))
    topic_words = tokens(topic)
    research_words = tokens(title + " " + extract)
    overlap = sorted(topic_words & research_words)
    # A short generic topic can match one word accidentally; require enough support.
    relevance = len(overlap) / max(1, len(topic_words))
    research_ok = research.get("status") == "found" and len(extract.strip()) >= 250 and relevance >= 0.34
    media = row.get("media_counts") or {}
    matched_leads = int(media.get("keyword_matched_leads", 0) or 0)
    distinct_sources = int(media.get("distinct_sources_with_keyword_matches", 0) or 0)
    video_leads = int(media.get("keyword_matched_video_file_candidates", 0) or 0)
    licensed_leads = int(media.get("keyword_matched_assets_with_license_metadata", 0) or 0)
    yt = row.get("youtube_discovery") or {}
    competitor_count = int(yt.get("result_count", 0) or 0)
    competitor_signal = competitor_count > 0 and yt.get("status") not in {
        "no_results_or_search_feed_unavailable", "unreadable", "not_run", "error"
    }
    reasons = []
    if not research_ok:
        reasons.append("Research relevance/depth is insufficient for this topic; verify the exact subject and add reliable sources.")
    if matched_leads < 3 or distinct_sources < 2:
        reasons.append("Relevant media coverage is thin or concentrated; inspect original item pages and consider other sources.")
    if video_leads == 0:
        reasons.append("No keyword-matched video-file leads were found; a still-image/graphics-led angle may be needed.")
    if licensed_leads == 0:
        reasons.append("No keyword-matched assets have explicit licence metadata; rights review is still mandatory.")
    if not competitor_signal:
        reasons.append("The free YouTube scout returned no usable competitor/demand sample, so relative competitiveness cannot yet be assessed.")
    if research_ok and matched_leads >= 3 and distinct_sources >= 2 and licensed_leads > 0 and competitor_signal:
        status = "ELIGIBLE_FOR_HUMAN_PRODUCTION_REVIEW"
    elif not research_ok:
        status = "RESEARCH_OR_TOPIC_MISMATCH"
    else:
        status = "HOLD_FOR_EVIDENCE"
    score = 0
    score += 30 if research_ok else 0
    score += 20 if matched_leads >= 3 and distinct_sources >= 2 else (10 if matched_leads >= 1 else 0)
    score += 10 if video_leads >= 2 else (5 if video_leads == 1 else 0)
    score += 10 if licensed_leads > 0 else 0
    score += 20 if competitor_signal else 0
    score += 10 if row.get("decision") == "CONDITIONAL_REVIEW" else 0
    storyboard_path = STORYBOARDS / re.sub(r"[^a-z0-9]+", "-", topic.casefold()).strip("-")[:70] / "storyboard.md"
    return {
        "topic": topic, "trend_rank": row.get("trend_rank"), "initial_score_out_of_100": row.get("score_out_of_100", 0),
        "production_gate_score_out_of_100": score, "status": status,
        "research": {"title": title, "url": research.get("url"), "character_count": len(extract.strip()),
                     "topic_keyword_overlap": overlap, "relevance_ratio": round(relevance, 3), "passed": research_ok},
        "media": {"keyword_matched_leads": matched_leads, "distinct_sources": distinct_sources,
                  "video_file_leads": video_leads, "assets_with_explicit_licence_metadata": licensed_leads},
        "competition": {"youtube_scout_status": yt.get("status", "unknown"),
                        "sample_count": competitor_count, "assessable": competitor_signal},
        "storyboard_exists": storyboard_path.exists(),
        "reasons": reasons,
        "next_action": "Human review only; no automatic publishing or rights clearance." if status == "ELIGIBLE_FOR_HUMAN_PRODUCTION_REVIEW" else "Hold full production; fix the listed evidence gaps or choose another topic."
    }

def main():
    source = ROOT / "shortlist-comparison.json"
    if not source.exists():
        raise SystemExit("topic-audit/shortlist-comparison.json missing; run the research/media audit first.")
    payload = json.loads(source.read_text(encoding="utf-8"))
    results = [candidate_check(r) for r in payload.get("results", []) if isinstance(r, dict)]
    results.sort(key=lambda x: (x["production_gate_score_out_of_100"], -int(x.get("trend_rank") or 999)), reverse=True)
    output = {"assessed_at_utc": datetime.now(timezone.utc).isoformat(),
              "purpose": "Conservative evidence gate, not a prediction of virality or legal clearance.",
              "full_production_auto_approved": False, "public_publishing_enabled": False,
              "candidate_count": len(results), "eligible_for_human_production_review": sum(x["status"] == "ELIGIBLE_FOR_HUMAN_PRODUCTION_REVIEW" for x in results),
              "results": results}
    OUT_JSON.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["# Production viability gate", "", f"- Assessed (UTC): {output['assessed_at_utc']}",
             f"- Candidates: {len(results)}", f"- Eligible for human production review: {output['eligible_for_human_production_review']}",
             "- **No candidate is automatically approved for production or publishing.**",
             "- A missing YouTube sample means competitiveness is unknown, not that demand is absent.", "", 
             "| Priority | Topic | Gate score | Status | Research match | Media leads | Video leads | Competitor sample |",
             "|---:|---|---:|---|---:|---:|---:|---:|"]
    for i, r in enumerate(results, 1):
        lines.append(f"| {i} | {r['topic'].replace('|', '/')} | {r['production_gate_score_out_of_100']} | {r['status']} | {r['research']['relevance_ratio']:.0%} | {r['media']['keyword_matched_leads']} | {r['media']['video_file_leads']} | {r['competition']['sample_count']} |")
    for r in results:
        lines += ["", f"## {r['topic']}", "", f"**Gate:** {r['status']} — {r['next_action']}", ""]
        lines += [f"- {reason}" for reason in (r["reasons"] or ["Evidence checks passed; human review remains required."])]
        lines += [f"- Research source: {r['research']['url'] or 'not supplied'}",
                  f"- Research title: {r['research']['title'] or 'not supplied'}",
                  f"- Storyboard exists: {'yes' if r['storyboard_exists'] else 'no'}"]
    lines += ["", "## How to use this gate", "",
              "Research relevance, independent media coverage, reusable-licence leads and a competitor sample are separate checks. Search-result counts and keyword overlap are only triage signals. A human must inspect the evidence, confirm the story is distinctive and achievable with free tools, and approve the production brief. If any major evidence source is missing, research more, change the angle or drop the topic."]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"candidates": len(results), "eligible_for_human_production_review": output["eligible_for_human_production_review"],
                      "report": str(OUT_MD), "json": str(OUT_JSON)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
