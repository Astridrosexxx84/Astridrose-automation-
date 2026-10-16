"""Generate a neutral Reddit hello test draft without publishing anything."""
from datetime import date
from pathlib import Path


def main():
    today = date.today().isoformat()
    content = f"""# Reddit proof-of-concept draft

Generated: {today}

**Title**

Hello

**Body**

Hello!

---

This is a neutral mechanics test only. Before any automated posting, confirm official Reddit API access is approved and choose a subreddit whose rules allow this post. Nothing has been posted to Reddit.
"""
    Path("reddit-draft.md").write_text(content, encoding="utf-8")
    print(f"Generated neutral Reddit test draft for {today}. Nothing was posted.")


if __name__ == "__main__":
    main()
