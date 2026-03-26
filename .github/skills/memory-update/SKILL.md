---
name: memory-update
description: Update the project memory after each completed phase using the repository's project-log, decisions, and known-context conventions.
---

# Memory Update

Use this skill when acting as the coordinator and a phase has been completed.

## Goals
- Preserve useful project knowledge for future iterations.
- Keep change history, decisions, and stable truths separated.

## Required Inputs
- Phase outcome
- Active artifacts in `docs/`
- Existing memory files in `framework/memory/`

## Required Outputs
- Updated `framework/memory/project-log.md`
- Updated `framework/memory/decisions.md` when needed
- Updated `framework/memory/known-context.md` when needed

## Rules
- `project-log.md` gets factual chronological updates.
- `decisions.md` gets only meaningful decisions with rationale and consequence.
- `known-context.md` gets only stable truths that should persist.
- Keep entries short and useful.
