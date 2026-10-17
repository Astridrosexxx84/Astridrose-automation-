#!/usr/bin/env python3
"""Search YouTube for public videos by keyword; this script does not modify YouTube."""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://www.googleapis.com/youtube/v3"
TOKEN_URL = "https://oauth2.googleapis.com/token"


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
    req = urllib.request.Request(TOKEN_URL, data=form, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Google OAuth refresh failed ({exc.code}): {detail[:1000]}") from None
    if not payload.get("access_token"):
        raise RuntimeError("Google OAuth did not return an access token.")
    return payload["access_token"]


def search(token, query, max_results):
    params = urllib.parse.urlencode({
        "part": "snippet",
        "type": "video",
        "q": query,
        "maxResults": max_results,
        "order": "relevance",
        "safeSearch": "moderate",
    })
    req = urllib.request.Request(
        f"{API}/search?{params}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode()).get("items", [])
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"YouTube search failed ({exc.code}): {detail[:1200]}") from None


def main():
    query = os.environ.get("SEARCH_QUERY", "").strip()
    if not query:
        raise RuntimeError("Enter a keyword or phrase in the workflow input.")
    try:
        max_results = max(1, min(25, int(os.environ.get("MAX_RESULTS", "10"))))
    except ValueError:
        max_results = 10

    items = search(get_access_token(), query, max_results)
    lines = [
        f'YouTube search for: {query}',
        f'Results returned: {len(items)}',
        '',
        'Review these results before adding them to your playlist:',
        '',
    ]
    if not items:
        lines.append("No results returned. Try a broader keyword.")
    for index, item in enumerate(items, start=1):
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})
        if not video_id:
            continue
        title = " ".join(snippet.get("title", "").split())
        channel = " ".join(snippet.get("channelTitle", "").split())
        published = snippet.get("publishedAt", "")[:10]
        url = f"https://www.youtube.com/watch?v={video_id}"
        line = f"{index}. {title}\n   Channel: {channel} | Published: {published}\n   {url}"
        print(line)
        lines.append(line)
    with open("youtube-search-results.txt", "w", encoding="utf-8") as output:
        output.write("\n".join(lines) + "\n")
    print("\nSaved results to youtube-search-results.txt (workflow artifact).")
    print("This search-only tool did not add videos or change any playlist.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
