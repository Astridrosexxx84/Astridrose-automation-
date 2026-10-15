"""Generate a Reddit draft without connecting to Reddit or publishing anything."""
from datetime import date
from pathlib import Path

DRAFTS = [
    ("A little mystery never hurt anyone 😉",
     "Sweet smile, mischievous thoughts. I do like leaving a little to the imagination 😘😈"),
    ("Just a little tease for your timeline 🖤",
     "I can be a good girl… but where’s the fun in that? 😇😈 A little mystery makes things more interesting."),
    ("Curious? That was kind of the idea 😏",
     "A little preview, a little tease, and plenty left to discover 💋"),
    ("Sweet on the surface… maybe 😉",
     "I like keeping things playful and leaving you wondering what comes next 😘✨"),
    ("A little temptation for your day 💋",
     "Consider this your reminder that curiosity can be a very fun thing 😏🖤"),
    ("I do love a little mystery 😈",
     "Not everything needs to be revealed at once… some things are more fun to discover slowly 😉"),
    ("A hint is sometimes better than the whole story 😉",
     "Just stopping by to add a little mischief to your feed. What can I say? 😘"),
    ("If you like a little tease… 🖤",
     "I’m a fan of playful previews and keeping things interesting. The rest is for the curious 💋"),
]


def main():
    week = date.today().isocalendar().week
    title, body = DRAFTS[(week - 1) % len(DRAFTS)]
    today = date.today().isoformat()
    content = f"""# Reddit post draft

Generated: {today}

**Title**

{title}

**Body**

{body}

---

**Before posting:** Choose a subreddit that allows adult creators and self-promotion, read its rules, and add your profile/content link only if permitted. This file is a draft; nothing has been posted to Reddit.
"""
    Path("reddit-draft.md").write_text(content, encoding="utf-8")
    print(f"Generated Reddit draft for {today}. Nothing was posted.")


if __name__ == "__main__":
    main()
