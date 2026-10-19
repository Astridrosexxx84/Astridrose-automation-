#!/usr/bin/env python3
"""Discover and rank YouTube videos, then add the top results to an unlisted playlist."""
import json, os, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

API = "https://www.googleapis.com/youtube/v3"
RETRYABLE = {408, 409, 429, 500, 502, 503, 504}

def request_json(url, token, method="GET", body=None):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Authorization": "Bearer " + token, "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    for attempt in range(5):
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code not in RETRYABLE or attempt == 4:
                raise RuntimeError(f"YouTube API error {exc.code}: {detail[:800]}") from None
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            if attempt == 4:
                raise RuntimeError(f"Network error after retries: {exc}") from None
        delay = 2 ** (attempt + 1)
        print(f"Temporary request failure; retrying in {delay}s (attempt {attempt + 2}/5)")
        time.sleep(delay)
    raise RuntimeError("Request failed after retries")

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
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raise RuntimeError("Google OAuth refresh failed: " + exc.read().decode()[:800]) from None
    if not payload.get("access_token"):
        raise RuntimeError("Google OAuth did not return an access token.")
    return payload["access_token"]

def discover(token, query, candidate_count, lookback_days):
    """Combine recent uploads and popular uploads, then rank by estimated views/day."""
    after = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    base = {"part":"snippet", "type":"video", "q":query, "maxResults":min(50, candidate_count),
            "safeSearch":"moderate", "publishedAfter":after}
    found_by_id = {}
    for order in ("date", "viewCount"):
        params = dict(base, order=order)
        items = request_json(API + "/search?" + urllib.parse.urlencode(params), token).get("items", [])
        for item in items:
            video_id = item.get("id", {}).get("videoId")
            if video_id:
                found_by_id[video_id] = item
        print(f"YouTube search ({order}) returned {len(items)} results.")
    if not found_by_id:
        print("No recent matches; trying an all-time popular search fallback.")
        params = dict(base, order="viewCount")
        params.pop("publishedAfter", None)
        items = request_json(API + "/search?" + urllib.parse.urlencode(params), token).get("items", [])
        for item in items:
            video_id = item.get("id", {}).get("videoId")
            if video_id:
                found_by_id[video_id] = item
    ids = list(found_by_id)
    if not ids:
        raise RuntimeError("No videos found for this topic; no playlist created.")
    details = request_json(API + "/videos?" + urllib.parse.urlencode({
        "part":"snippet,statistics", "id":",".join(ids[:50]), "maxResults":min(50, len(ids))}), token).get("items", [])
    now = datetime.now(timezone.utc)
    ranked = []
    for video in details:
        snippet, stats = video.get("snippet", {}), video.get("statistics", {})
        try:
            published = datetime.fromisoformat(snippet.get("publishedAt", "").replace("Z", "+00:00"))
            age_days = max(1, (now - published).total_seconds() / 86400)
        except (ValueError, TypeError):
            age_days = 1
        views = int(stats.get("viewCount", 0))
        ranked.append({"id":video["id"], "title":snippet.get("title",""),
                       "channel":snippet.get("channelTitle",""), "views":views,
                       "views_per_day":int(views / age_days),
                       "published_at":snippet.get("publishedAt",""),
                       "url":"https://www.youtube.com/watch?v=" + video["id"]})
    return sorted(ranked, key=lambda v:(v["views_per_day"], v["views"]), reverse=True)

def main():
    query = os.getenv("SEARCH_QUERY", "popular music 2026").strip()
    title = os.getenv("PLAYLIST_TITLE", "Automation Test - Unlisted Playlist").strip()
    playlist_count = max(1, min(5, int(os.getenv("MAX_RESULTS", "5"))))
    candidate_count = max(5, min(50, int(os.getenv("SEARCH_CANDIDATES", "25"))))
    lookback = max(1, min(365, int(os.getenv("LOOKBACK_DAYS", "30"))))
    token = get_token()
    ranked = discover(token, query, candidate_count, lookback)
    print(f"Ranked {len(ranked)} candidates; selecting up to {playlist_count} for the unlisted playlist.")
    ranked = ranked[:playlist_count]
    playlist = request_json(API + "/playlists?part=snippet,status", token, "POST", {
        "snippet":{"title":title, "description":"Unlisted research playlist created by automated YouTube discovery. Topic: " + query},
        "status":{"privacyStatus":"unlisted"}})
    added = []
    for video in ranked:
        try:
            request_json(API + "/playlistItems?part=snippet", token, "POST", {
                "snippet":{"playlistId":playlist["id"],
                           "resourceId":{"kind":"youtube#video","videoId":video["id"]}}})
            added.append(video)
            print(f'Added: {video["title"]} | {video["views"]:,} views | approx {video["views_per_day"]:,} views/day')
        except RuntimeError as exc:
            print(f'Skipped {video["id"]} after retries: {exc}')
    url = "https://www.youtube.com/playlist?list=" + playlist["id"]
    with open("discovery-playlist-result.txt", "w", encoding="utf-8") as f:
        f.write(f"Title: {title}\nPrivacy: unlisted\nTopic: {query}\nPlaylist: {url}\nVideos added: {len(added)} of {len(ranked)}\n\n")
        for video in added:
            f.write(f'{video["title"]}\n{video["url"]}\nViews: {video["views"]} | estimated lifetime views/day: {video["views_per_day"]}\n\n')
    print("Unlisted playlist created:", url)
    print(f"Videos added: {len(added)} of {len(ranked)}")
if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR:", exc)
        with open("discovery-playlist-result.txt", "w", encoding="utf-8") as f:
            f.write("FAILED\n" + str(exc) + "\n")
        raise
