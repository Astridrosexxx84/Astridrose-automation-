import os
from datetime import date

from atproto import Client


# A playful, teasing tone. Most posts build curiosity; a few gently point
# interested readers toward the link in your profile.
POSTS = [
    "I can be a good girl… but where’s the fun in that? 😇😈💋",
    "Just a little tease for your timeline. The more tempting things stay behind closed doors 😉🖤",
    "Sweet smile, mischievous thoughts. You’ve been warned 😘😈",
    "If you like the little preview here, there’s more to discover through the link in my profile 💋😉",
    "I do love leaving a little something to the imagination… 🔥",
    "Consider this your little reminder that curiosity can be a very fun thing 😏✨",
    "A little mystery looks good on me, don’t you think? 🖤💋",
    "Enjoying the previews? Take a peek at the link in my profile when you’re ready 😉💋",
]


def main():
    handle = os.environ.get("BLUESKY_HANDLE")
    app_password = os.environ.get("BLUESKY_APP_PASSWORD")
    custom_text = os.environ.get("BLUESKY_POST_TEXT", "").strip()

    if not handle or not app_password:
        raise RuntimeError("Bluesky settings are missing from GitHub Secrets.")

    # Manual test runs can supply BLUESKY_POST_TEXT; scheduled runs rotate
    # through the post list by ISO week so the message changes each week.
    week_number = date.today().isocalendar().week
    post_text = custom_text if custom_text else POSTS[(week_number - 1) % len(POSTS)]

    # Safe test mode: exercise post selection without logging in or publishing.
    if os.environ.get("BLUESKY_DRY_RUN", "false").strip().lower() == "true":
        print(f"DRY RUN: would publish: {post_text}")
        return

    client = Client()
    client.login(handle, app_password)
    client.send_post(text=post_text)
    print("Bluesky post published.")


if __name__ == "__main__":
    main()
