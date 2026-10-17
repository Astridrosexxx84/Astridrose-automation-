# AI Team Coordinator — setup and safeguards

## What it does

A manually triggered GitHub Actions job asks three AI roles to collaborate:
1. Gemini creates an independent strategy analysis.
2. A free model available through OpenRouter independently challenges it.
3. Gemini synthesizes both into a recommendation and report.

The report is saved as a downloadable workflow artifact. This is analysis-only: it does not publish posts, comment, schedule content, or change social accounts.

## Required setup

Add these repository Actions secrets under Settings → Secrets and variables → Actions:
- GEMINI_API_KEY: a key for a Google AI Studio project that remains on the free tier.
- OPENROUTER_API_KEY: an OpenRouter API key used only with listed zero-price models whose IDs end in :free.

Never paste keys into chat, workflow inputs, files, or commits. Do not enable billing or buy credits for this workflow. If billing is already enabled on the Google project, check its settings before running. The workflow itself does not create keys or change billing.

## How to run

After both secrets are configured, open Actions → Astrid Rose — AI team (manual, review-only) → Run workflow, enter a task, and run it manually. Open the completed run and download the astrid-rose-ai-team-report artifact.

## Free-tier and privacy safeguards

- The coordinator does not choose a paid OpenRouter model. If no qualifying free model is available, it stops.
- Gemini uses the model ID gemini-3.8-flash, listed in official pricing documentation as available on the free tier when this was prepared. Free-tier availability and quotas can change.
- Do not put sensitive personal data, passwords, access tokens, or confidential third-party information in a task. The prompt and intermediate analyses are sent to the providers.
- This code does not post to social media or mutate external accounts.
- The workflow is manual only. Do not add a schedule until cost and quota behavior has been tested.

## Expected behavior

With valid keys and available free quota, the run creates ai-team-report.md. If a key is missing, the provider fails, or no free OpenRouter model is available, it exits with an error rather than trying a paid fallback.
