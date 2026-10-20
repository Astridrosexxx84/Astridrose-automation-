# Brain App — MVP

The Brain App is the coordinator. AI providers are replaceable workers that take turns using a shared handoff packet.

## What exists
- Mobile-friendly project dashboard with separate projects and task queues.
- Browser-local storage and JSON backup/import.
- Work packets containing goal, context, current output and next action.
- GitHub Actions workflow that runs one AI worker per turn and saves a packet artifact.

## Open the dashboard
https://astridrosexxx84.github.io/Astridrose-automation-/brain-app/

## Run one AI worker turn
1. Open the repository's Actions tab.
2. Choose **Brain App — One Worker Relay Turn**, then **Run workflow**.
3. Enter the task, choose a provider, and select create, continue or review.
4. Download the `brain-app-relay-packet` artifact after the run.
5. For the next turn, run the workflow again and paste the previous packet into `prior_packet`.

This first relay uses manual handoff between runs. Automatic chaining and shared cloud storage are future milestones.

## Free-first and security rules
- OpenRouter is only attempted when its live catalogue lists a model ending in `:free` with zero prompt and completion prices.
- Gemini and Groq require explicit free-tier opt-in; their free quotas are limited and remaining quota is not guessed.
- No paid fallback, account rotation, public posting or external account changes.
- API keys stay in GitHub Actions secrets, never browser files or handoff packets.
- ChatGPT consumer sessions are not automatically connected as API workers. For now, copy the packet into ChatGPT manually, have it continue the artifact, and paste its output into the next worker turn.

## Next
1. Run and verify one worker turn with a configured provider.
2. Improve durable packet storage and automate safe handoffs.
3. Connect the dashboard to a secure backend without exposing secrets in browser code.
