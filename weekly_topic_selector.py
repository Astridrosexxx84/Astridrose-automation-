#!/usr/bin/env python3
"""Discover candidate topics from recent popular YouTube uploads, then score them.

No permanent category list: broad discovery searches produce candidate phrases from
recent high-view videos. Candidates are then compared using fresh-upload median
lifetime views/day against the prior upload cohort. This is a momentum proxy, not
true view acceleration; public YouTube statistics do not expose historical snapshots.
Prints only the winning query to stdout for GitHub Actions.
"""
import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone

API = "https://www.googleapis.com/youtube/v3"
LOOKBACK_DAYS = max(14, min(90, int(os.getenv("TOPIC_LOOKBACK_DAYS", "30"))))
RECENT_DAYS = 7
SAMPLE_SIZE = 25
CANDIDATE_LIMIT = 10
DISCOVERY_SEEDS = ("trending", "viral", "popular", "new", "best", "2026")
STOPWORDS = set("""
a an the and or but for to of in on at by from with without about into over after
before is are was were be been being it its this that these those as how what why
when where who which you your we our they their i my me he she his her them us
can could should would will just not no yes do does did has have had get got make
made official video videos music song songs full episode trailer clip clips shorts
short shortfilm new latest update updates reaction reactions review reviews watch
watching part live livestream stream streaming highlights compilation featuring ft
""".split())


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
        "https://oauth2.googleapis.com/token", data=form,
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


def api_search(token, query, published_after, published_before=None, order="date"):
    params = {
        "part": "snippet", "type": "video", "q": query, "order": order,
        "publishedAfter": published_after, "maxResults": SAMPLE_SIZE,
        "safeSearch": "moderate",
    }
    if published_before:
        params["publishedBefore"] = published_before
    return request_json(API + "/search?" + urllib.parse.urlencode(params), token).get("items", [])


def discover_candidates(token, recent_after):
    # Use broad discovery signals, not fixed subject categories. Candidate phrases
    # come from actual recent upload titles returned by YouTube.
    title_items = []
    seen_ids = set()
    for seed in DISCOVERY_SEEDS:
        for item in api_search(token, seed, recent_after, order="viewCount"):
            video_id = item.get("id", {}).get("videoId")
            title = item.get("snippet", {}).get("title", "")
            if video_id and title and video_id not in seen_ids:
                seen_ids.add(video_id)
                title_items.append(title)

    counts = Counter()
    for title in title_items:
        words = [
            word.lower() for word in re.findall(r"[A-Za-z0-9]+", title)
            if len(word) > 2 and word.lower() not in STOPWORDS and not word.isdigit()
        ]
        # Use short, searchable phrases from titles rather than whole video titles.
        for size in (2, 3, 4):
            for start in range(max(0, len(words) - size + 1)):
                phrase = " ".join(words[start:start + size])
                if len(phrase) >= 7:
                    counts[phrase] += 1

    # Prefer phrases appearing across several popular-upload titles; use a stable
    # lexical tie-break and avoid selecting multiple near-identical phrases.
    ranked = sorted(counts.items(), key=lambda pair: (pair[1], len(pair[0].split()), pair[0]), reverse=True)
    candidates = []
    for phrase, _frequency in ranked:
        words = set(phrase.split())
        if any(len(words & set(existing.split())) / max(1, len(words | set(existing.split()))) > 0.75
               for existing in candidates):
            continue
        candidates.append(phrase)
        if len(candidates) >= CANDIDATE_LIMIT:
            break

    if len(candidates) < CANDIDATE_LIMIT:
        # Fallback still comes from live discovery results, not a hard-coded topic list.
        for title in title_items:
            words = [
                word.lower() for word in re.findall(r"[A-Za-z0-9]+", title)
                if len(word) > 2 and word.lower() not in STOPWORDS and not word.isdigit()
            ]
            phrase = " ".join(words[:4])
            if len(phrase) >= 7 and phrase not in candidates:
                candidates.append(phrase)
            if len(candidates) >= CANDIDATE_LIMIT:
                break
    if not candidates:
        raise RuntimeError("Broad discovery returned no usable recent video-title topics.")
    print(f"Discovered {len(title_items)} recent videos; evaluating {len(candidates)} dynamic candidate topics.", file=sys.stderr)
    for candidate in candidates:
        print("Candidate: " + candidate, file=sys.stderr)
    return candidates


def search_video_ids(token, query, published_after, published_before=None):
    items = api_search(token, query, published_after, published_before, order="date")
    return [item.get("id", {}).get("videoId") for item in items
            if item.get("id", {}).get("videoId")]


def get_views_per_day(video, now):
    try:
        published = datetime.fromisoformat(
            video["snippet"]["publishedAt"].replace("Z", "+00:00")
        )
        age_days = max(1.0, (now - published).total_seconds() / 86400)
        return int(video.get("statistics", {}).get("viewCount", 0)) / age_days
    except (KeyError, ValueError, TypeError):
        return None


