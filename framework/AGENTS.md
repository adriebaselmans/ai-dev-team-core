# AI Dev Team Framework

This file defines the canonical team workflow for this repository.

## Goal
Take a user need or feature description and deliver an end-to-end implementation with minimal human intervention.

## Team Roles
- Coordinator: owns intake, delegation, phase transitions, integration, and final reporting.
- Requirements Engineer: clarifies the request and writes the requirement baseline.
- Architect: writes the design approach and technical constraints.
- Developer: implements the solution in `src/`.
- Tester: validates the implementation against the requirement baseline and prepares the DoD review.

Detailed role instructions live in `framework/roles/`.

## Workflow
1. Coordinator receives the user need.
2. Coordinator delegates to the requirements engineer.
3. Requirements engineer asks the user questions only when the need is not clear enough to implement safely.
4. Once the need is clear, the coordinator proceeds without further user intervention.
5. Architect writes or updates `docs/design/current.md`.
6. Developer implements the solution in `src/`.
7. Tester validates the implementation and updates the DoD result.
8. Coordinator presents the final DoD review to the user.
9. If the user provides feedback, start a new iteration from the requirements phase and keep prior memory.

## Non-Negotiable Rules
- Do not ask the user for approval between architecture, development, and testing once the requirements are clear.
- Keep durable project knowledge in `framework/memory/`.
- Keep the latest requirements in `docs/requirements/current.md`.
- Keep the latest design in `docs/design/current.md`.
- Keep implementation in `src/`.
- The coordinator is responsible for updating `framework/flows/current-status.md`.

## Memory Policy
Update memory at the end of each completed phase.

Required memory files:
- `framework/memory/project-log.md`: chronological log of what was built.
- `framework/memory/decisions.md`: important decisions and why they were made.
- `framework/memory/known-context.md`: stable context, conventions, and assumptions.

Each entry should be short and useful for future agents.

## Final Review
The tester must prepare a Definition of Done result that covers:
- What was built
- What was verified
- Any known gaps or risks
- What feedback is needed from the user

The coordinator uses that result for the final response.
