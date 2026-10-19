#!/usr/bin/env python3
"""Find YouTube video candidates and rank them using public view statistics."""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API = "https://www.googleapis.com/youtube/v3"
TOKEN_URL = "https://oauth2.googleapis.com/token"


def api_get(token, endpoint, params):
    url = f"{API}/{endpoint}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"YouTube API {endpoint} failed ({exc.code}): {detail[:1000]}") from None


def get_access_token():
    keys = ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")
    missing = [key for key in keys if not os.environ.get(key)]
    if missing:
        raise RuntimeError("Missing GitHub Actions secret(s): " + ", ".join(missing))
    form = urllib.parse.urlencode({
        "client_id": os.environ["YOUTUBE_CLIENT_ID"],
        "client_secret": os.environ["YOUTUBE_CLIENT_SECRET"],
        "refresh_token": os.environ["YOUTUBE_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(
        TOKEN_URL, data=form, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Google OAuth refresh failed ({exc.code}): {detail[:1000]}") from None
    if not payload.get("access_token"):
        raise RuntimeError("Google OAuth did not return an access token.")
    return payload["access_token"]


def search(token, query, max_results, lookback_days):
    # Prefer videos published recently, sorted by total views, then rank by views/day.
    published_after = datetime.now(timezone.utc).timestamp() - lookback_days * 86400
    published_after = datetime.fromtimestamp(published_after, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    params = {
        "part": "snippet", "type": "video", "q": query,
        "maxResults": max_results, "order": "viewCount", "safeSearch": "moderate",
        "publishedAfter": published_after,
    }
    data = api_get(token, "search", params)
    scope = f"videos published in the last {lookback_days} days"
    if not data.get("items"):
        # Avoid a dead end if a niche has no recent matches.
        params.pop("publishedAfter", None)
        data = api_get(token, "search", params)
        scope = "all-time fallback (no recent matches found)"

    # De-duplicate IDs while preserving search order.
    found = {}
    for item in data.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        if video_id and video_id not in found:
            found[video_id] = item.get("snippet", {})
    if not found:
        return [], scope

    details = api_get(token, "videos", {
        "part": "statistics,contentDetails,snippet",
        "id": ",".join(found.keys()),
        "maxResults": len(found),
    }).get("items", [])
    now = datetime.now(timezone.utc)
    results = []
    for video in details:
        video_id = video.get("id")
        snippet = video.get("snippet", found.get(video_id, {}))
        stats = video.get("statistics", {})
        published = snippet.get("publishedAt", "")
        try:
            age_days = max(1, (now - datetime.fromisoformat(published.replace("Z", "+00:00"))).days)
        except (ValueError, TypeError):
            age_days = 1
        views = int(stats.get("viewCount", 0))
        results.append({
            "id": video_id,
            "title": " ".join(snippet.get("title", "").split()),
            "channel": " ".join(snippet.get("channelTitle", "").split()),
            "published": published[:10],
            "views": views,
            "views_per_day": views // age_days,
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "url": f"https://www.youtube.com/watch?v={video_id}",
        })
    # A rough discovery signal: recent view velocity, with total views as tie-breaker.
    return sorted(results, key=lambda v: (v["views_per_day"], v["views"]), reverse=True), scope


def main():
    raw_queries = os.environ.get("SEARCH_QUERIES", os.environ.get("SEARCH_QUERY", "")).strip()
    queries = list(dict.fromkeys(q.strip() for q in raw_queries.split(",") if q.strip()))
    if not queries:
        raise RuntimeError("Enter one or more comma-separated topic phrases in the workflow input.")
    try:
        max_results = max(1, min(25, int(os.environ.get("MAX_RESULTS", "10"))))
    except ValueError:
        max_results = 10
    try:
        lookback_days = max(1, min(365, int(os.environ.get("LOOKBACK_DAYS", "30"))))
    except ValueError:
        lookback_days = 30

    token = get_access_token()
    sections = []
    total_unique = set()
    for query in queries:
        results, scope = search(token, query, max_results, lookback_days)
        sections.extend([
            f"TOPIC: {query}",
            f"Unique videos returned: {len(results)}",
            f"Search scope: {scope}",
            "",
            "Ranked by estimated lifetime views/day, then total views. This is a rough comparison signal, not proof of current trend growth.",
            "",
        ])
        if not results:
            sections.append("No results returned. Try a broader or more specific topic.")
            sections.append("")
            continue
        for index, video in enumerate(results, start=1):
            total_unique.add(video["id"])
            line = (
                f'{index}. {video["title"]}\n'
                f'   Channel: {video["channel"]} | Published: {video["published"]}\n'
                f'   Views: {video["views"]:,} | Approx. lifetime views/day: {video["views_per_day"]:,} '
                f'| Likes: {video["likes"]:,} | Comments: {video["comments"]:,}\n'
                f'   {video["url"]}'
            )
            print(f"[{query}] {line}")
            sections.append(line)
        sections.append("")

    header = [
        "YouTube multi-topic discovery report",
        f"Topics searched: {len(queries)}",
        f"Unique videos across all topics (duplicates may appear in separate topic sections): {len(total_unique)}",
        f"Preferred publication window: last {lookback_days} days; each topic falls back to all-time results if no recent matches exist.",
        "Discovery only: this workflow does not create playlists or change YouTube.",
        "",
    ]
    with open("youtube-search-results.txt", "w", encoding="utf-8") as output:
        output.write("\n".join(header + sections) + "\n")
    print("\nSaved multi-topic candidates to youtube-search-results.txt (workflow artifact).")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
