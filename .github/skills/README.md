# Project Skills

This repository uses project-local skills as the operational layer beneath the team roles.

## Purpose
- Roles define authority, responsibility, boundaries, and required outputs.
- Skills define repeatable execution patterns for recurring work.

## Primary Project Skills
- `coordinator-flow`
- `requirements-clarification`
- `architecture-design`
- `implementation-clean-code`
- `code-review`
- `unit-testing`
- `acceptance-testing`
- `memory-update`

## Reusable OpenAI Skills
These are useful when installed and available in Codex:
- `openai-docs`: use for official OpenAI or model/platform guidance.
- `playwright`: use for browser-based acceptance or end-to-end testing when the stack supports it.
- `security-best-practices`: use when a feature has meaningful security impact.
- `security-threat-model`: use when a feature changes trust boundaries, inputs, or access patterns.
- `doc`: use for documentation-heavy tasks when a general documentation helper is useful.

## Usage Rule
- Use the role file to decide who owns the work.
- Use the matching skill to decide how to perform the work.
- Prefer project-local skills for team-specific flow and artifacts.
- Prefer reusable external skills for general-purpose capability when they fit cleanly.
