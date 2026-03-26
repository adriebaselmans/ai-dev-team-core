---
name: acceptance-testing
description: Create or maintain automated acceptance or end-to-end tests when feasible, validate important user flows, and document when such automation is not practical.
---

# Acceptance Testing

Use this skill when acting as the tester for a feature where acceptance or end-to-end automation is feasible and worthwhile.

## Goals
- Validate user-visible behavior at acceptance level.
- Strengthen regression protection for important flows.

## Required Inputs
- `docs/requirements/current.md`
- `docs/design/current.md`
- Implementation and existing tests
- Current DoD artifact

## Required Outputs
- Acceptance or end-to-end tests when feasible
- Clear note when such automation is not feasible or not cost-effective

## Rules
- Cover the most important user flows first.
- Prefer stable, maintainable test flows over brittle end-to-end scripts.
- Be explicit about what the tests prove and what they do not prove.
