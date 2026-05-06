---
name: implementation-clean-code
description: Implement the approved design in clean, maintainable code, keep changes aligned with requirements, and leave the codebase ready for review with unit tests and lint-clean output where practical.
---

# Implementation Clean Code

Use this skill when acting as the developer in this repository.

## Goals
- Implement the design faithfully.
- Produce maintainable code that follows the clean-code standard.
- Leave the change ready for technical review.

## Required Inputs
- `phase_artifacts/requirements/current.yaml`
- `phase_artifacts/design/current.yaml`
- `.ai-team/framework/clean-code.md`
- Relevant code in `src/`

## Required Outputs
- Updated implementation in `src/`
- Unit tests for relevant new or changed behavior

## Procedure
1. Implement only the approved scope.
2. Before editing, assess foreseeable side effects across callers, data, configuration, performance, compatibility, tests, and user-visible behavior.
3. Map each meaningful side-effect risk to a mitigation or validation check; escalate if the risk cannot be bounded.
4. Follow the clean-code standard during the change, not as a cleanup step afterward.
5. Add or update unit tests for all relevant new or changed logic.
6. Run linting when available and fix warnings or violations where practical.
7. Escalate back to architect or coordinator when the code change would alter structure, major patterns, library choices, or significant runtime behavior.

## Quality Bar
- Clear naming
- Small focused units
- Separation of concerns
- Explicit error handling
- No avoidable lint errors
- Side-effect assessment completed before implementation handoff
- No missing unit tests for relevant behavior
