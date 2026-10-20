# Brain App — MVP

The Brain App is the coordinator. AI providers are replaceable workers that take turns on a shared task packet; they are not expected to answer the same prompt in parallel.

## Current MVP
- Phone-friendly project dashboard.
- Separate projects and task queues.
- Sequential handoff packet with goal, context, constraints, current output and next action.
- Local browser persistence plus JSON export/import for backup and transfer.
- Explicit provider integration status: no provider is falsely shown as connected.

## Run it
Open `index.html` in a browser, or publish the `brain-app/` folder with GitHub Pages. On the existing Pages site, try:

`https://astridrosexxx84.github.io/Astridrose-automation/brain-app/`

## Honest limits
This first version stores data in the current browser on the current device. Export a JSON backup to transfer it elsewhere. It does not yet call AI APIs, run workers automatically, or connect the ChatGPT consumer app. Provider keys must never be placed in browser code. The next milestone is a secret-backed worker runner and verified free-provider failover, then the relay test (worker A creates, worker B continues, worker C reviews).

## $0-first rules
- Use only routes verified to be free before dispatch.
- Keep provider secrets in GitHub Actions secrets or another secure server-side secret store, never in this static app.
- Record only observed provider status; do not invent quota percentages.
- Respect provider rate limits; do not rotate accounts or evade quotas.
- If no verified free route is available, stop and explain the blocker.
