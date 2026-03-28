# AI Dev Team Framework

This file defines the canonical team workflow for this repository.

## Goal
Take a user need or feature description and deliver an end-to-end implementation with minimal human intervention.

## Team Roles
- Coordinator: owns intake, delegation, phase transitions, integration, and final reporting.
- Requirements Engineer: clarifies the request and writes the requirement baseline.
- Architect: writes the design approach and technical constraints.
- Developer: implements the solution in `src/`.
- Reviewer: reviews the implementation for quality and technical risk before testing.
- Tester: validates the implementation against the requirement baseline and prepares the DoD review.
- Repository exploration support: shared grounding capability used when repo context is needed.

Detailed role instructions live in `framework/roles/`.
Role-to-skill mapping lives in `framework/skills.md`.
Runtime specs live in `framework/runtime/`.

## Skills
- Project-local skills live in `.github/skills/`.
- Roles define ownership and boundaries.
- Skills define repeatable execution patterns.
- Prefer project-local skills for this repository's workflow and artifacts.
- Use reusable external skills when they are available and fit cleanly.
- Repository exploration is a shared support capability with its own skill contract, not a standalone active team role.

## Runtime Orchestration
- This repository is moving to a model-agnostic runtime orchestration layer.
- The coordinator should use bounded specialist dispatch for specialist work.
- `framework/runtime/team.yaml` defines role registry and spawn rules.
- `framework/runtime/workflow.yaml` defines the state machine and rollback rules.
- `framework/runtime/task-template.md` defines the standard subagent task payload.
- `framework/runtime/review-template.md` defines the standard reviewer output shape.
- `framework/memory/repository-knowledge/` defines the durable store for analyzed repository knowledge.
- `framework/runtime/state.json` is the placeholder runtime state snapshot.

## Coordinator Runbook
The coordinator owns the full feature flow and moves the team through these phases:
- `idle`
- `requirements`
- `architecture`
- `development`
- `review`
- `testing`
- `dod-review`
- `done`

## Phase Flow
### 1. Idle
Entry condition:
- No active feature is currently being worked on.

Coordinator actions:
- Receive the user need.
- Start a new iteration from the requirements phase.
- Decide whether repository exploration is required before or during the phase flow.

Exit condition:
- A concrete user need is available.

### 2. Requirements
Entry condition:
- A user need exists but is not yet confirmed as implementation-ready.

Coordinator actions:
- Delegate to the requirements engineer.
- Use repository exploration support first when the request must be grounded in a specific repository and the baseline cannot be written safely without that context.
- Relay clarification questions to the user only when needed.
- Update `doc_templates/requirements/current.yaml` until it is clear enough to proceed.
- Update memory when the phase is completed.

Exit condition:
- `doc_templates/requirements/current.yaml` is complete enough for autonomous architecture and implementation.
- `Definition of Ready` in the requirements file is effectively `ready`.

Loop rule:
- Stay in this phase until blocking ambiguity is removed.

### 3. Architecture
Entry condition:
- Requirements are ready.

Coordinator actions:
- Delegate to the architect.
- Use repository exploration support when the design depends on an existing repository's architecture, conventions, or extension points.
- Ensure `doc_templates/design/current.yaml` is updated.
- Ensure the design reflects clean code, stack-appropriate best practices, and relevant performance tradeoffs.
- Update memory when the phase is completed.

Exit condition:
- The design is implementation-safe.
- The developer can proceed without guessing key structure or technical direction.

Loop rule:
- Return to requirements if the architect finds unresolved functional ambiguity or infeasibility.

### 4. Development
Entry condition:
- Requirements and design are both ready.

Coordinator actions:
- Delegate implementation to the developer.
- Delegate to repository exploration support when the developer needs grounded understanding of a target repository before making or proposing changes.
- Ensure code is written in `src/`.
- Ensure unit tests are added for relevant new or changed behavior.
- Update memory when the phase is completed.

Exit condition:
- The intended implementation is present.
- Relevant unit tests are present.
- The result is ready for validation.

Loop rule:
- Return to architecture if implementation reveals a structural design problem.
- Return to requirements if implementation reveals a material scope or behavior ambiguity.

### 5. Review
Entry condition:
- Implementation is complete enough for technical review.

Coordinator actions:
- Delegate review to the reviewer.
- Use repository exploration support when review findings depend on understanding upstream repository architecture or conventions.
- Ensure the implementation is checked against requirements, design, and `framework/clean-code.md`.
- Ensure linting issues and actionable warnings are resolved where practical before testing proceeds.
- Update memory when the phase is completed.

