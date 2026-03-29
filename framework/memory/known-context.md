# Known Context

Legacy or exported readable context summary derived from structured memory when needed.

## Rules
- Treat this file as optional readable output, not the canonical write path.
- Keep this file concise.
- Store only context that is expected to remain true across multiple iterations.
- Move time-bound change history to `project-log.md`.
- Move rationale for important choices to `decisions.md`.

## Current Baseline
- The memory subsystem is local-first, structured, and deterministic.
- `framework/memory/` is the durable project memory root, and `framework/memory/repository-knowledge/` remains a separate namespace for analyzed repositories.
- Structured memory records under `framework/memory/records/` are the durable source of truth for project memory.
- Markdown memory files, when present, are optional exports or legacy snapshots.
- Role context slices can consume scoped memory bundles through the runtime contract.
- Role memory bundles are defined as named recipes in `framework/runtime/context_slices.yaml`.
