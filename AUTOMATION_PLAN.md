# Free-first automation plan

## Goal
Build a highly automated income stream with $0 upfront. Income is not guaranteed; validate demand before scaling.

## Current foundation
- GitHub Actions runs the existing Bluesky workflow.
- Reddit posting remains disabled unless authorized API access is configured and the workflow is manually triggered.
- Keep all credentials in GitHub repository secrets, never in source code or chat.

## Build order
1. Keep the existing Bluesky bot stable and low-frequency.
2. Add a content library and a lightweight metrics log in this repository.
3. Test one audience hypothesis and one monetization offer at a time.
4. Automate drafts, scheduling, link tracking, and reporting after the manual process proves useful.
5. Add a storefront only after selecting an offer and checking current platform fees and policies.

## Monetization hypotheses
- Creator subscriptions: recurring revenue potential, but ongoing content and audience care are required.
- Digital downloads/templates: potentially more reusable after creation, but discovery and customer support remain.
- Affiliate content: low inventory burden, but requires traffic and clear disclosures.
- Automation templates: more upfront building, potentially repeatable sales if a real need is validated.

## Free-first infrastructure
Use GitHub Actions first because it already exists. Add another coordinator only when it removes a demonstrated bottleneck. Free tiers and quotas can change; never make the business depend on a quota without a fallback.

## Reddit constraints
The current external Reddit script requires valid OAuth credentials. Do not bypass Reddit access requirements or automate spam, repetitive comments, unsolicited DMs, or rule-breaking promotion. Revisit Reddit only through an official supported route.

## Success measures
Track posts, link clicks, sign-ups, sales, costs, and time spent. Prioritize evidence of demand over follower counts. Reinvest only after revenue is real.
