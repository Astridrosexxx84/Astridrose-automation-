import os
from atproto import Client


def main():
    handle = os.environ.get("BLUESKY_HANDLE")
    app_password = os.environ.get("BLUESKY_APP_PASSWORD")
    post_text = os.environ.get(
        "BLUESKY_POST_TEXT",
        "Hello Bluesky! My automated bot is running."
    )

    if not handle or not app_password:
        raise RuntimeError("Bluesky settings are missing from GitHub Secrets.")

    client = Client()
    client.login(handle, app_password)
    client.send_post(text=post_text)
    print("Bluesky post published.")


if __name__ == "__main__":
    main()
