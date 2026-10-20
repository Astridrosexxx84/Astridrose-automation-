# Brain App — MVP

The Brain App is the coordinator/control room. AI providers are replaceable workers that take turns using a shared handoff packet.

## Current capabilities
- Mobile-friendly project dashboard with separate projects and task queues.
- Browser-local storage and JSON backup/import.
- Portable work packets containing goal, context, current output and next action.
- Import relay result: load `brain-relay-packet.json` from a downloaded relay artifact to append provider outputs and the next action to the selected local task.
- GitHub Actions relay that attempts configured providers in sequence and records the combined result.
- A file-triggered relay request: updating `brain-app/relay-request.json` on `main` automatically starts the relay. ChatGPT can queue work by committing this request file through the connected GitHub integration, without a user click.
- A live dashboard status panel reads a metadata-only status file updated by the relay workflow. It shows each provider result and links to the run, without publishing prompts, task content, model responses or API keys.
- Latest live relay reviewed: Groq and Gemini succeeded; OpenRouter returned HTTP 429 (2/3). The chain now labels this `partial` rather than `success`; the dashboard also presents partial completion separately. Earlier 3/3 runs are historical, not proof that every current run succeeds.

## Open the dashboard
https://astridrosexxx84.github.io/Astridrose-automation-/brain-app/

## Run the sequential relay
There are two routes:
1. **Assistant-driven:** update `brain-app/relay-request.json` on `main`. That commit triggers the workflow automatically.
2. **Manual fallback:** open the [Brain App relay workflow](https://github.com/Astridrosexxx84/Astridrose-automation-/actions/workflows/brain-app-relay.yml), choose **Run workflow**, and enter a goal.

The chain order is Groq → Gemini → OpenRouter. Each successful worker passes its packet to the next; failures are recorded and skipped. OpenRouter is attempted only when its live model catalogue lists a model ending in `:free` with zero prompt and completion prices.

The relay creates a downloadable `brain-app-relay-packet` artifact containing the full task and worker responses, and updates `brain-app/relay-status.json` with metadata only (run ID, outcome, provider/model names, and error categories). The dashboard reads that public metadata file automatically, displays per-provider results, and marks the last run stale if it is older than 24 hours. It does not fetch the private task packet or response content. The browser dashboard is **not yet directly synced** to the relay: project/task data lives in browser storage, and results currently remain in the workflow artifact until imported or otherwise handed back. The request-file trigger removes the need for the user to click Run workflow, but it does not yet make the browser dashboard itself automatically dispatch or sync packets.

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