Exit condition:
- The reviewer has issued a clear review decision.
- Blocking findings are resolved or explicitly returned for rework.

Loop rule:
- Return to development if review findings require code or test changes.
- Return to architecture if review reveals a structural or design problem.

### 6. Testing
Entry condition:
- Review is complete and the change is approved for testing.

Coordinator actions:
- Delegate validation to the tester.
- Ensure `doc_templates/dod/current.yaml` is updated.
- Ensure an automated acceptance or end-to-end regression suite is added when feasible and worthwhile.
- Ensure the tester records how that regression suite should be rerun later.
- Update memory when the phase is completed.

Exit condition:
- The tester has issued a clear DoD decision.
- A rerunnable automated acceptance or end-to-end suite exists, or `doc_templates/dod/current.yaml` explicitly explains why it was not feasible.

Loop rule:
- Return to development if defects or coverage gaps must be fixed.
- Return to architecture or requirements if the defect shows a deeper upstream problem.

### 7. DoD Review
Entry condition:
- The tester has produced `doc_templates/dod/current.yaml`.

Coordinator actions:
- Present the DoD review to the user.
- Ask for approval or feedback.

Exit condition:
- The user approves, or provides feedback for another iteration.

Loop rule:
- If the user approves, move to `done`.
- If the user provides feedback, start a new iteration from `requirements` and preserve all relevant memory.

### 8. Done
Entry condition:
- The user has approved the delivered result.

Coordinator actions:
- Leave the current artifacts as the latest accepted baseline.
- Ensure memory reflects the accepted state.

Exit condition:
- The team returns to `idle` when a new user need arrives.

## Non-Negotiable Rules
- Do not ask the user for approval between architecture, development, and testing once the requirements are clear.
- Use repository exploration support only when repository grounding is required by the user request or by a blocking knowledge gap in another role.
- Treat repository exploration as a shared support capability, not a standalone role.
- Treat local build, test, and app run actions as implicitly approved within the team workflow.
- Treat routine dependency install, commit, tag, push, and release actions as implicitly approved within the team workflow when they are part of completing the requested work.
- When the execution environment still requires a tool-level elevation prompt for a build, test, or run action, request it directly without stopping for an extra conversational approval round.
- When the execution environment still requires a tool-level elevation prompt for install, commit, tag, push, or release actions, request it directly without stopping for an extra conversational approval round.
- Do not skip the review phase before testing.
- Do not treat automated acceptance coverage as optional when the feature can support a stable regression suite.
- Keep durable project knowledge in `framework/memory/`.
- Keep durable repository-specific knowledge in `framework/memory/repository-knowledge/`.
- Use the compaction skill to produce dense phase-boundary briefs when a phase completes.
- Keep the latest requirements in `doc_templates/requirements/current.yaml`.
- Keep the latest design in `doc_templates/design/current.yaml`.
- Keep the latest review in `doc_templates/review/current.yaml`.
- Keep the latest DoD review in `doc_templates/dod/current.yaml`.
- Keep implementation in `src/`.
- Follow the engineering standards in `framework/clean-code.md`.
- Use the role-aligned skills in `.github/skills/` and `framework/skills.md` where applicable.
- Use `framework/runtime/` as the machine-readable contract for native subagent orchestration.
- The coordinator is responsible for updating `framework/runtime/state.json`.
- The coordinator is responsible for updating `framework/memory/` after each completed phase.
- Specialists do not communicate with the user directly; the coordinator owns all user-facing interaction.
- Return to the user only during requirements clarification and final DoD review.
- Do not silently skip a phase artifact.

## Memory Policy
Update memory at the end of each completed phase.

Required memory files:
- `framework/memory/project-log.md`: chronological log of what was built.
- `framework/memory/decisions.md`: important decisions and why they were made.
- `framework/memory/known-context.md`: stable context, conventions, and assumptions.
- `framework/memory/repository-knowledge/`: compact repository briefs, machine-readable metadata, and an index for analyzed repositories.

Memory update rules:
- `project-log.md` records what changed in chronological order.
- `decisions.md` records meaningful project decisions, their context, and consequences.
- `known-context.md` records stable truths that future agents should treat as current baseline context.
- `repository-knowledge/` records reusable repository intelligence that other roles can consult instead of rescanning the same repo.
- Each entry should be short, factual, and useful for future agents.
- The coordinator updates memory after each completed phase, not only at the end of the full feature flow.

## Final Review
The tester must prepare a Definition of Done result that covers:
- What was built
- What was verified
- What automated regression command or suite should be run later
- Any known gaps or risks
- What feedback is needed from the user

The coordinator uses that result for the final response.
