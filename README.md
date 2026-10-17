# YouTube Curation Automation

Free-first tools for curating YouTube videos into themed playlists using the official YouTube Data API and GitHub Actions.

## Current focus: 90s Cartoon Nostalgia

The first channel theme is nostalgia for cartoons from the 1990s. Search ideas include:
- 90s cartoon opening themes
- Saturday morning cartoons from the 1990s
- forgotten 90s animated series
- official cartoon channel uploads and retrospectives

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

1. **YouTube keyword search** — enter a query such as `90s cartoon opening themes`; results are saved as an artifact for review. It does not change YouTube.
2. **YouTube playlist manager** — enter the URLs of selected videos. The script creates or reuses the channel's `90s Cartoon Nostalgia` playlist and adds the chosen videos.

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

