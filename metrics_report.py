"""Summarize the metrics log without external dependencies."""
import csv
from pathlib import Path

SOURCE = Path("metrics.csv")
OUTPUT = Path("metrics-report.md")
NUMERIC = ("impressions", "likes", "replies", "reposts", "link_clicks", "signups", "sales", "revenue_nzd", "cost_nzd", "minutes_spent")


def main():
    with SOURCE.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    totals = {key: 0.0 for key in NUMERIC}
    for row in rows:
        for key in NUMERIC:
            try:
                totals[key] += float(row.get(key) or 0)
            except ValueError:
                pass
    totals["profit_nzd"] = totals["revenue_nzd"] - totals["cost_nzd"]
    lines = [
        "# Automation metrics report", "",
        f"- Rows recorded: {len(rows)}",
        f"- Impressions: {totals['impressions']:g}",
        f"- Engagements (likes + replies + reposts): {totals['likes'] + totals['replies'] + totals['reposts']:g}",
        f"- Link clicks: {totals['link_clicks']:g}",
        f"- Sign-ups: {totals['signups']:g}",
        f"- Sales: {totals['sales']:g}",
        f"- Revenue (NZD): {totals['revenue_nzd']:.2f}",
        f"- Costs (NZD): {totals['cost_nzd']:.2f}",
        f"- Net tracked result (NZD): {totals['profit_nzd']:.2f}",
        f"- Time spent (minutes): {totals['minutes_spent']:g}",
        "",
        "## Notes",
        "- Empty metrics are treated as zero; update the CSV after publishing.",
        "- This report does not fetch platform analytics automatically.",
        "- A positive result is not guaranteed; use clicks, sign-ups, and sales to judge demand.",
        "",
    ]
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT} from {len(rows)} metrics row(s).")


if __name__ == "__main__":
    main()
