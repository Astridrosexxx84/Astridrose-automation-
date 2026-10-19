#!/usr/bin/env python3
"""Choose a weekly topic by comparing recent YouTube view velocity across seed topics.

Each search.list request costs 100 YouTube API quota units. This script searches
once per candidate topic, then uses videos.list (1 unit per request) for stats.
It prints only the winning query to stdout so GitHub Actions can capture it.
"""
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://www.googleapis.com/youtube/v3"
TOPICS = [
    "popular music new songs",
    "gaming highlights",
    "viral food videos",
    "football and sports highlights",
    "new technology and AI",
    "movie trailers and entertainment",
    "travel destinations",
    "funny comedy clips",
    "cute animals",
    "fitness and workout videos",
]
LOOKBACK_DAYS = max(7, min(90, int(os.getenv("TOPIC_LOOKBACK_DAYS", "30"))))
SAMPLE_SIZE = 5


def get_token():
    keys = ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")
    missing = [key for key in keys if not os.getenv(key)]
    if missing:
        raise RuntimeError("Missing GitHub Actions secret(s): " + ", ".join(missing))
    form = urllib.parse.urlencode({
        "client_id": os.environ["YOUTUBE_CLIENT_ID"],
        "client_secret": os.environ["YOUTUBE_CLIENT_SECRET"],
        "refresh_token": os.environ["YOUTUBE_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError("Google OAuth refresh failed: " + detail[:500]) from None
    if not payload.get("access_token"):
        raise RuntimeError("Google OAuth did not return an access token.")
    return payload["access_token"]


def request_json(url, token):
    req = urllib.request.Request(
        url, headers={"Authorization": "Bearer " + token, "Accept": "application/json"}
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code not in (408, 429, 500, 502, 503, 504) or attempt == 3:
                raise RuntimeError(f"YouTube API error {exc.code}: {detail[:500]}") from None
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            if attempt == 3:
                raise RuntimeError(f"Network error after retries: {exc}") from None
        time.sleep(2 ** (attempt + 1))
    raise RuntimeError("YouTube API request failed after retries.")


def score_topic(token, query, published_after):
    params = {
        "part": "snippet",
        "type": "video",
        "q": query,
        "order": "viewCount",
        "publishedAfter": published_after,
        "maxResults": SAMPLE_SIZE,
        "safeSearch": "moderate",
    }
    items = request_json(API + "/search?" + urllib.parse.urlencode(params), token).get("items", [])
    ids = [item.get("id", {}).get("videoId") for item in items]
    ids = [video_id for video_id in ids if video_id]
    if not ids:
        return {"topic": query, "score": 0, "videos": 0, "median_views_per_day": 0, "top_views_per_day": 0}

    details = request_json(API + "/videos?" + urllib.parse.urlencode({
        "part": "snippet,statistics",
        "id": ",".join(ids),
        "maxResults": len(ids),
    }), token).get("items", [])
    now = datetime.now(timezone.utc)
    velocities = []
    for video in details:
        snippet = video.get("snippet", {})
        stats = video.get("statistics", {})
        try:
            published = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
            age_days = max(1.0, (now - published).total_seconds() / 86400)
            views = int(stats.get("viewCount", 0))
        except (KeyError, ValueError, TypeError):
            continue
        velocities.append(views / age_days)

    velocities.sort(reverse=True)
    # Median reduces the chance one exceptional viral upload dominates a whole topic.
    median_velocity = int(statistics.median(velocities)) if velocities else 0
    top_velocity = int(velocities[0]) if velocities else 0
    return {
        "topic": query,
        "score": median_velocity,
        "videos": len(velocities),
        "median_views_per_day": median_velocity,
        "top_views_per_day": top_velocity,
    }


def main():
    token = get_token()
    after = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    results = []
    for topic in TOPICS:
        result = score_topic(token, topic, after)
        results.append(result)
        print(
            f'{topic}: median approx {result["median_views_per_day"]:,} views/day '
            f'across {result["videos"]} recent videos; top approx '
            f'{result["top_views_per_day"]:,}/day',
            file=sys.stderr,
        )

    # Stable tie-breaker: median velocity, then sample count, then topic name.
    results.sort(key=lambda item: (item["score"], item["videos"], item["topic"]), reverse=True)
    winner = results[0]
    if winner["videos"] == 0:
        raise RuntimeError("No usable recent video statistics were found for any candidate topic.")

    with open("topic-discovery-scorecard.txt", "w", encoding="utf-8") as report:
        report.write(
            "YouTube topic comparison (recent uploads only)\n"
            f"Lookback window: {LOOKBACK_DAYS} days\n"
            "Metric: median estimated lifetime views per day among up to five recent, "
            "high-view-count search results per topic. This is a proxy, not an official "
            "YouTube trending ranking.\n\n"
        )
        for index, result in enumerate(results, 1):
            report.write(
                f'{index}. {result["topic"]} | median estimated views/day: '
                f'{result["median_views_per_day"]:,} | top estimated views/day: '
                f'{result["top_views_per_day"]:,} | videos scored: {result["videos"]}\n'
            )
        report.write(f'\nSelected topic: {winner["topic"]}\n')

    print(winner["topic"])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
