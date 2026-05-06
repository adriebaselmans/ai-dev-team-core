---
name: architecture-design
description: Produce a compact technical design that satisfies the active requirements baseline, enforces clean-code principles, uses current best practices for the chosen stack, and makes important performance tradeoffs explicit.
---

# Architecture Design

Use this skill when acting as the architect in this repository.

## Goals
- Create an implementation-safe design.
- Keep the design simple, clean, and testable.
- Make relevant CPU and memory tradeoffs explicit.

## Required Inputs
- `phase_artifacts/requirements/current.yaml`
- `phase_artifacts/design/current.yaml`
- `.ai-team/framework/clean-code.md`
- Relevant code in `src/`
- Project wiki via `wiki-read` skill

## Required Output
- Updated `phase_artifacts/design/current.yaml`

## Procedure
1. Read the active requirements and current codebase.
2. Identify affected modules, boundaries, contracts, and foreseeable side effects.
3. Research the best current stack-appropriate approach when a meaningful technical choice exists.
4. Choose the simplest design that satisfies the requirements and supports maintainable implementation.
5. Map side-effect risks to mitigations and validation expectations before approving implementation.
6. Document separation of concerns, module ownership, interfaces, data flow, clean-code constraints, performance considerations, side-effect controls, and non-goals.

## Design Rules
- Prefer current stable ecosystem practices over outdated patterns.
- Avoid speculative architecture.
- Separate business logic, orchestration, and I/O where practical.
- Make non-trivial CPU or memory tradeoffs explicit.
- Do not approve design for implementation until side effects are assessed and validation expectations are explicit.
- Return to requirements if functional ambiguity blocks safe design.
