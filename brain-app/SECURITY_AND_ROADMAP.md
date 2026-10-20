# Brain App — Security and Forward Roadmap

Last reviewed: 2026-10-21

## Current verified boundary

- The GitHub repository is public.
- GitHub Pages serves a static dashboard; anyone with the URL can load it.
- Project/task data in the dashboard is stored in that browser, not in an authenticated shared database.
- The relay can be triggered by committing `brain-app/relay-request.json`; that request is part of public Git history.
- Relay artifacts can contain the full task packet and AI responses. Treat them as potentially accessible to repository readers.
- `brain-app/relay-status.json` is designed to expose status metadata only.
- Provider API keys belong only in GitHub Actions secrets. Never place them in HTML, JavaScript, browser storage, task packets, commits, or chat.
- The dashboard and relay are not yet automatically synchronised end-to-end.

## Security rules until a private bridge exists

1. Use only generic, non-sensitive test tasks with the current public relay.
2. Never include personal details, private business plans, credentials, API keys, tokens, or confidential client data in relay requests.
3. Do not embed a GitHub token or provider key in the browser app.
4. Do not assume that hiding a URL, adding a robots.txt file, or changing the dashboard UI makes a public site private.
5. Do not change repository visibility until the hosting impact is understood; GitHub Pages access and repository access are separate concerns.
6. Do not enable paid services or paid model routes without explicit approval.

## Roadmap — broad strokes first

### P0 — Contain exposure
- Owner changes repository visibility only after reviewing the impact on GitHub Pages and Actions.
- Check repository history for accidentally committed credentials; if any are found, revoke/rotate them immediately rather than merely deleting the current file.
- Keep relay tasks generic while repository and artifact access remain public.

### P1 — Reliable working control room
- Add clear separation between local draft tasks and tasks deliberately sent to the relay.
- Make the UI explain what leaves the browser and where the output will be stored before dispatch.
- Improve error states, run freshness, and artifact/result import feedback.
- Add or retain automated checks for JavaScript syntax, relay tests, status schema, and privacy boundaries.

### P2 — Private task and result transport
- Choose a genuinely free hosting/authentication/storage design before implementation.
- Require authentication and server-side authorization for private task content.
- Store provider credentials only in server-side secrets.
- Return private results only to an authorized user; do not put prompts or model responses into public Git history or public artifacts.
- Test unauthorized access and cross-user isolation before using real business data.

### P3 — Useful multi-AI coordination
- Synchronise project/task packets with the authenticated backend.
- Run workers sequentially with explicit budgets, retries, and stop conditions.
- Record which workers actually ran and distinguish verified results from suggestions.
- Keep publishing, account changes, and any paid usage behind explicit approval.

## Definition of done for the next milestone

The Brain App is not considered private or production-ready until private task text and AI responses are inaccessible to unauthenticated visitors, credentials remain server-side, and a test confirms the browser dashboard can securely submit a task and retrieve its result without committing the content to public Git history.
