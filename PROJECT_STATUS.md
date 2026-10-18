# Project Coordinator Handover

Last checked: 2026-10-18

## Active goal (current instruction takes priority)
Work only on YouTube curation and playlist-building for Dragon Ball Z for now. Do not create social-media posts or promotional content. Use existing YouTube uploads and links; do not download or re-upload other creators' videos. Work phone-first, $0 upfront, and give the user one small next step at a time.

## Repository
- Repository: Astridrosexxx84/Astridrose-automation-
- Default branch: main
- Public repository; GitHub integration can read and write.
- Existing files include README.md, AI_TEAM_SETUP.md, AUTOMATION_PLAN.md, ai_team_coordinator.py, youtube_keyword_search.py, youtube_playlist_manager.py, and GitHub Actions workflows.

## Verified current setup
- A manual multi-provider AI coordinator workflow exists: .github/workflows/ai-team-coordinator.yml.
- It calls Gemini, Groq, and OpenRouter free models for analysis only and uploads a report artifact. Latest observed run #4 succeeded on 2026-10-17. Earlier run #2 and #1 failed; later run #4 succeeded.
- YouTube keyword search workflow exists: .github/workflows/youtube-keyword-search.yml. It is configured with a weekly schedule and manual dispatch. It requires YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, and YOUTUBE_REFRESH_TOKEN secrets.
- YouTube playlist manager workflow exists: .github/workflows/youtube-playlist-manager.yml. It requires the same three YouTube OAuth secrets and selected video URLs.
- README says Google Cloud project and YouTube Data API v3 are set up and an OAuth desktop client was created.
- README still lists secure credential configuration, authorization/refresh-token acquisition, and Actions secret testing as incomplete.
- No secret values are readable through this integration; never ask the user to paste keys or tokens into chat.
- The recent workflow-run listing did not show a completed YouTube search or playlist-manager run. Treat those workflows as unverified until a run is checked.

## Important mismatch to correct later
The scheduled keyword workflow's fallback query is a general 1990s-cartoon query, while the user's current choice is Dragon Ball Z only. Do not change workflow files until the current OAuth blocker is resolved or the user explicitly asks to change it.

## Next action
Continue the YouTube OAuth setup, using text-only phone instructions if the user cannot send screenshots. First establish the exact current Google Cloud screen and which OAuth step is unfinished. Then finish the approved OAuth flow and store credentials only in GitHub Actions secrets. Do not enable paid billing. Once secrets are configured, manually run the YouTube keyword-search workflow with a Dragon Ball Z query, inspect its artifact, and only then test playlist changes with user-selected video URLs.

## Coordinator rules
- Read this file first when resuming work.
- Keep it updated when a milestone changes.
- Delegate independent research or review to Gemini/Groq/OpenRouter only if their free quotas are available; do not treat provider switching as a way to bypass usage limits.
- Prefer deterministic scripts and scheduled GitHub Actions over using AI calls for repeatable tasks.
- Keep the user in control of public playlist changes and any publishing.
