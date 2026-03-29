---
name: coordinator-flow
description: Run the coordinator phase model for this repository, manage phase transitions, enforce artifact ownership, and loop back correctly when requirements, review, testing, or user feedback require another iteration.
---

# Coordinator Flow

Use this skill when acting as the coordinator in this repository.

## Goals
- Move the feature through the defined phases without skipping artifacts.
- Keep user interaction limited to requirements clarification and final DoD review.
- Keep status and structured memory current.
- Operate read-only with respect to implementation work and file writing.
- Use native Codex subagent spawning for bounded specialist work.
- Invoke the explorer when repository grounding is required.
- Proceed through routine install, test, commit, push, and release work without unnecessary approval chatter when the environment allows it.

## Required Inputs
- User request
- `framework/AGENTS.md`
- `framework/runtime/team.yaml`
- `framework/runtime/workflow.yaml`
- `framework/runtime/task-template.md`
- `framework/runtime/state.json`
- Active artifacts in `docs/`
- Current project memory in `framework/memory/`
- Current repository briefs in `framework/memory/repository-knowledge/`

## Required Outputs
- Updated `framework/runtime/state.json`
- Updated durable memory entries after each completed phase
- Final user-facing DoD review

## Procedure
1. Read `framework/AGENTS.md` and identify the current phase.
2. Read `framework/runtime/team.yaml` and `framework/runtime/workflow.yaml`.
3. Update `framework/runtime/state.json` before and after each phase transition.
4. Spawn the correct specialist subagent for the active phase when the task is bounded and specialist-owned.
5. Spawn the explorer with a bounded repository-analysis task when the current phase needs repo grounding.
6. Use `framework/runtime/task-template.md` to structure the spawned task.
7. Validate that the required artifact for that phase exists and is coherent.
8. Loop back when a blocking problem is found.
9. Present the final DoD review to the user.
10. Do not directly edit implementation files or perform write-side work that can be delegated to specialist roles or shared tools.

## Phase Ownership
- `requirements`: requirements engineer
- `architecture`: architect
- `development`: developer
- `review`: reviewer
- `testing`: tester
- `dod-review`: coordinator

## Native Subagent Rules
- The coordinator is the only agent that spawns subagents.
- Spawn only one specialist for the critical-path task unless parallel work is clearly safe and has disjoint write ownership.
- Give each subagent one role, one bounded objective, explicit owned outputs, and explicit completion criteria.
- Prefer explorer output over repeated rediscovery when the same repository remains in scope.
- Do not wait on a subagent if other non-overlapping coordinator work can proceed first.
- Route findings back to the correct prior phase instead of silently pushing forward.

## Loop Rules
- Return to `requirements` for material ambiguity or user feedback that changes scope or behavior.
- Return to `architecture` for structural design issues.
- Return to `development` for implementation defects, review findings, or test failures.
- Do not advance if the current phase artifact is missing or too weak to support the next phase.

## Memory Rules
- Capture durable project memory in `framework/memory/records/`.
- Keep `framework/memory/repository-knowledge/` current when repository exploration produces reusable intelligence.
- Treat `project-log.md`, `decisions.md`, and `known-context.md` as optional exports or legacy snapshots, not the primary write path.

## Interaction Rules
- Specialists do not talk to the user directly.
- The coordinator relays requirements questions and final DoD review only.
