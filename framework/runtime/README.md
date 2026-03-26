# Runtime Orchestration

This folder defines the Codex-first runtime orchestration model for this repository.

## Purpose
- The repository files define the team and workflow.
- The coordinator uses native Codex subagent spawning to execute the workflow.
- These files provide the machine-readable and template-backed runtime contract.

## Files
- `team.yaml`: role registry, ownership, and default subagent model.
- `workflow.yaml`: phase state machine, exit rules, rollback rules, and required artifacts.
- `task-template.md`: standard task payload for spawned specialist subagents.
- `review-template.md`: standard findings format for reviewer output.
- `state.json`: machine-readable runtime state snapshot.

## Codex-First Rule
- The coordinator is the only top-level user-facing agent.
- The coordinator should use native subagent spawning for specialist work when the task is bounded.
- Each spawned specialist gets one role, one bounded objective, explicit artifact ownership, and explicit completion criteria.
