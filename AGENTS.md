# Desk Deck Agent Instructions

## Agent Status Light

Global Codex hooks in `C:\Users\Austin\.codex\hooks.json` now report `WORKING` at the start of every Codex request and `DONE` at the end, including work in other repositories.

Do not invoke the local lifecycle scripts as part of ordinary Codex work; keep them for manual testing and direct user control. The global hooks are best-effort, so Codex work continues normally when the companion is unavailable.

## Project Process

- Do not commit local secrets, virtual environments, build outputs, or generated logs.
- Prefer small, validated milestones and push after a milestone is complete.
