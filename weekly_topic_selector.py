#!/usr/bin/env python3
"""Rank topics using recent-upload performance and a prior-period comparison.

For each topic, sample up to 25 uploads from the last 7 days and up to 25
uploads from the preceding period. Compare median lifetime views/day between
the cohorts. This is a fresh-upload momentum proxy, not true view acceleration:
the public YouTube API does not provide historical view-count snapshots for
other creators' videos. Prints only the winning query to stdout for Actions.
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
LOOKBACK_DAYS = max(14, min(90, int(os.getenv("TOPIC_LOOKBACK_DAYS", "30"))))
RECENT_DAYS = 7
SAMPLE_SIZE = 25


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


def search_video_ids(token, query, published_after, published_before=None):
    params = {
        "part": "snippet",
        "type": "video",
        "q": query,
        "order": "date",
        "publishedAfter": published_after,
        "maxResults": SAMPLE_SIZE,
        "safeSearch": "moderate",
    }
    if published_before:
        params["publishedBefore"] = published_before
    items = request_json(API + "/search?" + urllib.parse.urlencode(params), token).get("items", [])
    return [item.get("id", {}).get("videoId") for item in items if item.get("id", {}).get("videoId")]


def get_views_per_day(video, now):
    snippet = video.get("snippet", {})
    stats = video.get("statistics", {})
    try:
        published = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
        age_days = max(1.0, (now - published).total_seconds() / 86400)
        return int(stats.get("viewCount", 0)) / age_days
    except (KeyError, ValueError, TypeError):
        return None


def score_topic(token, query, recent_after, prior_after, recent_before):
    # Two upload cohorts let us compare fresh uploads with the previous period.
    recent_ids = search_video_ids(token, query, recent_after)
    prior_ids = search_video_ids(token, query, prior_after, recent_before)
    all_ids = list(dict.fromkeys(recent_ids + prior_ids))
    if not all_ids:
        return {
            "topic": query, "score": 0, "recent_median": 0, "prior_median": 0,
            "momentum_ratio": 1.0, "recent_videos": 0, "prior_videos": 0,
            "top_recent": 0,
        }

    # At most 50 IDs per topic, so both cohorts fit in one videos.list request.
    details = request_json(API + "/videos?" + urllib.parse.urlencode({
        "part": "snippet,statistics",
        "id": ",".join(all_ids[:50]),
        "maxResults": min(50, len(all_ids)),
    }), token).get("items", [])
    now = datetime.now(timezone.utc)
    recent_set, prior_set = set(recent_ids), set(prior_ids)
    recent_rates, prior_rates = [], []
    for video in details:
        video_id = video.get("id")
        rate = get_views_per_day(video, now)
        if rate is None:
            continue
        if video_id in recent_set:
            recent_rates.append(rate)
        elif video_id in prior_set:
            prior_rates.append(rate)

    recent_median = statistics.median(recent_rates) if recent_rates else 0
    prior_median = statistics.median(prior_rates) if prior_rates else 0
    # Missing/zero prior data is neutral, not an artificial momentum boost.
    ratio = recent_median / prior_median if prior_median > 0 else 1.0
    # Cap the boost so a tiny baseline cannot dominate; recent performance still matters.
    factor = 0.5 + 0.5 * min(3.0, max(0.0, ratio))
    score = int(recent_median * factor)
    return {
        "topic": query,
        "score": score,
        "recent_median": int(recent_median),
        "prior_median": int(prior_median),
        "momentum_ratio": ratio,
        "recent_videos": len(recent_rates),
        "prior_videos": len(prior_rates),
        "top_recent": int(max(recent_rates)) if recent_rates else 0,
    }


def main():
    token = get_token()
    now = datetime.now(timezone.utc)
    recent_start = now - timedelta(days=RECENT_DAYS)
    lookback_start = now - timedelta(days=LOOKBACK_DAYS)
    fmt = lambda value: value.strftime("%Y-%m-%dT%H:%M:%SZ")
    results = []
    for topic in TOPICS:
        result = score_topic(
            token, topic, fmt(recent_start), fmt(lookback_start), fmt(recent_start)
        )
        results.append(result)
        ratio_text = f'{result["momentum_ratio"]:.2f}x' if result["prior_videos"] else "n/a"
        print(
            f'{topic}: recent median approx {result["recent_median"]:,} views/day; '
            f'prior median {result["prior_median"]:,}/day; cohort ratio {ratio_text}; '
            f'{result["recent_videos"]} recent and {result["prior_videos"]} prior videos',
            file=sys.stderr,
        )

    results.sort(
        key=lambda item: (item["score"], item["recent_median"], item["recent_videos"], item["topic"]),
        reverse=True,
    )
    winner = results[0]
    if winner["recent_videos"] == 0:
        raise RuntimeError("No usable video statistics found for uploads in the last 7 days.")

    with open("topic-discovery-scorecard.txt", "w", encoding="utf-8") as report:
        report.write(
            "YouTube topic comparison (fresh-upload momentum proxy)\n"
            f"Lookback window: {LOOKBACK_DAYS} days; recent cohort: last {RECENT_DAYS} days\n"
            f"Sample: up to {SAMPLE_SIZE} newest uploads per topic in each cohort\n"
            "Metric: recent-cohort median lifetime views/day adjusted by a capped ratio "
            "against the prior cohort's median lifetime views/day. This is a proxy for "
            "which topics have stronger-performing fresh uploads, not true view acceleration "
            "or an official YouTube trending ranking. Public video statistics do not expose "
            "historical view-count snapshots. Missing/zero prior medians are treated neutrally.\n"
            f"Estimated API requests: {len(TOPICS) * 2} search.list + {len(TOPICS)} videos.list "
            "for the scorecard; playlist stage adds two search.list calls, one videos.list "
            "call, one playlist insert and up to five playlist-item inserts.\n\n"
        )
        for index, result in enumerate(results, 1):
            ratio_text = f'{result["momentum_ratio"]:.2f}x' if result["prior_videos"] else "n/a"
            report.write(
                f'{index}. {result["topic"]} | momentum-adjusted score: {result["score"]:,} '
                f'| last-7-day cohort median: {result["recent_median"]:,} views/day '
                f'| prior cohort median: {result["prior_median"]:,} views/day '
                f'| cohort ratio: {ratio_text} | videos: {result["recent_videos"]} recent, '
                f'{result["prior_videos"]} prior | top recent: {result["top_recent"]:,}/day\n'
            )
        report.write(f'\nSelected topic: {winner["topic"]}\n')

    print(winner["topic"])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
