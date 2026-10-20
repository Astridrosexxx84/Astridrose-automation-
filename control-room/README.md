# AI Control Room prototype

Open `index.html` to preview the phone-first UI. It stores projects and handover checkpoints in this browser's local storage and can export a JSON backup. It does not call AI providers yet and is not a connected application. API keys must never be entered here.

## Current scope
- Create and switch between local projects
- Choose preferred coordinator and two workers
- Save brief, completed work, next action, and decisions as a checkpoint
- Export a project checkpoint backup
- Show a free-provider setup checklist

## Next
1. Connect to a small backend using the existing coordinator and provider adapters.
2. Persist checkpoints before each model handoff.
3. Normalize rate-limit and quota errors, then automatically resume with another eligible free provider.
4. Add secure authentication / private access before remote hosting.
5. Test simulated quota exhaustion end-to-end.

This is a prototype; browser-local data can be lost if site data is cleared. Export backups.
