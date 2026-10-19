#!/usr/bin/env python3
"""Discover English-market topics by comparing free Google Trends RSS feeds."""
import os
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict

GEOS = [g.strip().upper() for g in os.getenv(
    "TRENDS_GEOS", "US,GB,CA,AU,NZ,IE"
).split(",") if g.strip()]
MAX_PER_GEO = int(os.getenv("TRENDS_MAX_PER_GEO", "20"))
URL = "https://trends.google.com/trending/rss?geo={}"

def fetch_geo(geo):
    request = urllib.request.Request(URL.format(geo), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        root = ET.fromstring(response.read())
    result = []
    for rank, item in enumerate(root.findall(".//item")[:MAX_PER_GEO], start=1):
        title = re.sub(r"\s+", " ", (item.findtext("title") or "").strip())
        if title:
            result.append((title, rank))
    return result

def main():
    by_key = defaultdict(lambda: {"topic": "", "regions": [], "rank_score": 0, "best_rank": 999})
    failures = []
    for geo in GEOS:
        try:
            for topic, rank in fetch_geo(geo):
                key = topic.casefold()
                entry = by_key[key]
                if not entry["topic"]:
                    entry["topic"] = topic
                entry["regions"].append(geo)
                entry["rank_score"] += max(1, MAX_PER_GEO + 1 - rank)
                entry["best_rank"] = min(entry["best_rank"], rank)
        except Exception as exc:
            failures.append(f"{geo}: {type(exc).__name__}: {exc}")
    if not by_key:
        raise RuntimeError("No regional Google Trends RSS feeds could be read. " + "; ".join(failures))
    # Prioritize topics surfacing in multiple markets, then topics ranking highly in a market.
    ranked = sorted(
        by_key.values(),
        key=lambda x: (len(set(x["regions"])), x["rank_score"], -x["best_rank"]),
        reverse=True
    )
    chosen = ranked[0]
    topic = chosen["topic"][:100]
    with open("topic-discovery-scorecard.txt", "w", encoding="utf-8") as report:
        report.write(
            "English-market trend discovery report\n"
            f"Sources: Google Trends RSS across {len(GEOS)} target markets\n"
            f"Markets queried: {', '.join(GEOS)}\n"
            f"Feeds read successfully: {len(GEOS) - len(failures)}\n"
            f"Unique topics collected: {len(by_key)}\n"
            "Ranking: cross-market recurrence first, then combined feed position.\n"
            "Note: English-speaking target markets are a proxy for international English-language interest, not an official worldwide ranking.\n"
            "YouTube Search API calls for discovery: 0\n\n"
            + "\n".join(
                f"{i+1}. {x['topic']} | markets={','.join(sorted(set(x['regions'])))} | score={x['rank_score']}"
                for i, x in enumerate(ranked[:50])
            )
            + f"\n\nSelected topic: {topic}\n"
            + f"Appeared in markets: {', '.join(sorted(set(chosen['regions'])))}\n"
            + (("\nFeed errors:\n" + "\n".join(failures) + "\n") if failures else "")
        )
    print(
        f"English-market Google Trends: {len(GEOS) - len(failures)}/{len(GEOS)} feeds; 
        "YouTube Search calls: 0.",
        file=sys.stderr
    )
    print(topic)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: English-market trend discovery failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
