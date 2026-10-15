"""Optional Reddit integration for the Bluesky bot.

Safe by default: authenticates and reports the account, but never publishes unless
REDDIT_PUBLISH is explicitly set to "true" in the workflow.
Requires Reddit-approved API access. Do not use before Reddit authorizes the app.
"""
import os
import sys

import praw


def required(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing GitHub Actions secret/environment value: {name}. "
            "Add the required Reddit OAuth credentials in repository Settings > Secrets and variables > Actions."
        )
    return value


def main():
    client_id = required("REDDIT_CLIENT_ID")
    client_secret = required("REDDIT_CLIENT_SECRET")
    refresh_token = required("REDDIT_REFRESH_TOKEN")
    expected_username = required("REDDIT_USERNAME")
    user_agent = (
        os.environ.get("REDDIT_USER_AGENT", "").strip()
        or f"script:bluesky-ai-bot:v1.0 (by u/{expected_username})"
    )

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        user_agent=user_agent,
    )

    # Verify the authorized account before doing anything else.
    account = reddit.user.me()
    if account is None:
        raise RuntimeError("Reddit OAuth did not return an authenticated account.")
    if account.name.lower() != expected_username.lower():
        raise RuntimeError(
            f"OAuth token belongs to u/{account.name}, but REDDIT_USERNAME is "
            f"u/{expected_username}. Check the configured account."
        )
    print(f"Reddit OAuth check successful for u/{account.name}.")

    publish = os.environ.get("REDDIT_PUBLISH", "false").strip().lower() == "true"
    if not publish:
        print("SAFE TEST ONLY: no Reddit post was published. Set REDDIT_PUBLISH=true only when ready.")
        return

    subreddit_name = required("REDDIT_SUBREDDIT").removeprefix("r/").strip()
    title = required("REDDIT_POST_TITLE")
    body = required("REDDIT_POST_BODY")

    submission = reddit.subreddit(subreddit_name).submit(title=title, selftext=body)
    print(f"Reddit post published: https://www.reddit.com{submission.permalink}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Reddit integration failed: {exc}", file=sys.stderr)
        raise
