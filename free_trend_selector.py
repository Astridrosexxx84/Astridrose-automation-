#!/usr/bin/env python3
"""Discover broad English-market trends and rank them for viral video potential.

Uses free Google Trends RSS feeds only. This is a discovery heuristic, not a claim
that a topic is guaranteed to go viral. Sex appeal is a meaningful bonus, never a
hard niche filter; gaming, sports, cars, tech, entertainment and other topics stay eligible.
"""
import math
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict

GEOS = [g.strip().upper() for g in os.getenv(
    "TRENDS_GEOS", "US,GB,CA,AU,NZ,IE"
).split(",") if g.strip()]
MAX_PER_GEO = int(os.getenv("TRENDS_MAX_PER_GEO", "20"))
URL = "https://trends.google.com/trending/rss?geo={}"

# Adult, non-explicit sex-appeal / provocative-entertainment signals.
SEX_APPEAL_TERMS = {
    "model", "models", "bikini", "bikinis", "lingerie", "cleavage", "curvy",
    "curves", "swimsuit", "swimwear", "fashion model", "onlyfans", "influencer",
    "influencers", "beauty", "hot", "sexy", "glamour", "glamorous", "miss universe",
    "victoria's secret", "fashion show", "fitness model", "cosplay", "cheerleader",
    "cheerleaders", "actress", "celebrity", "dating", "romance", "reality tv"
}
MALE_AUDIENCE_TERMS = {
    "gaming", "game", "football", "soccer", "basketball", "ufc", "mma", "boxing",
    "wrestling", "cars", "car", "supercar", "motorcycle", "motogp", "formula 1",
    "f1", "tech", "iphone", "android", "pc", "gpu", "anime", "movie", "trailer",
    "celebrity", "model", "models", "bikini", "fitness", "bodybuilding", "viral"
}
HIGH_VIDEO_POTENTIAL_TERMS = {
    "trailer", "leaked", "reaction", "vs", "challenge", "highlights", "final",
    "launch", "revealed", "update", "new", "live", "fight", "comeback", "drama",
    "scandal", "record", "review", "explained", "fails", "best", "worst"
}

def clean(value):
    return re.sub(r"\s+", " ", (value or "").strip())

