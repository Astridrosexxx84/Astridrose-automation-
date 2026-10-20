# AI Team Coordinator — setup and safeguards

## What it does

A GitHub Actions job asks configured AI providers to contribute independently. Gemini and Groq provide analysis when their explicit free-tier opt-in flags are enabled; OpenRouter provides independent analysis and final synthesis using a model whose live catalogue entry has a `:free` ID and zero prompt/completion prices. If one provider fails, the others continue. If no eligible synthesis route is available, the coordinator preserves partial work in a deterministic report.

The report is saved as a downloadable workflow artifact. This is analysis-only: it does not publish posts, comment, schedule content, or change social accounts.

## Setup: providers are optional

Add provider secrets under Settings → Secrets and variables → Actions only if you already have them:
- `GEMINI_API_KEY`: Google AI Studio API key.
- `GROQ_API_KEY`: GroqCloud API key.
- `OPENROUTER_API_KEY`: OpenRouter API key; calls are limited to models listed with a `:free` ID and zero prompt/completion prices.

**Safety default:** Gemini and Groq generation calls are disabled unless the corresponding repository Actions variable `ALLOW_GEMINI_FREE_TIER_CALLS` or `ALLOW_GROQ_FREE_TIER_CALLS` is explicitly set to `true`. Only set a flag after confirming that the account route is genuinely free and billing is disabled. This flag is an acknowledgement, not a technical guarantee of zero cost. OpenRouter is separately checked against its live zero-price model listing, but availability/quota can still vary. Never paste keys into chat, workflow inputs, files, or commits. Do not enable billing or buy credits.

## How to run

Open Actions → Astrid Rose — AI team (manual, review-only) → Run workflow, enter a task, and run it manually. Open the completed run and download the `astrid-rose-ai-team-report` artifact. A successful multi-provider run was verified on 20 October 2026; it recorded contributions from Gemini, Groq, and OpenRouter and completed synthesis with a runtime-verified zero-price OpenRouter model. The current fallback task is aligned with the existing trend-led video/content pipeline.

## Free-tier and privacy safeguards

- The coordinator does not choose a paid OpenRouter model. If no qualifying free model is available, it skips AI synthesis and preserves partial work in a deterministic report.
- Gemini and Groq are off by default. Their opt-in flags do not independently verify pricing; they must only be enabled after the account holder confirms free-only access and disabled billing.
- Do not put sensitive personal data, passwords, access tokens, or confidential third-party information in a task. The prompt and intermediate analyses are sent to the providers.
- This code does not post to social media or mutate external accounts.
- The workflow is manual only. Do not add a schedule until cost and quota behavior has been tested.

## Expected behavior

With at least one enabled route and available free quota, the run creates `ai-team-report.md`. Missing keys skip that provider. If no provider route is usable, the coordinator can still write a deterministic report without external AI calls. If no free OpenRouter model is available, it does not try a paid model.
