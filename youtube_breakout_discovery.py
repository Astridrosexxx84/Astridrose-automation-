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
from datetime import datetime, timezone
from pathlib import Path

SCORECARD = Path("topic-discovery-scorecard.txt")
OUT = Path("topic-audit")
MAX_TOPICS = 12
MAX_RESULTS_PER_TOPIC = 15
def parse_int(value):
    try:
        return int(value or 0)
    except (ValueError, TypeError):
        return 0

def parse_views(value):
    if not value:
        return 0
    match = re.search(r'([0-9,.]+)\\s*([KMB]?)', value.upper())
    if not match:
        return 0
    number = float(match.group(1).replace(',', ''))
    scale = {'': 1, 'K': 1000, 'M': 1000000, 'B': 1000000000}.get(match.group(2), 1)
    return int(number * scale)

def age_in_days(value):
    match = re.search(r'(\\d+)\\s*(second|minute|hour|day|week|month|year)', (value or '').casefold())
    if not match:
        return None
    n, unit = int(match.group(1)), match.group(2)
    factor = {'second': 1/86400, 'minute': 1/1440, 'hour': 1/24, 'day': 1, 'week': 7, 'month': 30, 'year': 365}
    return max(1/24, n * factor[unit])

def walk_video_renderers(node):
    if isinstance(node, dict):
        renderer = node.get('videoRenderer')
        if isinstance(renderer, dict) and renderer.get('videoId'):
            yield renderer
        for value in node.values():
            yield from walk_video_renderers(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk_video_renderers(value)

def search_topic(topic):
    # The old search feed endpoint returns HTTP 400; use YouTube's public search page.
    url = 'https://www.youtube.com/results?' + urllib.parse.urlencode({'search_query': topic, 'sp': 'CAISAhAB'})
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    with urllib.request.urlopen(req, timeout=22) as response:
        page = response.read().decode('utf-8', errors='replace')
    match = re.search(r'ytInitialData\\s*=\\s*', page)
    if not match:
        raise RuntimeError('YouTube search page did not expose ytInitialData')
    data, _ = json.JSONDecoder().raw_decode(page[match.end():])
    results, seen = [], set()
    for renderer in walk_video_renderers(data):
        video_id = renderer.get('videoId', '')
        if not video_id or video_id in seen:
            continue
        seen.add(video_id)
        title = ''.join(x.get('text', '') for x in renderer.get('title', {}).get('runs', []))
        channel = ''.join(x.get('text', '') for x in renderer.get('ownerText', {}).get('runs', []))
        published = renderer.get('publishedTimeText', {}).get('simpleText', '')
        view_text = renderer.get('viewCountText', {}).get('simpleText', '') or renderer.get('shortViewCountText', {}).get('simpleText', '')
        views = parse_views(view_text)
        age_days = age_in_days(published)
        views_per_day = round(views / age_days, 2) if views and age_days else 0
        score = round(math.log10(views + 1) * 10 + math.log10(views_per_day + 1) * 12, 2)
        results.append({'query_topic': topic, 'title': title, 'video_id': video_id, 'url': 'https://www.youtube.com/watch?v=' + video_id, 'channel': channel, 'published_utc': published, 'views_snapshot': views, 'likes_snapshot': 0, 'views_per_day_proxy': views_per_day, 'like_rate_proxy': 0, 'breakout_score_proxy': score, 'thumbnail_url': '', 'measurement_note': 'Public search-page snapshot; views and age are approximate; not measured growth velocity.'})
        if len(results) >= MAX_RESULTS_PER_TOPIC:
            break
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
        "method": "Public YouTube search page; no API key or paid credits",
        "topics_checked": topics,
        "video_results_count": len(all_rows),
        "results": all_rows[:100],
        "feed_errors": failures,
        "limitations": [
            "YouTube may block automated public-page searches or change its page structure.",
            "Only returned search results are evaluated; this is not an exhaustive YouTube crawl.",
            "Displayed view counts and rounded upload ages are one-time snapshots. Views/day is only a rough age-adjusted proxy, not measured view velocity; likes are not reliably exposed.",
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