def parse_traffic(value):
    """Convert approximate traffic strings such as '20K+' to a rough numeric proxy."""
    value = clean(value).upper().replace(",", "").replace("+", "")
    match = re.search(r"(\d+(?:\.\d+)?)\s*([KMB]?)", value)
    if not match:
        return 0
    amount = float(match.group(1))
    multiplier = {"": 1, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[match.group(2)]
    return int(amount * multiplier)

def fetch_geo(geo):
    request = urllib.request.Request(URL.format(geo), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        root = ET.fromstring(response.read())
    result = []
    for rank, item in enumerate(root.findall(".//item")[:MAX_PER_GEO], start=1):
        title = clean(item.findtext("title"))
        if not title:
            continue
        traffic = 0
        for element in item.iter():
            if element.tag.split("}")[-1].casefold() == "approx_traffic":
                traffic = parse_traffic(element.text or "")
                break
        news_titles = []
        for element in item.iter():
            if element.tag.split("}")[-1].casefold() == "news_item_title" and element.text:
                news_titles.append(clean(element.text))
        result.append({"topic": title, "rank": rank, "traffic": traffic,
                       "news_titles": news_titles[:4]})
    return result

def phrase_hits(text, terms):
    folded = text.casefold()
    return [term for term in sorted(terms, key=len, reverse=True)
            if re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", folded)]

def score_topic(entry, geo_count, max_rank_score):
    topic = entry["topic"]
    context = " ".join([topic] + entry.get("news_titles", []))
    sex_hits = phrase_hits(context, SEX_APPEAL_TERMS)
    audience_hits = phrase_hits(context, MALE_AUDIENCE_TERMS)
    video_hits = phrase_hits(context, HIGH_VIDEO_POTENTIAL_TERMS)

    # Recurrence and position are the main signal; RSS traffic is a rough extra signal.
    recurrence = min(30, max(0, (geo_count - 1) * 6))
    rank_signal = min(30, round(entry["rank_score"] / max(1, max_rank_score) * 30))
    traffic = entry.get("traffic", 0)
    traffic_signal = min(20, round(math.log10(max(1, traffic)) * 3.2)) if traffic else 0
    # Deliberate bonus for the requested adult-audience appeal without forcing the whole channel into one niche.
    sex_bonus = min(24, len(sex_hits) * 8)
    audience_bonus = min(10, len(audience_hits) * 2)
    video_bonus = min(10, len(video_hits) * 2)
    final = recurrence + rank_signal + traffic_signal + sex_bonus + audience_bonus + video_bonus
    return {
        **entry,
        "markets_count": geo_count,
        "traffic_signal": traffic_signal,
        "sex_appeal_hits": sex_hits,
        "sex_appeal_bonus": sex_bonus,
        "audience_hits": audience_hits,
        "audience_bonus": audience_bonus,
        "video_potential_hits": video_hits,
        "video_potential_bonus": video_bonus,
        "final_score": final,
    }

def main():
    by_key = defaultdict(lambda: {"topic": "", "regions": [], "rank_score": 0,
                                  "best_rank": 999, "traffic": 0, "news_titles": []})
    failures = []
    for geo in GEOS:
        try:
            for item in fetch_geo(geo):
                topic, rank = item["topic"], item["rank"]
                entry = by_key[topic.casefold()]
                if not entry["topic"]:
                    entry["topic"] = topic
                entry["regions"].append(geo)
                entry["rank_score"] += max(1, MAX_PER_GEO + 1 - rank)
                entry["best_rank"] = min(entry["best_rank"], rank)
                entry["traffic"] = max(entry["traffic"], item["traffic"])
                entry["news_titles"].extend(item["news_titles"])
        except Exception as exc:
            failures.append(f"{geo}: {type(exc).__name__}: {exc}")
    if not by_key:
        raise RuntimeError("No regional Google Trends RSS feeds could be read. " + "; ".join(failures))

    max_rank_score = max(x["rank_score"] for x in by_key.values())
    ranked = []
    for entry in by_key.values():
        markets = len(set(entry["regions"]))
        ranked.append(score_topic(entry, markets, max_rank_score))
    ranked.sort(key=lambda x: (
        x["final_score"], x["markets_count"], x["rank_score"], -x["best_rank"]
    ), reverse=True)

    chosen = ranked[0]
    topic = chosen["topic"][:100]
    with open("topic-discovery-scorecard.txt", "w", encoding="utf-8") as report:
        report.write(
            "English-market trend discovery report\n"
            f"Sources: free Google Trends RSS across {len(GEOS)} target markets\n"
            f"Markets queried: {', '.join(GEOS)}\n"
            f"Feeds read successfully: {len(GEOS) - len(failures)}\n"
            f"Unique topics collected: {len(by_key)}\n"
            "Ranking: cross-market recurrence + RSS traffic proxy + search position, with bonuses for sex appeal, male-audience relevance, and video-friendly hooks.\n"
            "Sex appeal is a bonus, not a hard filter; broad topic discovery remains enabled.\n"
            "Traffic values are approximate feed metadata, not YouTube views.\n"
            "This score is a heuristic, not a prediction or guarantee of virality.\n"
            "YouTube Search API calls for discovery: 0\n\n"
            + "\n".join(
                f"{i+1}. {x['topic']} | markets={','.join(sorted(set(x['regions'])))} | score={x['rank_score']} | final={x['final_score']} | traffic={x['traffic'] or 'n/a'} | sex_appeal={','.join(x['sex_appeal_hits']) or 'none'} | audience={','.join(x['audience_hits']) or 'none'} | hooks={','.join(x['video_potential_hits']) or 'none'}"
                for i, x in enumerate(ranked[:50])
            )
            + f"\n\nSelected topic: {topic}\n"
            + f"Final score: {chosen['final_score']} | traffic proxy: {chosen['traffic'] or 'not supplied'}\n"
            + f"Appeared in markets: {', '.join(sorted(set(chosen['regions'])))}\n"
            + f"Sex-appeal bonus: {chosen['sex_appeal_bonus']} | matches: {', '.join(chosen['sex_appeal_hits']) or 'none'}\n"
            + (("\nFeed errors:\n" + "\n".join(failures) + "\n") if failures else "")
        )
    print(
        f"English-market Google Trends: {len(GEOS) - len(failures)}/{len(GEOS)} feeds; "
        f"unique topics: {len(by_key)}; top score: {chosen['final_score']}; YouTube Search calls: 0.",
        file=sys.stderr
    )
    print(topic)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: English-market trend discovery failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
