---
name: memory-update
description: Update the project memory after each completed phase using the repository's project-log, decisions, and known-context conventions.
---

# Memory Update

Use this skill when acting as the coordinator and a phase has been completed.

## Goals
- Preserve useful project knowledge for future iterations.
- Keep durable memory structured and retrievable.

## Required Inputs
- Phase outcome
- Active artifacts in `docs/`
- Existing structured memory in `framework/memory/records/`

## Required Outputs
- Updated structured records in `framework/memory/records/`
- Optional human-readable exports only when explicitly requested

## Rules
- Structured records are the source of truth for project memory.
- Use bounded record kinds such as facts, decisions, questions, contradictions, and phase briefs.
- Keep durable entries short, factual, and useful.
- Generate markdown snapshots only as explicit exports, not as the normal phase-update path.
