#!/usr/bin/env python3
"""Add selected public YouTube videos to the user's own playlist.

Uses only the standard library and the official YouTube Data API.
It never downloads videos, uploads videos, publishes posts, or comments.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import time

API = "https://www.googleapis.com/youtube/v3"
TOKEN_URL = "https://oauth2.googleapis.com/token"
PLAYLIST_TITLE = os.environ.get("PLAYLIST_TITLE", "Dragon Ball Z Nostalgia").strip() or "Dragon Ball Z Nostalgia"
PLAYLIST_DESCRIPTION = os.environ.get(
    "PLAYLIST_DESCRIPTION",
    "A fan-curated collection of publicly available YouTube videos. This playlist links to original YouTube uploads and does not claim ownership of the videos.",
).strip()


def request_json(url, *, method="GET", headers=None, body=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
            return json.loads(raw.decode("utf-8")) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        # API errors are useful, but never print OAuth credentials.
        raise RuntimeError(f"API request failed ({exc.code}): {detail[:1200]}") from None


def access_token():
    required = ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise RuntimeError("Missing GitHub Actions secret(s): " + ", ".join(missing))
    form = urllib.parse.urlencode({
        "client_id": os.environ["YOUTUBE_CLIENT_ID"],
        "client_secret": os.environ["YOUTUBE_CLIENT_SECRET"],
        "refresh_token": os.environ["YOUTUBE_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode("utf-8")
    req = urllib.request.Request(
        TOKEN_URL, data=form, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Google OAuth token refresh failed ({exc.code}): {detail[:1000]}") from None
    if not result.get("access_token"):
        raise RuntimeError("Google OAuth did not return an access token.")
    return result["access_token"]


def api(token, endpoint, params=None, *, method="GET", body=None):
    query = urllib.parse.urlencode(params or {})
    url = f"{API}/{endpoint}" + (f"?{query}" if query else "")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    return request_json(url, method=method, headers=headers, body=body)


def video_id(value):
    value = value.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    parsed = urllib.parse.urlparse(value)
    host = (parsed.hostname or "").lower()
    candidate = None
    if host in ("youtu.be", "www.youtu.be"):
        candidate = parsed.path.strip("/").split("/")[0]
    elif host.endswith("youtube.com") or host.endswith("youtube-nocookie.com"):
        if parsed.path == "/watch":
            candidate = urllib.parse.parse_qs(parsed.query).get("v", [None])[0]
        else:
            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) >= 2 and parts[0] in ("shorts", "embed", "live"):
                candidate = parts[1]
    if candidate and re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate):
        return candidate
    raise ValueError(f"Couldn't recognize a YouTube video ID from: {value}")


def all_pages(token, endpoint, params):
    page_token = None
    while True:
        query = dict(params)
        if page_token:
            query["pageToken"] = page_token
        result = api(token, endpoint, query)
        yield from result.get("items", [])
        page_token = result.get("nextPageToken")
        if not page_token:
            break


def get_or_create_playlist(token):
    for item in all_pages(token, "playlists", {
        "part": "snippet", "mine": "true", "maxResults": 50,
    }):
        if item.get("snippet", {}).get("title") == PLAYLIST_TITLE:
            playlist_id = item["id"]
            print(f'Using existing playlist "{PLAYLIST_TITLE}" ({playlist_id}).')
            return playlist_id

    created = api(token, "playlists", {"part": "snippet,status"}, method="POST", body={
        "snippet": {
            "title": PLAYLIST_TITLE,
            "description": PLAYLIST_DESCRIPTION,
        },
        "status": {"privacyStatus": "public"},
    })
    playlist_id = created.get("id")
    if not playlist_id:
        raise RuntimeError("YouTube did not return a playlist ID after creation.")
    print(f'Created public playlist "{PLAYLIST_TITLE}" ({playlist_id}).')
    return playlist_id


def main():
    raw = os.environ.get("VIDEO_URLS", "")
    values = [item.strip() for item in re.split(r"[\n,]+", raw) if item.strip()]
    if not values:
        raise RuntimeError("Enter at least one YouTube URL or 11-character video ID in the workflow input.")

    ids = []
    for value in values:
        parsed = video_id(value)
        if parsed not in ids:
            ids.append(parsed)

    token = access_token()
    playlist_id = get_or_create_playlist(token)
    existing = set()
    # YouTube may briefly take a moment to make a newly created playlist
    # available to playlistItems.list. Retry only that transient not-found case.
    for attempt in range(5):
        try:
            for item in all_pages(token, "playlistItems", {
                "part": "contentDetails", "playlistId": playlist_id, "maxResults": 50,
            }):
                video = item.get("contentDetails", {}).get("videoId")
                if video:
                    existing.add(video)
            break
        except RuntimeError as exc:
            if "playlistNotFound" not in str(exc) or attempt == 4:
                raise
            wait_seconds = 2 + attempt * 2
            print(f"Playlist is not visible to the items API yet; retrying in {wait_seconds}s.")
            time.sleep(wait_seconds)

    added = 0
    skipped = 0
    for vid in ids:
        if vid in existing:
            print(f"Already in playlist; skipped {vid}.")
            skipped += 1
            continue
        api(token, "playlistItems", {"part": "snippet"}, method="POST", body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": vid},
            }
        })
        print(f"Added video {vid}.")
        added += 1

    print(f"Finished. Added: {added}; already present: {skipped}.")
    print(f"Playlist: https://www.youtube.com/playlist?list={playlist_id}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
