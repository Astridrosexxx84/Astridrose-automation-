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
    # Use MediaWiki's stable API rather than relying only on the REST summary endpoint,
    # which can return 404 for valid titles or unusual capitalization.
    api_url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "prop": "extracts|info",
        "exintro": "1", "explaintext": "1", "inprop": "url",
        "redirects": "1", "titles": topic
    })
    try:
        data = get_json(api_url)
        pages = data.get("query", {}).get("pages", {})
        page = next((p for p in pages.values() if "missing" not in p), None)
        if page and page.get("extract", "").strip():
            return {"status": "found", "title": page.get("title", topic),
                    "extract": page.get("extract", ""),
                    "url": page.get("fullurl", f"https://en.wikipedia.org/w/index.php?search={urllib.parse.quote(topic)}")}
        search_url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "format": "json", "list": "search", "srsearch": topic, "srlimit": "1"
        })
        results = get_json(search_url).get("query", {}).get("search", [])
        if results:
            found_title = results[0].get("title", topic)
            retry_url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
                "action": "query", "format": "json", "prop": "extracts|info",
                "exintro": "1", "explaintext": "1", "inprop": "url",
                "redirects": "1", "titles": found_title
            })
            retry = get_json(retry_url).get("query", {}).get("pages", {})
            found_page = next((p for p in retry.values() if "missing" not in p), None)
            if found_page and found_page.get("extract", "").strip():
                return {"status": "found", "title": found_page.get("title", found_title),
                        "extract": found_page.get("extract", ""),
                        "url": found_page.get("fullurl", f"https://en.wikipedia.org/w/index.php?search={urllib.parse.quote(found_title)}")}
        return {"status": "unavailable", "title": topic, "extract": "",
                "url": f"https://en.wikipedia.org/w/index.php?search={urllib.parse.quote(topic)}",
                "note": "No usable introductory extract was returned by the MediaWiki API."}
    except Exception as exc:
        return {"status": "unavailable", "title": topic, "extract": "",
                "url": f"https://en.wikipedia.org/w/index.php?search={urllib.parse.quote(topic)}",
                "note": f"MediaWiki API unavailable: {type(exc).__name__}: {exc}"}


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



def openverse_media(topic, limit=8):
    """Find openly licensed image leads; verify the original host and exact licence."""
    url = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode({"q": topic, "page_size": str(limit)})
    try:
        data = get_json(url)
        assets = []
        for item in data.get("results", []):
            lic, lic_url = item.get("license", ""), item.get("license_url", "")
            assets.append({"source": "Openverse", "title": item.get("title", ""),
                "page_url": item.get("foreign_landing_url") or item.get("url", ""),
                "file_url": item.get("url", ""), "preview_url": item.get("thumbnail", ""),
                "media_type": "image", "creator": item.get("creator", ""),
                "license": lic, "license_url": lic_url,
                "rights_status": "REVIEW_REQUIRED" if lic and lic_url else "LICENCE_UNVERIFIED",
                "rights_note": "Openverse is an index; verify original host, exact licence, attribution and third-party rights."})
        return assets, None
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"


def loc_media(topic, limit=8):
    """Search Library of Congress catalog; every item still needs rights review."""
    url = "https://www.loc.gov/search/?" + urllib.parse.urlencode({"q": topic, "fo": "json", "c": str(limit), "at": "results"})
    try:
        data = get_json(url)
        assets = []
        for item in data.get("results", []):
            rights = item.get("rights", "")
            images = item.get("image_url") or []
            formats = item.get("online_format") or []
            creator = item.get("contributor", "")
            if isinstance(creator, list):
                creator = ", ".join(str(x) for x in creator)
            assets.append({"source": "Library of Congress", "title": item.get("title", ""),
                "page_url": item.get("url", ""), "file_url": images[0] if images else "",
                "preview_url": images[0] if images else "", "media_type": ", ".join(str(x) for x in formats),
                "creator": creator, "date_created": item.get("date", ""), "license": rights,
                "license_url": item.get("rights_url", ""), "rights_status": "REVIEW_REQUIRED",
                "rights_note": "Check the individual item's rights note; only dedicated Free to Use and Reuse sets are preselected as rights-free."})
        return assets, None
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"


def internet_archive_media(topic, limit=8):
    """Search archive catalogue for movies/images; catalogue presence is not a reuse grant."""
    params = {"q": f"({topic}) AND (mediatype:movies OR mediatype:image)",
              "fl[]": ["identifier", "title", "mediatype", "creator", "date", "description", "licenseurl", "rights"],
              "rows": str(limit), "page": "1", "output": "json"}
    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(params, doseq=True)
    try:
        data = get_json(url)
        assets = []
        for item in data.get("response", {}).get("docs", []):
            identifier = item.get("identifier", "")
            lic_url, rights = item.get("licenseurl", ""), item.get("rights", "")
            assets.append({"source": "Internet Archive", "title": item.get("title", ""),
                "page_url": "https://archive.org/details/" + urllib.parse.quote(identifier, safe="") if identifier else "",
                "file_url": "", "media_type": item.get("mediatype", ""), "creator": item.get("creator", ""),
                "date_created": item.get("date", ""), "license": rights or ("See item metadata" if lic_url else ""),
                "license_url": lic_url, "description": str(item.get("description", ""))[:500],
                "rights_status": "REVIEW_REQUIRED",
                "rights_note": "Inspect item metadata and individual file rights. Downloadable file URL is not yet resolved."})
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
            "Openverse openly licensed images": f"https://openverse.org/search/image?q={q}",
            "Library of Congress": f"https://www.loc.gov/search/?q={q}",
            "Internet Archive movies and images": f"https://archive.org/search?query={q}%20AND%20(mediatype%3Amovies%20OR%20mediatype%3Aimage)",
            "YouTube reference research only": f"https://www.youtube.com/results?search_query={q}",
            "Google Trends explore": f"https://trends.google.com/trends/explore?q={q}"}


