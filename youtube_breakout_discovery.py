#!/usr/bin/env python3
"""Free YouTube breakout-video scouting via public search feeds, if available.

No YouTube API key, paid service, download, or upload is used. Feed support can
change; a failed search is recorded as unavailable rather than treated as no demand.
"""
import csv
import json
import math
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

SCORECARD = Path("topic-discovery-scorecard.txt")
OUT = Path("topic-audit")
MAX_TOPICS = 12
MAX_RESULTS_PER_TOPIC = 15
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}

def get_text(node, path):
    found = node.find(path, NS)
    return (found.text or "").strip() if found is not None else ""

def parse_int(value):
    try:
        return int(value or 0)
    except (ValueError, TypeError):
        return 0

def parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None

def topics_from_scorecard():
    if not SCORECARD.exists():
        return []
    topics = []
    for line in SCORECARD.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*\d+\.\s*(.*?)\s*\|\s*markets=", line)
        if match:
            topic = match.group(1).strip()
            if topic and topic.casefold() not in {x.casefold() for x in topics}:
                topics.append(topic)
        if len(topics) >= MAX_TOPICS:
            break
    return topics

def search_topic(topic):
    url = "https://www.youtube.com/feeds/videos.xml?search_query=" + urllib.parse.quote_plus(topic)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; TopicScout/1.0)"})
    with urllib.request.urlopen(req, timeout=18) as response:
        root = ET.fromstring(response.read())
    entries = root.findall("atom:entry", NS)
    results = []
    now = datetime.now(timezone.utc)
    for entry in entries[:MAX_RESULTS_PER_TOPIC]:
        video_id = get_text(entry, "yt:videoId")
        title = get_text(entry, "atom:title")
        published = parse_date(get_text(entry, "atom:published"))
        link_node = entry.find("atom:link[@rel='alternate']", NS)
        link = link_node.attrib.get("href", "") if link_node is not None else (
            "https://www.youtube.com/watch?v=" + video_id if video_id else ""
        )
        channel = get_text(entry, "atom:author/atom:name")
        group = entry.find("media:group", NS)
        views = likes = 0
        thumbnail = ""
        if group is not None:
            community = group.find("media:community", NS)
            if community is not None:
                stats = community.find("media:statistics", NS)
                stars = community.find("media:starRating", NS)
                if stats is not None:
                    views = parse_int(stats.attrib.get("views"))
                if stars is not None:
                    likes = parse_int(stars.attrib.get("count"))
            thumb = group.find("media:thumbnail", NS)
            if thumb is not None:
                thumbnail = thumb.attrib.get("url", "")
        age_hours = max(1.0, (now - published).total_seconds() / 3600) if published else None
        views_per_day = round(views / max(age_hours / 24, 1 / 24), 2) if views else 0
        like_rate = round(likes / views, 5) if views else 0
        # Transparent heuristic: current view total + age-adjusted pace + like rate.
        # It is not true historical velocity because only one snapshot is available.
        score = round(math.log10(views + 1) * 10 + math.log10(views_per_day + 1) * 12
                      + min(10, like_rate * 1000), 2)
        results.append({
            "query_topic": topic, "title": title, "video_id": video_id, "url": link,
            "channel": channel, "published_utc": published.isoformat() if published else "",
            "views_snapshot": views, "likes_snapshot": likes, "views_per_day_proxy": views_per_day,
            "like_rate_proxy": like_rate, "breakout_score_proxy": score, "thumbnail_url": thumbnail,
            "measurement_note": "Single RSS snapshot; views/day is not measured growth velocity."
        })
    return results

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    topics = topics_from_scorecard()
    all_rows, failures = [], []
    for topic in topics:
        try:
            rows = search_topic(topic)
            all_rows.extend(rows)
            print(f"{topic}: {len(rows)} video result(s)")
        except Exception as exc:
            failures.append({"topic": topic, "error": f"{type(exc).__name__}: {exc}"})
            print(f"{topic}: feed unavailable ({type(exc).__name__})")
        time.sleep(0.4)
    all_rows.sort(key=lambda x: (x["breakout_score_proxy"], x["views_snapshot"]), reverse=True)
    payload = {
        "status": "results_found" if all_rows else "no_results_or_search_feed_unavailable",
        "method": "Public YouTube search Atom feed; no API key or paid credits",
        "topics_checked": topics,
        "video_results_count": len(all_rows),
        "results": all_rows[:100],
        "feed_errors": failures,
        "limitations": [
            "Search-feed support may change or be blocked.",
            "Only returned search results are evaluated; this is not an exhaustive YouTube crawl.",
            "Views and likes are one-time snapshots. Views/day is only a rough age-adjusted proxy, not measured view velocity.",
            "This is an additional discovery signal, not a claim of guaranteed virality."
        ]
    }
    (OUT / "youtube-breakout-discovery.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    with (OUT / "youtube-breakout-discovery.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["query_topic", "title", "url", "channel", "published_utc", "views_snapshot",
                  "likes_snapshot", "views_per_day_proxy", "like_rate_proxy", "breakout_score_proxy"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in all_rows[:100]:
            writer.writerow({key: row.get(key, "") for key in fields})
    lines = [
        "# YouTube breakout-video discovery", "",
        f"- Topics checked: {len(topics)}",
        f"- Video results collected: {len(all_rows)}",
        f"- Search feed errors: {len(failures)}",
        "- Cost: public feed only; no API key or paid credits",
        "- Score: view total + rough age-adjusted views/day + like-rate proxy",
        "- Important: this is a one-time snapshot, not actual measured growth velocity.", "",
        "## Highest-scoring results", ""
    ]
    for i, row in enumerate(all_rows[:40], 1):
        lines.append(f"{i}. [{row['title'] or 'Untitled'}]({row['url']}) — {row['channel'] or 'unknown channel'}; views={row['views_snapshot']:,}; rough views/day={row['views_per_day_proxy']:,.0f}; score={row['breakout_score_proxy']}")
    if failures:
        lines += ["", "## Feed errors", ""] + [f"- {x['topic']}: {x['error']}" for x in failures]
    if not all_rows:
        lines += ["No video results were returned. Check the JSON for feed errors; do not interpret this as proof that the topics have no demand."]
    lines += ["", "## Limitations", ""] + [f"- {item}" for item in payload["limitations"]]
    (OUT / "youtube-breakout-discovery.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved {len(all_rows)} candidate video(s) to {OUT}/youtube-breakout-discovery.*")

if __name__ == "__main__":
    main()
