# Desk Deck Agent Instructions

## Agent Status Light

When working in this repository, use the local Desk Deck status scripts when the companion server is available.

- Before starting substantial implementation, validation, or repo inspection work:
  ```powershell
  .\scripts\agent-working.ps1
  ```
- Before asking the user for a decision, clarification, or blocker resolution:
  ```powershell
  .\scripts\agent-waiting.ps1
  ```
- After completing the requested work and validation, before the final response:
  ```powershell
  .\scripts\agent-done.ps1
  ```
- To clear the agent override and return to normal status selection:
  ```powershell
  .\scripts\agent-reset.ps1
  ```

Do not spam status changes for tiny one-message answers. If the companion server is unavailable, continue the task; the scripts are designed to warn without blocking work.

## Project Process

- Keep `status.md` updated for meaningful milestones and validation results.
- Do not commit local secrets, virtual environments, build outputs, or generated logs.
- Prefer small, validated milestones and push after a milestone is complete.
