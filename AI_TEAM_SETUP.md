# AI Team Coordinator — setup and safeguards

## What it does

A manually triggered GitHub Actions job asks whichever configured AI providers are available to contribute. Gemini and Groq can provide independent analysis; OpenRouter can provide independent analysis and final synthesis using a listed zero-price free model. If no eligible synthesis route is available, the coordinator preserves partial work in a deterministic report.

The report is saved as a downloadable workflow artifact. This is analysis-only: it does not publish posts, comment, schedule content, or change social accounts.

## Setup: providers are optional

Add any provider secrets you have configured under Settings → Secrets and variables → Actions:
- GEMINI_API_KEY: Google AI Studio API key; verify the project is on a genuinely free tier before use.
- GROQ_API_KEY: GroqCloud API key; use only within the account's free allowance and keep paid billing disabled.
- OPENROUTER_API_KEY: OpenRouter API key; the coordinator only uses models listed with a `:free` ID and zero prompt/completion prices.

You do not need all three. The workflow skips providers without keys and continues with configured providers; at least one provider key must exist for an AI run. OpenRouter is the only currently eligible final-synthesis route because its zero-price model is checked at runtime. If no eligible synthesis route is available, the coordinator writes a deterministic report preserving partial analyses. Never paste keys into chat, workflow inputs, files, or commits. Do not enable billing or buy credits.

## How to run

After at least one provider secret is configured, open Actions → Astrid Rose — AI team (manual, review-only) → Run workflow, enter a task, and run it manually. Open the completed run and download the astrid-rose-ai-team-report artifact.

## Free-tier and privacy safeguards

- The coordinator does not choose a paid OpenRouter model. If no qualifying free model is available, it skips AI synthesis and preserves partial work in a deterministic report.
- Groq's available models and rate limits depend on the account; keep billing disabled and do not proceed if the console says paid usage is required.
- Gemini uses the model ID gemini-3.8-flash, listed in official pricing documentation as available on the free tier when this was prepared. Free-tier availability and quotas can change.
- Do not put sensitive personal data, passwords, access tokens, or confidential third-party information in a task. The prompt and intermediate analyses are sent to the providers.
- This code does not post to social media or mutate external accounts.
- The workflow is manual only. Do not add a schedule until cost and quota behavior has been tested.

## Expected behavior

With at least one valid key and available free quota, the run creates ai-team-report.md. A missing key skips only that provider. If no key is configured, the run stops; if no free OpenRouter model is available, it does not try a paid model.
