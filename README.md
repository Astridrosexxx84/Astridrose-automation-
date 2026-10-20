# YouTube Curation Automation

Free-first tools for curating YouTube videos into themed playlists using the official YouTube Data API and GitHub Actions.

## Current focus: topic-agnostic discovery and original content

The trend detector chooses a candidate topic; Zelda and Apollo 11 have been examples, not permanent niches. The pipeline must research the subject and audit topic-specific media plus free stock media before choosing a story. Do not assume a popular topic is viable if its usable media supply is weak or rights are unclear.

## What this project does

- Searches YouTube for public video results and saves a review list as a GitHub Actions artifact.
- Adds video URLs selected by the channel owner to a playlist on the owner's own YouTube channel.
- Uses YouTube's own hosted videos and links. It does not download, copy, re-upload, or publish someone else's video.
- Uses manual GitHub Actions runs so the owner reviews results before adding them to the public playlist.

## Important boundaries

A video being publicly viewable on YouTube does not grant permission to download or re-upload it. This project is a curator: it organises and points viewers to original uploads and does not claim authorship of the videos. Use accurate playlist titles and descriptions, and check that each selection fits YouTube's policies.

Playlists can be created and shared on YouTube, including playlists containing videos uploaded by other channels. See [YouTube Help: Create and manage playlists](https://support.google.com/youtube/answer/57792).

This curation approach does not guarantee eligibility for YouTube monetization. If the channel later publishes its own videos, they should add substantial original commentary or other original value and follow YouTube's reused-content rules.

## Cost and security

- Designed for $0 upfront using GitHub Actions and the official YouTube Data API.
- API requests use quota. Do not enable paid billing or enter payment details for this project.
- Store `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, and `YOUTUBE_REFRESH_TOKEN` only as GitHub Actions secrets. Never commit OAuth files, client secrets, or refresh tokens.
- Keep the Google OAuth app in Testing while setting it up; only authorized test users can grant access in that state.

## Workflows

1. **Topic viability audit** — run `.github/workflows/topic-viability-audit.yml`. Enter a topic or leave it blank to use the free Google Trends RSS detector. The workflow researches the topic and inventories leads from Wikimedia Commons and NASA, records licence metadata and rights-review flags, and outputs a scorecard plus CSV/JSON/Markdown artifacts. It makes no YouTube Search API calls and does not publish or modify a channel.
2. **YouTube keyword search** — discovery-only research using the YouTube Data API; results are saved as an artifact for review.
3. **YouTube playlist manager** — a separate, manually triggered tool for adding user-selected URLs to a playlist. Use only with explicit approval.

## Setup status

- [x] Google Cloud project created
- [x] YouTube Data API v3 enabled
- [x] OAuth consent configuration started
- [x] OAuth desktop client created
- [x] Manual playlist workflow and playlist manager script added
- [x] Manual keyword-search workflow added
- [ ] Securely configure credentials in GitHub Actions
- [ ] Authorize the YouTube account and obtain a refresh token
- [ ] Add and test GitHub Actions secrets and OAuth authorization



## Required topic decision gate

Before writing a script or storyboard, research the actual subject, audit relevant free media, check licences and rights, and compare audience opportunity with media coverage, production feasibility, and risk. Read [TOPIC_SELECTION_GATE.md](TOPIC_SELECTION_GATE.md). The audit is a first-pass triage aid, not legal clearance; every chosen asset still requires human review. A public video is not automatically reusable, attribution is not permission, and fair use/fair dealing are not blanket exceptions. Do not build the pipeline around superficial repackaging of other creators' videos.


## Separate project: Brain App

The Brain App is a separate coordinator project being built alongside this content pipeline. Its job is to manage independent projects and let replaceable AI workers take turns through persistent task packets—not to make the social-media pipeline the coordinator.

- [Open the Brain App MVP](brain-app/index.html)
- [Brain App build notes and limitations](brain-app/README.md)

The current MVP saves data in the current browser and supports JSON backup/import and manual handoffs. It does not yet make AI API calls or connect ChatGPT automatically. Provider keys must stay server-side; automatic workers and verified free-tier failover are future milestones.