def main():
    topic = fetch_topic()
    research = wikipedia_research(topic)
    commons, commons_error = commons_media(topic)
    nasa, nasa_error = nasa_media(topic)
    openverse, openverse_error = openverse_media(topic)
    loc, loc_error = loc_media(topic)
    archive, archive_error = internet_archive_media(topic)
    assets = commons + nasa + openverse + loc + archive
    commons_licensed = sum(1 for x in commons if x.get("license") and x.get("license_url"))
    # Scores are deliberately conservative: search-result counts and licence labels
    # are only leads, not proof of relevance, usability, or commercial clearance.
    research_chars = len(research.get("extract", "").strip())
    research_score = 2 if research["status"] == "found" and research_chars >= 250 else (1 if research_chars else 0)
    raw_media_count = len(assets)
    media_score = 0 if raw_media_count == 0 else (1 if raw_media_count <= 2 else 2)
    rights_score = 0 if not assets else 1  # Human item-by-item rights review is not yet implemented.
    feasibility_score = 3 if assets and research_chars >= 250 else (2 if assets or research_chars else 0)
    trend_score = 0
    trend_evidence = "Not measured for manually entered topics."
    scorecard = Path("topic-discovery-scorecard.txt")
    if not os.getenv("AUDIT_TOPIC", "").strip() and scorecard.exists():
        trend_text = scorecard.read_text(encoding="utf-8")
        selected_line = ""
        for line in trend_text.splitlines():
            match_topic = re.match(r"^\d+\.\s*(.*?)\s*\|\s*markets=", line)
            if match_topic and match_topic.group(1).strip().casefold() == topic.casefold():
                selected_line = line
                break
        if selected_line:
            market_match = re.search(r"markets=([^|]+)", selected_line)
            rank_match = re.search(r"^(\d+)\.", selected_line)
            market_count = len([x for x in (market_match.group(1).split(",") if market_match else []) if x.strip()])
            rank = int(rank_match.group(1)) if rank_match else 50
            trend_score = 5 if market_count >= 4 and rank <= 5 else 4 if market_count >= 3 and rank <= 10 else 3 if market_count >= 2 else 2 if market_count >= 1 else 0
            trend_evidence = f"Google Trends RSS scorecard: rank {rank}, {market_count} markets. This is a limited proxy, not total audience demand."
        else:
            trend_evidence = "Trends run occurred but selected-topic ranking evidence was not matched; audience signal not scored."
    weighted = round((trend_score * 25 + research_score * 20 + media_score * 30 + rights_score * 15 + feasibility_score * 10) / 5)
    if assets and research_chars >= 250:
        decision = "CONDITIONAL_RESEARCH"
        reason = "Initial research and media leads exist, but relevance, video coverage, stock-media supply, and item-level rights still need verification. Not yet cleared for storyboarding."
    else:
        decision = "HOLD_OR_RESELECT"
        reason = "Insufficient evidence of both usable research and relevant media leads. Try another candidate or angle before story writing."
    # No automated GO decision is allowed until relevance, actual video coverage,
    # stock sources, and item-level rights have dedicated verification stages.
    report = {
        "topic": topic, "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision, "decision_reason": reason, "score_out_of_100": weighted,
        "audience_signal_evidence": trend_evidence,
        "score_components_0_to_5": {"audience_signal": trend_score, "research_depth": research_score,
            "media_inventory": media_score, "rights_readiness": rights_score, "production_feasibility": feasibility_score},
        "research": research,
        "media_counts": {"commons_search_results": len(commons), "commons_with_licence_metadata": commons_licensed,
                         "nasa_search_results": len(nasa), "openverse_image_results": len(openverse), "loc_results": len(loc), "internet_archive_results": len(archive), "automatically_cleared_assets": 0},
        "errors": {"commons": commons_error, "nasa": nasa_error, "openverse": openverse_error, "loc": loc_error, "internet_archive": archive_error},
        "search_links": search_links(topic), "assets": assets,
        "important_limitations": [
            "Search results are leads, not proof that each asset is relevant, downloadable, or legally reusable.",
            "Openverse currently adds image discovery only; it is not a video source in this pipeline.",
            "Library of Congress and Internet Archive records may have unclear rights or downloadability; review each item.",
            "This version does not yet inventory stock-video libraries or verify playable/downloadable video coverage.",
            "No topic is automatically approved for storyboarding; human review is mandatory.",
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
        f"- NASA image/video results: {len(nasa)}", f"- Openverse image results: {len(openverse)}", f"- Library of Congress results: {len(loc)}", f"- Internet Archive results: {len(archive)}", "- No assets are automatically marked cleared. Review the CSV and each source page.", "",
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
