# Brain App — MVP

The Brain App is the coordinator/control room. AI providers are replaceable workers that take turns using a shared handoff packet.

## Current capabilities
- Mobile-friendly project dashboard with separate projects and task queues.
- Browser-local storage and JSON backup/import.
- Portable work packets containing goal, context, current output and next action.
- GitHub Actions relay that attempts configured providers in sequence and records the combined result.
- A file-triggered relay request: updating `brain-app/relay-request.json` on `main` automatically starts the relay. ChatGPT can queue work by committing this request file through the connected GitHub integration, without a user click.
- A live dashboard status panel reads a metadata-only status file updated by the relay workflow. It shows each provider result and links to the run, without publishing prompts, task content, model responses or API keys.
- Live verification: Groq and Gemini have each completed real calls and handed work to the next provider. OpenRouter was rate-limited (HTTP 429) in the latest verified run.

## Open the dashboard
https://astridrosexxx84.github.io/Astridrose-automation-/brain-app/

## Run the sequential relay
There are two routes:
1. **Assistant-driven:** update `brain-app/relay-request.json` on `main`. That commit triggers the workflow automatically.
2. **Manual fallback:** open the [Brain App relay workflow](https://github.com/Astridrosexxx84/Astridrose-automation-/actions/workflows/brain-app-relay.yml), choose **Run workflow**, and enter a goal.

The chain order is Groq → Gemini → OpenRouter. Each successful worker passes its packet to the next; failures are recorded and skipped. OpenRouter is attempted only when its live model catalogue lists a model ending in `:free` with zero prompt and completion prices.

The relay creates a downloadable `brain-app-relay-packet` artifact and updates `.github/brain-relay-status.json` with metadata only (run ID, outcome, provider/model names, and error categories). The dashboard reads that public metadata file automatically; it does not fetch the private task packet or response content. The browser dashboard is **not yet directly synced** to the relay: project/task data lives in browser storage, and results currently remain in the workflow artifact until imported or otherwise handed back. The request-file trigger removes the need for the user to click Run workflow, but it does not yet make the browser dashboard itself automatically dispatch or sync packets.

## Provider and quota rules
- Gemini and Groq require explicit free-tier opt-in.
- Remaining provider quotas are not exposed by this app and must not be guessed.
- No paid fallback, account rotation, public posting, or external account changes.
- API keys stay in GitHub Actions secrets, never browser files or handoff packets.
- A configured key is not proof that a provider is healthy; only a successful live call counts as verified.

## Security and next milestone
GitHub Pages is a static client, so it must never contain provider API keys or a privileged GitHub token. The next milestone is a secure, free-first bridge between browser task records and Actions relay packets, with durable result import and honest run status. Until that exists, use the dashboard for planning and portable packets, and let the assistant queue relay work through the request file.