def score_topic(token, query, recent_after, prior_after, recent_before):
    recent_ids = search_video_ids(token, query, recent_after)
    prior_ids = search_video_ids(token, query, prior_after, recent_before)
    all_ids = list(dict.fromkeys(recent_ids + prior_ids))
    if not all_ids:
        return {"topic": query, "score": 0, "recent_median": 0, "prior_median": 0,
                "momentum_ratio": 1.0, "recent_videos": 0, "prior_videos": 0, "top_recent": 0}
    details = request_json(API + "/videos?" + urllib.parse.urlencode({
        "part": "snippet,statistics", "id": ",".join(all_ids[:50]),
        "maxResults": min(50, len(all_ids)),
    }), token).get("items", [])
    now = datetime.now(timezone.utc)
    recent_set, prior_set = set(recent_ids), set(prior_ids)
    recent_rates, prior_rates = [], []
    for video in details:
        rate = get_views_per_day(video, now)
        if rate is None:
            continue
        if video.get("id") in recent_set:
            recent_rates.append(rate)
        elif video.get("id") in prior_set:
            prior_rates.append(rate)
    recent_median = statistics.median(recent_rates) if recent_rates else 0
    prior_median = statistics.median(prior_rates) if prior_rates else 0
    ratio = recent_median / prior_median if prior_median > 0 else 1.0
    factor = 0.5 + 0.5 * min(3.0, max(0.0, ratio))
    return {
        "topic": query, "score": int(recent_median * factor),
        "recent_median": int(recent_median), "prior_median": int(prior_median),
        "momentum_ratio": ratio, "recent_videos": len(recent_rates),
        "prior_videos": len(prior_rates),
        "top_recent": int(max(recent_rates)) if recent_rates else 0,
    }


def main():
    token = get_token()
    now = datetime.now(timezone.utc)
    recent_start = now - timedelta(days=RECENT_DAYS)
    lookback_start = now - timedelta(days=LOOKBACK_DAYS)
    fmt = lambda value: value.strftime("%Y-%m-%dT%H:%M:%SZ")
    candidates = discover_candidates(token, fmt(recent_start))
    results = []
    for topic in candidates:
        result = score_topic(token, topic, fmt(recent_start), fmt(lookback_start), fmt(recent_start))
        results.append(result)
        ratio_text = f'{result["momentum_ratio"]:.2f}x' if result["prior_videos"] else "n/a"
        print(f'{topic}: recent median approx {result["recent_median"]:,} views/day; '
              f'prior median {result["prior_median"]:,}/day; cohort ratio {ratio_text}; '
              f'{result["recent_videos"]} recent and {result["prior_videos"]} prior videos',
              file=sys.stderr)
    results.sort(key=lambda item: (
        item["score"], item["recent_median"], item["recent_videos"], item["topic"]
    ), reverse=True)
    winner = next((item for item in results if item["recent_videos"] > 0), None)
    if winner is None:
        raise RuntimeError("No usable video statistics found for candidate topics in the last 7 days.")

    with open("topic-discovery-scorecard.txt", "w", encoding="utf-8") as report:
        report.write(
            "YouTube dynamic topic comparison (fresh-upload momentum proxy)\n"
            f"Lookback window: {LOOKBACK_DAYS} days; recent cohort: last {RECENT_DAYS} days\n"
            f"Discovery: broad searches {', '.join(DISCOVERY_SEEDS)}; candidate phrases extracted "
            "from recent high-view upload titles. No fixed subject categories.\n"
            f"Candidates evaluated: {len(results)} (target {CANDIDATE_LIMIT})\n"
            "Metric: recent-cohort median lifetime views/day adjusted by a capped ratio against "
            "the prior cohort median. This is a proxy for fresh-upload performance, not true "
            "view acceleration or an official YouTube trending ranking. Public statistics do "
            "not expose historical view-count snapshots.\n"
            f"Estimated scorecard API usage: {len(DISCOVERY_SEEDS) + len(results) * 2} "
            "search.list calls + up to one videos.list per candidate; playlist stage adds "
            "two search.list calls, one videos.list call, one playlist insert and up to five "
            "playlist-item inserts. YouTube API quota remains subject to Google's limits.\n\n"
        )
        for index, result in enumerate(results, 1):
            ratio_text = f'{result["momentum_ratio"]:.2f}x' if result["prior_videos"] else "n/a"
            report.write(
                f'{index}. {result["topic"]} | score: {result["score"]:,} '
                f'| recent median: {result["recent_median"]:,} views/day '
                f'| prior median: {result["prior_median"]:,} views/day '
                f'| cohort ratio: {ratio_text} | videos: {result["recent_videos"]} recent, '
                f'{result["prior_videos"]} prior | top recent: {result["top_recent"]:,}/day\n'
            )
        report.write(f"\nSelected topic: {winner['topic']}\n")
    print(winner["topic"])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
