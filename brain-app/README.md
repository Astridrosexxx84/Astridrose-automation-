# Brain App — MVP

The Brain App is the coordinator/control room. AI providers are replaceable workers that take turns using a shared handoff packet.

## Current capabilities
- Mobile-friendly project dashboard with separate projects and task queues; the first task in the selected project opens automatically so the work packet is visible immediately.
- Browser-local storage and JSON backup/import.
- First Supabase sign-in and cloud-sync code is present, but end-to-end browser sync remains unverified; do not rely on it as the only copy of important work yet.
- A free GitHub Actions smoke-check workflow now runs JavaScript syntax checks and verifies that the app's referenced UI IDs and core database contract are present.
- Task packet fields autosave as you type without re-rendering the editor; switching projects also saves the current packet first.
- Live relay status refreshes automatically every 60 seconds while the dashboard is visible.
- Portable work packets containing goal, context, current output and next action.
- Copy or download a relay-request JSON generated from the selected task, with an explicit public-repository warning before task text is included. This prepares the request but does not itself dispatch the workflow; it still needs to be committed to `brain-app/relay-request.json`.
- Import relay result: load `brain-relay-packet.json` from a downloaded relay artifact. Requests created from a task now carry its local task/project IDs through the workflow, and the app automatically selects the matching task before importing. If that task ID is missing from the current browser workspace, import is refused rather than attaching results to the wrong task. Older results without IDs still require selecting the intended task first.
- GitHub Actions relay that attempts configured providers in sequence and records the combined result.
- A file-triggered relay request: updating `brain-app/relay-request.json` on `main` automatically starts the relay. ChatGPT can queue work by committing this request file through the connected GitHub integration, without a user click.
- A live dashboard status panel reads a metadata-only status file updated by the relay workflow. It shows each provider result and links to the run, without publishing prompts, task content, model responses or API keys.
- Relay workers are text-only API calls with no repository tools. Their outputs are proposals, not applied changes; any claim that a file was created, edited, tested or deployed must be independently verified by the coordinator before it is treated as fact.
- Latest completed live relay reviewed (run #11, 2026-10-20): Groq (`allam-2-7b`), Gemini (`gemini-flash-lite-latest`), and OpenRouter (`cohere/north-mini-code:free`) all succeeded (3/3). A previous run had OpenRouter HTTP 429 (2/3), so this is evidence of one successful run—not a guarantee every future run will succeed. The chain labels partial completion separately.

## Open the dashboard
https://astridrosexxx84.github.io/Astridrose-automation-/brain-app/

## Run the sequential relay
There are two routes:
1. **Assistant-driven:** update `brain-app/relay-request.json` on `main`. That commit triggers the workflow automatically.
2. **Manual fallback:** open the [Brain App relay workflow](https://github.com/Astridrosexxx84/Astridrose-automation-/actions/workflows/brain-app-relay.yml), choose **Run workflow**, and enter a goal.

The chain order is Groq → Gemini → OpenRouter. Each successful worker passes its packet to the next; failures are recorded and skipped. OpenRouter is attempted only when its live model catalogue lists a model ending in `:free` with zero prompt and completion prices.

The relay creates a downloadable `brain-app-relay-packet` artifact containing the full task and worker responses, and updates `brain-app/relay-status.json` with metadata only (run ID, outcome, provider/model names, and error categories). The dashboard reads that public metadata file automatically, displays per-provider results, and marks the last run stale if it is older than 24 hours. It does not fetch the private task packet or response content. The browser dashboard is **not yet fully or automatically synced** to the relay: project/task data lives in browser storage, and results remain in the workflow artifact until the user downloads and imports them. Task IDs now travel with generated relay requests and result packets, reducing manual matching mistakes, but this is not an automatic artifact download or private backend. The request-file trigger removes the need for the user to click Run workflow, but it does not yet make the browser dashboard itself automatically dispatch or sync packets.

## Privacy boundary — important

This repository is public. The file-triggered request at `brain-app/relay-request.json` is committed to the public Git history, so its `task` and `prior_packet` fields are public even though the dashboard status file excludes them. Only put generic, non-sensitive work in that file; never put personal, confidential, credential, or private business data there. The repository is public, so treat workflow artifacts and their task/response contents as potentially accessible to anyone who can read the repository or its Actions artifacts. Do not send confidential or personal tasks through this relay. A genuinely private task-to-relay bridge is not implemented yet; do not describe the current static dashboard as private or fully synced.

## Provider and quota rules
- Gemini and Groq require explicit free-tier opt-in.
- Remaining provider quotas are not exposed by this app and must not be guessed.
- No paid fallback, account rotation, public posting, or external account changes.
- API keys stay in GitHub Actions secrets, never browser files or handoff packets.
- A configured key is not proof that a provider is healthy; only a successful live call counts as verified.

## Security and next milestone
GitHub Pages is a static client, so it must never contain provider API keys or a privileged GitHub token. A true direct bridge still requires a trusted write path from the browser and a private way to store/read task content. GitHub Pages cannot safely hold a privileged GitHub token, and this public repository cannot safely store plaintext task packets or full responses. Do not solve the sync gap by committing results or embedding a token in the page. The safe current route is assistant-driven queueing of generic, non-sensitive tasks plus artifact retrieval by the assistant; dashboard task records remain browser-local. A private bridge must first establish a free hosting/authentication design and a privacy boundary before implementation.

## Supabase backend — free-tier foundation deployed
- Supabase organisation: `Astrid` (Free plan).
- Project: `brain-app`, region `ap-southeast-2` (Sydney), project ref `cjqgdqcbtcwsgbbqrqcf`.
- Live Supabase project quote was **$0/month** at creation. Project status verified as `ACTIVE_HEALTHY`.
- Applied migration `brain_app_core` from `brain-app/supabase/migrations/0001_brain_app_core.sql` and `brain_app_owner_fk_indexes` from `brain-app/supabase/migrations/0002_brain_app_owner_fk_indexes.sql`.
- Verified the four database tables exist: `brain_projects`, `brain_tasks`, `brain_worker_runs`, and `brain_task_events`. Row-level security is enabled on all four tables; the schema contains owner-scoped policies and relevant indexes. A follow-up migration adds indexes on the owner foreign keys for worker runs and task events.
- Added a first browser-side Supabase integration in `brain-app/app.js` and sign-in/sign-up controls in `brain-app/index.html` (commit `fca0646` / `257cd0a`). It uses only the public publishable key and authenticated client queries under RLS. **This code has not yet been browser-tested end-to-end**: account creation/sign-in, email-confirmation redirect settings, first sync, multi-device conflict handling and deletion propagation still need validation before calling cloud sync usable. Do not assume it is production-ready.
- No trusted server-side AI dispatcher has been deployed yet; the existing GitHub Actions relay remains a separate, transitional mechanism.
- Notion contains a private page named “Brain App — System Architecture and Build Plan” documenting the tool roles, privacy boundaries, current verified baseline and build sequence.
- Target division of responsibility: Brain App coordinates; Supabase stores operational state; Notion stores readable architecture/decisions; GitHub stores source and tests; GitHub Actions is the current transitional relay; Groq/Gemini/OpenRouter are replaceable workers.
- **Hard $0 policy:** use free resources only. Never create, enable, upgrade, or continue any resource that has a nonzero cost or could incur an unapproved charge. If a required capability is paid or the cost cannot be verified as zero, skip it and find a free alternative. Do not ask the user to approve nonzero costs.
- Next implementation: verify the cloud sync path in a real browser session, fix merge/deletion edge cases, and make the task queue's worker execution/result return path dependable. Then implement a trusted dispatcher using only verified $0 infrastructure. Never put service-role credentials in browser code or the public repository.
