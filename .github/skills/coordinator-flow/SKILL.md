---
name: coordinator-flow
description: Run the coordinator phase model for this repository, manage phase transitions, enforce artifact ownership, and loop back correctly when requirements, review, testing, or user feedback require another iteration.
---

# Coordinator Flow

Use this skill when acting as the coordinator in this repository.

## Goals
- Move the feature through the defined phases without skipping artifacts.
- Keep user interaction limited to requirements clarification and final DoD review.
- Keep status and memory current.

## Required Inputs
- User request
- `framework/AGENTS.md`
- `framework/flows/current-status.md`
- Active artifacts in `docs/`
- Current project memory in `framework/memory/`

## Required Outputs
- Updated `framework/flows/current-status.md`
- Updated `framework/memory/` entries after each completed phase
- Final user-facing DoD review

## Procedure
1. Read `framework/AGENTS.md` and identify the current phase.
2. Update `framework/flows/current-status.md` before and after each phase transition.
3. Delegate to the correct role for the active phase.
4. Check that the required artifact for that phase exists and is coherent.
5. Loop back when a blocking problem is found.
6. Present the final DoD review to the user.

## Phase Ownership
- `requirements`: requirements engineer
- `architecture`: architect
- `development`: developer
- `review`: reviewer
- `testing`: tester
- `dod-review`: coordinator

## Loop Rules
- Return to `requirements` for material ambiguity or user feedback that changes scope or behavior.
- Return to `architecture` for structural design issues.
- Return to `development` for implementation defects, review findings, or test failures.
- Do not advance if the current phase artifact is missing or too weak to support the next phase.

## Memory Rules
- Update `project-log.md` with what changed and why.
- Update `decisions.md` when a meaningful decision was made or changed.
- Update `known-context.md` only for stable truths that should persist across iterations.

## Interaction Rules
- Specialists do not talk to the user directly.
- The coordinator relays requirements questions and final DoD review only.
