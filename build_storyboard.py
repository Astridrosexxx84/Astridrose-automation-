#!/usr/bin/env python3
"""Turn preliminary topic audits into transparent storyboard drafts (never rights-cleared)."""
import json
import re
from pathlib import Path

ROOT = Path("topic-audit")
OUT = Path("storyboard-drafts")

def clean(value, limit=500):
    return re.sub(r"\\s+", " ", str(value or "")).strip()[:limit]

def build(report, folder):
    topic = clean(report.get("topic"), 120) or "Unspecified topic"
    research = report.get("research") or {}
    extract = clean(research.get("extract"), 1400)
    research_url = clean(research.get("url"), 500)
    assets = report.get("assets") or []
    topic_terms = {w.casefold() for w in re.findall(r"[a-zA-Z0-9]{3,}", topic)}
    leads = []
    for asset in assets:
        overlap = clean(asset.get("topic_keyword_overlap"))
        status = clean(asset.get("relevance_status"))
        if not status:
            status = "RELEVANCE_NOT_ESTABLISHED"
        if overlap or status == "KEYWORD_MATCH_REVIEW_REQUIRED":
            leads.append({
                "source": clean(asset.get("source"), 100),
                "title": clean(asset.get("title"), 240),
                "page_url": clean(asset.get("page_url"), 500),
                "file_url": clean(asset.get("file_url"), 500),
                "media_type": clean(asset.get("media_type") or asset.get("mime"), 100),
                "creator": clean(asset.get("creator"), 160),
                "license": clean(asset.get("license"), 160),
                "license_url": clean(asset.get("license_url"), 500),
                "keyword_overlap": overlap,
                "relevance_status": status,
                "rights_status": "UNVERIFIED — human item-level review required"
            })
    leads = leads[:12]
    storyboard = {
        "topic": topic,
        "audit_decision": report.get("decision", "UNKNOWN"),
        "research_source": research_url,
        "research_status": research.get("status", "unknown"),
        "research_excerpt": extract,
        "storyboard_status": "PRELIMINARY DRAFT — not fact-checked, media not verified, rights not cleared",
        "automatic_rights_clearance": False,
        "scenes": [
            {"scene": 1, "purpose": "Hook", "duration_seconds": 5,
             "narration_draft": f"What is the most interesting question about {topic}?",
             "visual": "Use a verified, relevant establishing image/video only after checking the source page and rights.",
             "evidence_needed": "Choose a specific question supported by the research; do not imply an unverified claim."},
            {"scene": 2, "purpose": "Context", "duration_seconds": 12,
             "narration_draft": extract[:450] if extract else "Research summary unavailable; add verified context before scripting.",
             "visual": "Candidate media lead(s) may illustrate context only after relevance, playback and rights checks.",
             "evidence_needed": "Check every factual statement against the linked research and preferably a second reliable source."},
            {"scene": 3, "purpose": "The detail", "duration_seconds": 12,
             "narration_draft": "Find one specific, surprising detail in the source material, then explain why it matters.",
             "visual": "Select a real image/clip or document detail that directly supports the fact; otherwise use a clearly labelled graphic.",
             "evidence_needed": "Not yet selected; this is a research task, not a claim."},
            {"scene": 4, "purpose": "Payoff", "duration_seconds": 10,
             "narration_draft": "Connect the evidence to a clear takeaway, noting uncertainty or competing interpretations where relevant.",
             "visual": "Use a simple timeline, map, comparison or sourced image only when it improves understanding.",
             "evidence_needed": "Add citations and verify any dates, numbers, quotes and interpretations."},
            {"scene": 5, "purpose": "Close", "duration_seconds": 5,
             "narration_draft": "What question should we investigate next?",
             "visual": "End card with one specific audience question.",
             "evidence_needed": "No factual claim."}
        ],
        "media_leads": leads,
        "required_checks_before_render": [
            "Verify relevance on the original item page; keyword overlap is not proof.",
            "Check the actual file plays and is downloadable; a search result or URL alone is insufficient.",
            "Verify item-level licence/rights permits intended reuse, adaptation and commercial use; record attribution.",
            "Check third-party rights, music, logos, identifiable people and source restrictions.",
            "Fact-check every narration line against reliable sources and add citations.",
            "If usable footage is missing, use licensed/public-domain stills, original graphics or a newly researched angle."
        ],
        "limitations": [
            "This is a structure draft, not a completed script or finished video.",
            "No assets are automatically approved or rights-cleared.",
            "Research excerpts are preliminary and must be independently fact-checked.",
            "No video is downloaded, edited, uploaded or published by this script."
        ]
    }
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "storyboard.json").write_text(json.dumps(storyboard, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        f"# Storyboard draft: {topic}", "",
        f"- Audit decision: {storyboard['audit_decision']}",
        f"- Research: {research_url or 'No research URL returned'}",
        "- Status: **PRELIMINARY — not fact-checked; media and rights not verified**",
        "- Planned duration: about 44 seconds", "",
        "## Research starting point", "", extract or "No research excerpt returned; research is required before scripting.", "",
        "## Scene plan", ""
    ]
    for scene in storyboard["scenes"]:
        lines += [f"### Scene {scene['scene']} — {scene['purpose']} ({scene['duration_seconds']} sec)",
                  f"**Draft narration:** {scene['narration_draft']}",
                  f"**Visual direction:** {scene['visual']}",
                  f"**Evidence needed:** {scene['evidence_needed']}", ""]
    lines += ["## Candidate media leads (not approved)", ""]
    if not leads:
        lines += ["No keyword-matched media leads were found in the audit. Do not invent or substitute unrelated footage.", ""]
    for i, lead in enumerate(leads, 1):
        lines += [f"{i}. **{lead['title'] or 'Untitled item'}** — {lead['source'] or 'unknown source'}",
                  f"   - Item page: {lead['page_url'] or 'not supplied'}",
                  f"   - File lead: {lead['file_url'] or 'not supplied'}",
                  f"   - Creator/licence: {lead['creator'] or 'unknown'} / {lead['license'] or 'unknown'}",
                  f"   - Licence details: {lead['license_url'] or 'not supplied'}",
                  f"   - Keyword overlap: {lead['keyword_overlap'] or 'not recorded'}",
                  "   - **Rights/relevance status: unverified; do not use until checked.**", ""]
    lines += ["## Mandatory checks before rendering", ""]
    lines += [f"- [ ] {item}" for item in storyboard["required_checks_before_render"]]
    lines += ["", "## Limitations", ""] + [f"- {item}" for item in storyboard["limitations"]]
    (folder / "storyboard.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return folder

def main():
    if not ROOT.exists():
        raise SystemExit("topic-audit/ not found; run the topic viability audit first.")
    reports = list(ROOT.glob("topic-audit.json")) + list(ROOT.glob("candidates/*/audit.json"))
    if not reports:
        raise SystemExit("No audit JSON found; no storyboard draft created.")
    made = 0
    for path in reports:
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
            topic = clean(report.get("topic") or (report.get("results") or [{}])[0].get("topic"), 120)
            if not report.get("topic") and report.get("results"):
                # Shortlist comparison: create a draft for each audited candidate, preserving its own evidence.
                for candidate in report["results"]:
                    if candidate.get("assets") or candidate.get("research"):
                        slug = re.sub(r"[^a-z0-9]+", "-", clean(candidate.get("topic"), 120).casefold()).strip("-")[:70] or "topic"
                        build(candidate, OUT / slug)
                        made += 1
                continue
            slug = re.sub(r"[^a-z0-9]+", "-", topic.casefold()).strip("-")[:70] or "topic"
            build(report, OUT / slug)
            made += 1
        except (OSError, ValueError, TypeError) as exc:
            print(f"Skipping {path}: {exc}")
    if not made:
        raise SystemExit("No storyboard drafts could be built.")
    print(f"Created {made} preliminary storyboard draft(s) under {OUT}/; none are fact-checked or rights-cleared.")

if __name__ == "__main__":
    main()
