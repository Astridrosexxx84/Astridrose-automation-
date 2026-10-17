# Astrid Rose Automation

Free-first automation tools for the Astrid Rose creator project.

## Current focus: YouTube playlist management

The first tool will add selected public YouTube videos to a playlist owned by the channel. It will use the official YouTube Data API and GitHub Actions, with manual runs only.

- No videos are downloaded or re-uploaded.
- No public posts or comments are published by this tool.
- The workflow will only change playlists after Google OAuth has been authorized.
- Google OAuth credentials and refresh tokens must be stored as GitHub Actions secrets, never committed to this repository or pasted into chat.
- Keep the Google OAuth app in **Testing** while setting it up. Only authorized test users can grant access in that state.

## Cost and safety

This project is designed for a $0 upfront budget. YouTube Data API requests use quota; do not enable paid billing or enter payment details for this project. Review current Google API quota and OAuth policies before expanding use.

## Other tools

Existing content planning and metrics files are retained for now, but this repository is no longer a Bluesky bot. Old files will only be removed or renamed when their purpose has been checked so useful work is not lost.

## Setup status

- [x] Google Cloud project created
- [x] YouTube Data API v3 enabled
- [x] OAuth consent configuration started
- [x] OAuth desktop client created
- [ ] Securely configure credentials in GitHub Actions
- [ ] Authorize the YouTube account and obtain a refresh token
- [ ] Add and test the manual playlist workflow

Never commit downloaded OAuth JSON files or secrets.
