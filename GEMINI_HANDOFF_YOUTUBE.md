# Gemini Handoff — YouTube Curation Only
Last updated: 2026-10-18

## Please read first
Read `PROJECT_STATUS.md` and this handoff before making changes. The user wants the AIs to coordinate through shared GitHub files and verify work instead of repeatedly asking the user to click around. The user is working from the GitHub mobile app on Android and needs one small, clear next step only when user action is unavoidable.

## Goal and boundaries
- Build a free-first, phone-friendly YouTube curation workflow for **Dragon Ball Z nostalgia**.
- For now, only YouTube research, discovery, and playlist building. No social-media or promotional work.
- Curate links to original YouTube uploads; do not download, copy, or re-upload other creators' videos.
- Search results must be reviewed by the user before videos are added to their public playlist.
- Do not enable paid billing or ask the user to paste credentials into chat.
- Keep credentials only in GitHub Actions Secrets. Never print or commit secrets.

## Repository
https://github.com/Astridrosexxx84/Astridrose-automation-

Relevant files:
- `PROJECT_STATUS.md` — durable project state and shared AI coordination rules.
- `.github/workflows/youtube-keyword-search.yml` — weekly scheduled and manual discovery workflow.
- `youtube_keyword_search.py` — search script.
- `.github/workflows/youtube-playlist-manager.yml` and `youtube_playlist_manager.py` — playlist workflow; this can modify the user's YouTube playlist, so only run it with user-selected URLs and clear consent.
- `README.md` — project scope and setup notes.

## Verified technical evidence
- The keyword-search workflow runs checkout and Python setup successfully, but the latest observed run failed at the step **“Search YouTube (discovery only; no posts or playlist changes)”**. Artifact upload was skipped because the search step failed.
- Latest failed run: https://github.com/Astridrosexxx84/Astridrose-automation-/actions/runs/39092734298
- Previous failed run: https://github.com/Astridrosexxx84/Astridrose-automation-/actions/runs/39092516493
- The AI-team coordinator workflow has had successful runs, so the repo's coordinator mechanism is not itself the current YouTube blocker.
- The keyword workflow uses these GitHub Actions secret names: `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, and `YOUTUBE_REFRESH_TOKEN`.
- The user recently said all three secrets were present/saved, but whether the values are correct and whether OAuth refresh succeeds has **not** been verified. GitHub integrations cannot read secret values. Do not infer that a secret is valid merely because it exists.
- `PROJECT_STATUS.md` and README setup checklists may be stale on whether secrets have been added. Reconcile them after verifying the actual run; never reveal secret values.
- The workflow's scheduled fallback query is still a generic 1990s-cartoon query, despite the current Dragon Ball Z-only scope. Do not change unrelated workflow logic while diagnosing the authentication failure unless needed and explain the change.

## What I need you (Gemini) to do
1. Inspect the failed run linked above. Open the failed step's logs and identify the exact exception/error text. Do not guess from the red X alone.
2. Inspect `youtube_keyword_search.py` and the OAuth setup assumptions. Determine whether the error indicates a missing secret, invalid client ID/secret, bad/expired refresh token, OAuth client-type mismatch, API enablement issue, quota issue, or a script bug.
3. Recommend the **smallest safe next action** based on the log. Avoid sending the user back through Google Cloud screens unless the log proves that is necessary. The user has already spent substantial time trying to retrieve the client secret.
4. If code changes are justified, inspect the full current file first, make the minimal change, and explain why. Do not modify playlist behavior or run the playlist-manager workflow during this diagnosis.
5. After a fix, verify by rerunning the read-only keyword-search workflow with a Dragon Ball Z query, then check that the run succeeds and the `dbz-video-candidates` artifact exists. If you cannot trigger or inspect a run with your tools, state that limitation honestly.
6. Update `PROJECT_STATUS.md` with verified facts, the exact error/root cause, what changed, run link/result, and the next single action. Do not mark credentials as verified until a workflow proves they work.
7. Return a concise report to the user and ChatGPT: evidence, diagnosis, change (if any), test result, and one next step.

## Security and coordination
- Never request, echo, or commit OAuth secrets, refresh tokens, API keys, or credential files.
- Do not make public playlist changes without the user's chosen video URLs and explicit go-ahead.
- Keep shared project files factual and dated. If evidence is incomplete, say so.
- Do not claim to have tested anything unless the relevant workflow result/log has actually been inspected.
