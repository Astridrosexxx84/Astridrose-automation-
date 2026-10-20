# Brain App — MVP

The Brain App is intended to be the coordinator/control room. AI providers are replaceable workers that take turns using a shared handoff packet.

## Current capabilities
- Mobile-friendly project dashboard with separate projects and task queues.
- Browser-local storage and JSON backup/import.
- Portable work packets containing goal, context, current output and next action.
- GitHub Actions relay that attempts configured providers in sequence and records the combined result.

## Open the dashboard
https://astridrosexxx84.github.io/Astridrose-automation-/brain-app/

## Run the sequential relay
Open the [Brain App relay workflow](https://github.com/Astridrosexxx84/Astridrose-automation-/actions/workflows/brain-app-relay.yml), choose **Run workflow**, leave provider set to **auto**, and enter the goal. The chain attempts OpenRouter, Groq, and Gemini in sequence, passing the last successful packet forward and recording failures without treating them as successful work.

The relay creates a downloadable `brain-app-relay-packet` artifact. The dashboard is **not yet directly connected** to this workflow: project/task data currently lives in the browser, and the user must launch the workflow and retrieve its artifact separately. Do not claim that the dashboard automatically dispatches jobs or syncs packets.

## Provider and quota rules
- OpenRouter is attempted only when its live model catalogue lists a model ending in `:free` with zero prompt and completion prices.
- Gemini and Groq require explicit free-tier opt-in. Their remaining quotas are not exposed by this app and must not be guessed.
- No paid fallback, account rotation, public posting, or external account changes.
- API keys stay in GitHub Actions secrets, never browser files or handoff packets.
- A configured key is not proof that a provider is healthy; only a successful live call counts as verified.

## Security and next milestone
GitHub Pages is a static client, so it must never contain provider API keys or a privileged GitHub token. The next architectural milestone is a secure, free-first bridge between task records and the Actions relay, with explicit permissions, durable packet storage, and honest run status. Until that exists, use the dashboard for planning and portable packets, and GitHub Actions for the provider relay.
