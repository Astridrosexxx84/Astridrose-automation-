#!/usr/bin/env python3
"""Research a candidate topic and audit likely free-media supply before story writing.

Uses public, unauthenticated APIs only. It never downloads/re-uploads third-party
videos, spends AI credits, calls YouTube Search, or publishes anything.
"""
import csv
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USER_AGENT = "AstridTopicViabilityAudit/1.0 (research-only; GitHub Actions)"
OUT = Path("topic-audit")
OUT.mkdir(exist_ok=True)


def get_json(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_topic():
    topic = os.getenv("AUDIT_TOPIC", "").strip()
    if topic:
        return topic
    scorecard = Path("topic-discovery-scorecard.txt")
    if scorecard.exists():
        match = re.search(r"^Selected topic:\s*(.+)$", scorecard.read_text(encoding="utf-8"), re.MULTILINE)
        if match:
            return match.group(1).strip()
    raise RuntimeError("No topic supplied and no Selected topic found in topic-discovery-scorecard.txt")


def wikipedia_research(topic):
    title = urllib.parse.quote(topic.replace(" ", "_"), safe="")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
    try:
        data = get_json(url)
        return {"status": "disambiguation" if data.get("type") == "disambiguation" else "found",
                "title": data.get("title", topic), "extract": data.get("extract", ""),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", url)}
    except Exception as exc:
        return {"status": "unavailable", "title": topic, "extract": "",
                "url": f"https://en.wikipedia.org/w/index.php?search={urllib.parse.quote(topic)}",
                "note": f"Automated summary unavailable: {type(exc).__name__}: {exc}"}


def commons_media(topic, limit=10):
    params = {"action": "query", "format": "json", "generator": "search",
              "gsrsearch": topic, "gsrnamespace": "6", "gsrlimit": str(limit),
              "prop": "imageinfo", "iiprop": "url|extmetadata"}
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    try:
        data = get_json(url)
        assets = []
        for page in data.get("query", {}).get("pages", {}).values():
            info = (page.get("imageinfo") or [{}])[0]
            meta = info.get("extmetadata", {})
            def val(key):
                item = meta.get(key, {})
                return re.sub(r"<[^>]+>", "", str(item.get("value", ""))).strip()
            license_name, license_url = val("LicenseShortName"), val("LicenseUrl")
            assets.append({"source": "Wikimedia Commons", "title": page.get("title", ""),
                           "page_url": info.get("descriptionurl", ""), "file_url": info.get("url", ""),
                           "mime": info.get("mime", ""), "creator": val("Artist"),
                           "license": license_name, "license_url": license_url, "credit": val("Credit"),
                           "rights_note": "Review exact file page, commercial/adaptation terms, attribution and third-party rights.",
                           "rights_status": "REVIEW_REQUIRED" if license_name and license_url else "LICENCE_UNVERIFIED"})
        return assets, None
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"


def nasa_media(topic, limit=10):
    params = {"q": topic, "media_type": "image,video", "page_size": str(limit)}
    url = "https://images-api.nasa.gov/search?" + urllib.parse.urlencode(params)
    try:
        data = get_json(url)
        assets = []
        for item in data.get("collection", {}).get("items", []):
            d = (item.get("data") or [{}])[0]
            links = item.get("links") or []
            preview = next((x.get("href") for x in links if x.get("rel") == "preview"), "")
            nasa_id = d.get("nasa_id", "")
            assets.append({"source": "NASA Image and Video Library", "title": d.get("title", ""),
                           "page_url": f"https://images.nasa.gov/details/{urllib.parse.quote(nasa_id, safe='')}" if nasa_id else url,
                           "preview_url": preview, "media_type": d.get("media_type", ""),
                           "date_created": d.get("date_created", ""),
                           "description": re.sub(r"\s+", " ", d.get("description", ""))[:500],
                           "rights_note": "Verify the individual asset, credit line, logos/people/third-party material, and NASA usage guidelines.",
                           "rights_status": "ITEM_LEVEL_REVIEW_REQUIRED"})
        return assets, None
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"


def search_links(topic):
    q = urllib.parse.quote_plus(topic)
    official_q = urllib.parse.quote_plus(topic + " official")
    return {"Web research": f"https://www.google.com/search?q={q}",
            "Official and primary sources": f"https://www.google.com/search?q={official_q}",
            "News coverage": f"https://news.google.com/search?q={q}",
            "Pexels videos": f"https://www.pexels.com/search/videos/{urllib.parse.quote(topic, safe='')}/",
            "Pixabay videos": f"https://pixabay.com/videos/search/{urllib.parse.quote(topic, safe='')}/",
            "YouTube reference research only": f"https://www.youtube.com/results?search_query={q}",
            "Google Trends explore": f"https://trends.google.com/trends/explore?q={q}"}


def main():
    topic = fetch_topic()
    research = wikipedia_research(topic)
    commons, commons_error = commons_media(topic)
    nasa, nasa_error = nasa_media(topic)
    assets = commons + nasa
    commons_licensed = sum(1 for x in commons if x.get("license") and x.get("license_url"))
    research_score = 4 if research["status"] == "found" and len(research.get("extract", "")) >= 250 else (2 if research.get("extract") else 1)
    media_score = min(5, (len(commons) + len(nasa)) // 3)
    rights_score = 1 if not assets else min(4, max(1, commons_licensed // 2 + (1 if nasa else 0)))
    feasibility_score = 4 if assets and research.get("extract") else (3 if assets or research.get("extract") else 1)
    trend_score = 0
    trend_evidence = "Not measured for manually entered topics."
    scorecard = Path("topic-discovery-scorecard.txt")
    if not os.getenv("AUDIT_TOPIC", "").strip() and scorecard.exists():
        trend_text = scorecard.read_text(encoding="utf-8")
        selected_line = next((line for line in trend_text.splitlines() if line.casefold().startswith(topic.casefold() + " |")), "")
        if selected_line:
            market_match = re.search(r"markets=([^|]+)", selected_line)
            rank_match = re.search(r"^([0-9]+)\\.", selected_line)
            market_count = len([x for x in (market_match.group(1).split(",") if market_match else []) if x.strip()])
            rank = int(rank_match.group(1)) if rank_match else 50
            trend_score = 5 if market_count >= 4 and rank <= 5 else 4 if market_count >= 3 and rank <= 10 else 3 if market_count >= 2 else 2 if market_count >= 1 else 0
            trend_evidence = f"Google Trends RSS scorecard: rank {rank}, {market_count} markets. This is a limited proxy, not total audience demand."
        else:
            trend_evidence = "Trends run occurred but selected-topic ranking evidence was not matched; audience signal not scored."
    weighted = round((trend_score * 25 + research_score * 20 + media_score * 30 + rights_score * 15 + feasibility_score * 10) / 5)
    if weighted >= 70 and commons_licensed >= 3 and research_score >= 3:
        decision = "GO_TO_STORYBOARD"
        reason = "Preliminary score and source inventory meet the threshold; individual files still require human rights review."
    elif assets and research.get("extract"):
        decision = "CONDITIONAL_RESEARCH"
        reason = "Research context and media leads exist, but audience demand and/or rights/coverage are not sufficiently verified to green-light story writing."
    else:
        decision = "HOLD_OR_RESELECT"
        reason = "Insufficient evidence of both research depth and relevant media supply. Try another angle or candidate before story writing."
    report = {
        "topic": topic, "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision, "decision_reason": reason, "score_out_of_100": weighted,
        "audience_signal_evidence": trend_evidence,
        "score_components_0_to_5": {"audience_signal": trend_score, "research_depth": research_score,
            "media_inventory": media_score, "rights_readiness": rights_score, "production_feasibility": feasibility_score},
        "research": research,
        "media_counts": {"commons_search_results": len(commons), "commons_with_licence_metadata": commons_licensed,
                         "nasa_search_results": len(nasa), "automatically_cleared_assets": 0},
        "errors": {"commons": commons_error, "nasa": nasa_error},
        "search_links": search_links(topic), "assets": assets,
        "important_limitations": [
            "Search results are leads, not proof that each asset is relevant, downloadable, or legally reusable.",
            "Audience score is not measured for manually entered topics. Media counts do not indicate popularity.",
            "Fair use/fair dealing is context-specific; this script does not determine whether a copyright exception applies.",
            "A human must check facts, exact asset pages, licences, commercial/adaptation terms, and coverage gaps before story writing."
        ]}
    (OUT / "topic-audit.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    fields = ["source", "title", "page_url", "file_url", "preview_url", "mime", "media_type", "creator",
              "license", "license_url", "date_created", "rights_status", "rights_note"]
    with (OUT / "media-inventory.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(assets)
    lines = [f"# Topic viability audit: {topic}", "", f"- **Decision:** {decision}",
        f"- **Preliminary score:** {weighted}/100", f"- **Audited (UTC):** {report['audited_at_utc']}",
        f"- **Reason:** {reason}", "", "## Decision scores (0–5)", "",
        "| Factor | Score | Meaning |", "|---|---:|---|",
        f"| Audience signal | {trend_score}/5 | {trend_evidence} |",
        f"| Research depth | {research_score}/5 | Public summary is a starting point, not full fact-checking |",
        f"| Media inventory | {media_score}/5 | Search-result count only; relevance and file access need review |",
        f"| Rights readiness | {rights_score}/5 | Metadata proxy, not legal clearance |",
        f"| Production feasibility | {feasibility_score}/5 | Early estimate from research and media leads |",
        "", "## Topic research", "", f"**Source:** [{research.get('title', topic)}]({research.get('url', '')})", "",
        research.get("extract", "No automated summary was returned."), "", "## Media inventory", "",
        f"- Wikimedia Commons results: {len(commons)}; with licence metadata: {commons_licensed}",
        f"- NASA image/video results: {len(nasa)}", "- No assets are automatically marked cleared. Review the CSV and each source page.", "",
        "## Search more free media", ""]
    lines += [f"- [{label}]({url})" for label, url in report["search_links"].items()]
    lines += ["", "## Rights and go/no-go gate", "",
        "- Do not download/re-upload other creators' YouTube videos as a shortcut.",
        "- Prefer public-domain assets and licences allowing the intended commercial use and adaptations; record creator, source, licence, attribution and date.",
        "- Check third-party rights, music, logos, identifiable people and asset-specific restrictions.",
        "- Fair use and fair dealing are not interchangeable blanket permissions.",
        "- If relevant media is thin or rights unclear, change the angle or reject the topic before scripting.",
        "- This report is a research aid, not legal advice or automatic rights clearance.", "",
        "## Errors", "", f"- Wikimedia Commons: {commons_error or 'none'}", f"- NASA API: {nasa_error or 'none'}", ""]
    (OUT / "topic-audit.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Topic: {topic}")
    print(f"Decision: {decision} ({weighted}/100)")
    print(f"Research summary: {research['status']}; Commons leads: {len(commons)}; NASA leads: {len(nasa)}")
    print("Saved topic-audit/topic-audit.md, topic-audit/topic-audit.json, and topic-audit/media-inventory.csv")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: topic viability audit failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
