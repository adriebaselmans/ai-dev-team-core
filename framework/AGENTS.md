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

Detailed role instructions live in `framework/roles/`.
Role-to-skill mapping lives in `framework/skills.md`.

## Skills
- Project-local skills live in `.github/skills/`.
- Roles define ownership and boundaries.
- Skills define repeatable execution patterns.
- Prefer project-local skills for this repository's workflow and artifacts.
- Use reusable external skills when they are available and fit cleanly.

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

Update `framework/flows/current-status.md` at each phase transition.

## Phase Flow
### 1. Idle
Entry condition:
- No active feature is currently being worked on.

Coordinator actions:
- Receive the user need.
- Start a new iteration from the requirements phase.

Exit condition:
- A concrete user need is available.

### 2. Requirements
Entry condition:
- A user need exists but is not yet confirmed as implementation-ready.

Coordinator actions:
- Delegate to the requirements engineer.
- Relay clarification questions to the user only when needed.
- Update `docs/requirements/current.md` until it is clear enough to proceed.
- Update memory when the phase is completed.

Exit condition:
- `docs/requirements/current.md` is complete enough for autonomous architecture and implementation.
- `Definition of Ready` in the requirements file is effectively `ready`.

Loop rule:
- Stay in this phase until blocking ambiguity is removed.

### 3. Architecture
Entry condition:
- Requirements are ready.

Coordinator actions:
- Delegate to the architect.
- Ensure `docs/design/current.md` is updated.
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
- Ensure `docs/dod/current.md` is updated.
- Ensure acceptance or end-to-end tests are added when feasible and worthwhile.
- Update memory when the phase is completed.

Exit condition:
- The tester has issued a clear DoD decision.

Loop rule:
- Return to development if defects or coverage gaps must be fixed.
- Return to architecture or requirements if the defect shows a deeper upstream problem.

### 7. DoD Review
Entry condition:
- The tester has produced `docs/dod/current.md`.

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
- Do not skip the review phase before testing.
- Keep durable project knowledge in `framework/memory/`.
- Keep the latest requirements in `docs/requirements/current.md`.
- Keep the latest design in `docs/design/current.md`.
- Keep the latest DoD review in `docs/dod/current.md`.
- Keep implementation in `src/`.
- Follow the engineering standards in `framework/clean-code.md`.
- Use the role-aligned skills in `.github/skills/` and `framework/skills.md` where applicable.
- The coordinator is responsible for updating `framework/flows/current-status.md`.
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

Memory update rules:
- `project-log.md` records what changed in chronological order.
- `decisions.md` records meaningful project decisions, their context, and consequences.
- `known-context.md` records stable truths that future agents should treat as current baseline context.
- Each entry should be short, factual, and useful for future agents.
- The coordinator updates memory after each completed phase, not only at the end of the full feature flow.

## Final Review
The tester must prepare a Definition of Done result that covers:
- What was built
- What was verified
- Any known gaps or risks
- What feedback is needed from the user

The coordinator uses that result for the final response.
