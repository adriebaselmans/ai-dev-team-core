---
name: memory-update
description: Update the project memory after each completed phase using the repository's project-log, decisions, and known-context conventions.
---

# Memory Update

Use this skill when acting as the coordinator and a phase has been completed.

## Goals
- Preserve useful project knowledge for future iterations.
- Keep durable memory structured and retrievable.
- Avoid duplicating active shared state or phase artifacts.

## Required Inputs
- Reusable knowledge produced by the current run
- Bootstrapped project metadata in `.ai-team/framework/init-metadata.json`
- Existing structured memory in `.ai-team/framework/memory/records/`

## Required Outputs
- Updated structured records in `.ai-team/framework/memory/records/`
- Optional human-readable exports only when explicitly requested

## Rules
- Structured records are the source of truth for project memory.
- Use bounded record kinds such as facts, decisions, questions, contradictions, and phase briefs.
- Keep durable entries short, factual, reusable, and cross-run valuable.
- Write structured memory only in bootstrapped project repos created from this skeleton.
- Do not copy current-run orchestration state, trace, or phase artifacts into memory.
- Generate markdown snapshots only as explicit exports, not as the normal phase-update path.
