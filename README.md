# ai-dev-team-core

Model-agnostic AI dev team framework with:
- role contracts
- project-local skills with explicit I/O contracts
- structured requirements/design/review/DoD artifacts
- a runtime orchestration layer for bounded specialist work
- repository exploration support and reusable repository knowledge storage

## Version
- Current release: `0.4`

## What This Repo Is
This repo is a reusable project skeleton.

Copy it for a new project, run `python init.py`, and then give the coordinator a feature request or user need. The system is designed to move through:
1. requirements
2. architecture
3. development
4. review
5. testing
6. DoD review

> **WARNING**
> `start.bat` launches Codex with `--ask-for-approval never`. That suppresses approval prompts and can make destructive or unintended actions easier to execute in the wrong workspace. Use it only in a trusted local checkout where you are comfortable with fully autonomous execution.

The coordinator can invoke repository exploration support when work must be grounded in an existing repository or application.

The active project artifacts start empty on purpose:
- `docs/requirements/current.md`
- `docs/design/current.md`
- `docs/review/current.md`
- `docs/dod/current.md`
- `framework/memory/*`

## Team
- Coordinator
- Requirements Engineer
- Architect
- Developer
- Reviewer
- Tester
- Repository exploration support

## Repo Structure
- `AGENTS.md`: root entry point for Codex.
- `.github/skills/`: project-local skills for repeatable role behavior.
- `framework/`: team rules, roles, flow state, memory, and helper scripts.
- `framework/runtime/`: runtime orchestration contract and Python runtime modules.
- `docs/`: active project artifacts.
- `src/`: implementation code.

## Prerequisites
- Python 3.12+
- `pip`

## Setup
Run the guided bootstrap:

```powershell
python init.py
```

That script checks Python 3.12+, installs dependencies from `pyproject.toml`, validates the repository structure, and captures project metadata for the bootstrap flow.

## How To Use
Start Codex in the repo root.

The root [AGENTS.md](AGENTS.md) tells Codex to use:
- the coordinator workflow in [framework/AGENTS.md](framework/AGENTS.md)
- role mappings in [framework/skills.md](framework/skills.md)
- the runtime contract in [framework/runtime/](framework/runtime/)

Example feature request:

```text
Build a small REST API in src for managing tasks with create/list/update/delete, persist data in SQLite, and add tests.
```

Runtime commands:

```powershell
python framework/runtime/orchestrator.py start --feature "Build a small REST API for tasks"
python framework/runtime/orchestrator.py status
python framework/runtime/orchestrator.py next-task
python framework/runtime/orchestrator.py validate
python framework/runtime/orchestrator.py continue
python framework/runtime/orchestrator.py sync-status
python -m unittest discover framework/runtime/tests
```

Repository exploration support is invoked internally by the coordinator when a task needs repository grounding; it is not exposed as a standalone active role command.

## Runtime Behavior
- The coordinator is the only top-level user-facing agent.
- Specialist work is executed through bounded dispatch payloads.
- Repository exploration is a shared support capability rather than a mandatory workflow phase owner.
- Runtime specs live in `framework/runtime/`.
- The runtime maintains:
  - `framework/runtime/state.json`
  - `framework/flows/current-status.md`

## Release Notes
- See [CHANGELOG.md](CHANGELOG.md) for release history.
