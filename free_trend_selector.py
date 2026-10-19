#!/usr/bin/env python3
"""Choose a topic from Google's free live-trends RSS without using YouTube Search quota."""
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

GEO = os.getenv("TRENDS_GEO", "NZ").strip().upper() or "NZ"
URL = f"https://trends.google.com/trending/rss?geo={GEO}"

def main():
    request = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=25) as response:
        root = ET.fromstring(response.read())
    topics = []
    for item in root.findall(".//item"):
        title = re.sub(r"\s+", " ", (item.findtext("title") or "").strip())
        if title and title.lower() not in {x.lower() for x in topics}:
            topics.append(title)
        if len(topics) >= 20:
            break
    if not topics:
        raise RuntimeError(f"Google Trends RSS returned no topics for geo={GEO}.")
    # RSS order is the provider's current ordering; avoid any YouTube Search API call.
    topic = topics[0][:100]
    with open("topic-discovery-scorecard.txt", "w", encoding="utf-8") as report:
        report.write(
            "Free trend discovery report\n"
            f"Source: Google Trends live RSS ({GEO})\n"
            f"Topics returned: {len(topics)}\n"
            "Selection: first topic in the feed's current order.\n"
            "YouTube Search API calls for topic discovery: 0\n\n"
            + "\n".join(f"{i+1}. {t}" for i, t in enumerate(topics))
            + f"\\n\\nSelected topic: {topic}\n"
        )
    print(f"Selected from Google Trends RSS ({GEO}); YouTube Search calls: 0.", file=sys.stderr)
    print(topic)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: free trend discovery failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
