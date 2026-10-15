"""Optional Reddit integration for the Bluesky bot.

Safe by default: authenticates and reports the account, but never publishes unless
REDDIT_PUBLISH is explicitly set to "true" in the workflow.
"""
import os
import sys

import praw


def required(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing GitHub Actions secret/environment value: {name}. "
            "Add the required Reddit API credentials in repository Settings > Secrets and variables > Actions."
        )
    return value


def main():
    client_id = required("REDDIT_CLIENT_ID")
    client_secret = required("REDDIT_CLIENT_SECRET")
    username = required("REDDIT_USERNAME")
    password = required("REDDIT_PASSWORD")
    user_agent = os.environ.get(
        "REDDIT_USER_AGENT",
        f"script:bluesky-ai-bot:v1.0 (by u/{username})",
    ).strip()

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        username=username,
        password=password,
        user_agent=user_agent,
    )

    # Verify that Reddit accepted the credentials before doing anything else.
    account = reddit.user.me()
    if account is None:
        raise RuntimeError("Reddit authentication did not return an account.")
    print(f"Reddit authentication successful for u/{account.name}.")

    publish = os.environ.get("REDDIT_PUBLISH", "false").strip().lower() == "true"
    if not publish:
        print("SAFE TEST ONLY: no Reddit post was published. Set REDDIT_PUBLISH=true only when ready.")
        return

    subreddit_name = required("REDDIT_SUBREDDIT").removeprefix("r/").strip()
    title = required("REDDIT_POST_TITLE")
    body = required("REDDIT_POST_BODY")

    if title.lower().startswith("test") and subreddit_name.lower() != "test":
        print("Reminder: test posts should go to a subreddit where you have permission to test.")

    submission = reddit.subreddit(subreddit_name).submit(title=title, selftext=body)
    print(f"Reddit post published: https://www.reddit.com{submission.permalink}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Reddit integration failed: {exc}", file=sys.stderr)
        raise
