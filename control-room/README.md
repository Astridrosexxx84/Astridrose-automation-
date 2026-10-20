# AI Control Room

A phone-first personal project cockpit built with static files and no paid hosting requirement.

## Working in this version
- Create and switch between projects.
- Save coordinator and worker preferences.
- Keep a project brief, completed work, decisions, and exact next action.
- Create a portable handover packet for moving work between AI conversations/providers.
- Export one project or all projects as JSON and restore from a JSON backup.
- Delete a local project.
- Cache the app shell for offline opening after the first successful load.

## Open and install
The GitHub Pages workflow deploys the contents of this folder. After a successful deployment, the expected URL is:

https://astridrosexxx84.github.io/Astridrose-automation-/

On Android, open the URL in Chrome, use the three-dot menu, then choose **Add to Home screen** or **Install app** if offered.

## Important current limits
Project content is stored in browser local storage on this device/browser. It is not synced, encrypted, or remotely backed up. Export backups regularly and do not store passwords, API keys, or sensitive data in project notes. The public static app contains no project data by itself.

AI provider calls, authenticated remote storage, cross-device sync, and automatic quota-aware handoff are **not connected yet**. Provider choices are preferences only, not a live connection status. API keys must never be put into HTML, JavaScript, or committed files.

## Cost policy
The app itself uses static files and GitHub Pages. No paid service or model route is required for the local project-memory features. Any future AI execution path must explicitly block paid model routes and preserve the checkpoint before switching providers.
