# bluesky-ai-bot

AI-assisted Bluesky posting bot with an optional, separate Reddit integration.

## Reddit integration status

The Reddit integration is **manual-only** and **safe by default**. It checks OAuth access but does not publish unless the workflow's `publish` input is explicitly set to true. It is not scheduled and will not affect the existing Bluesky workflow.

**Important:** Reddit currently requires explicit approval before accessing Reddit data through its API. Because this project is intended to support a paid-content funnel, obtain Reddit's written permission for the commercial use case before connecting or publishing. Follow Reddit's [Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy) and [API access guidance](https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data). Do not attempt to bypass approval.

### When Reddit approves the app

Add these under GitHub repository **Settings → Secrets and variables → Actions**:

- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_REFRESH_TOKEN` (OAuth token authorized for the required scope)
- `REDDIT_USERNAME` (username only, without `u/`)
- Optional: `REDDIT_USER_AGENT` (a truthful, unique identifier for this app)

Never put credentials in source code or send them in chat.

### Test the connection

1. Open **Actions → Test Reddit bot → Run workflow**.
2. Leave **publish** set to false.
3. Run it and inspect the log. A successful test reports the authorized Reddit account and confirms no post was published.
4. Only after access approval and subreddit-rule checks, enable publishing manually and provide a title, body, and subreddit.

The Reddit workflow has no scheduled trigger. Do not automate repetitive promotional posts or post to communities that prohibit promotion.
