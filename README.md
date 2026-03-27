# ai-dev-team-core

Model-agnostic AI dev team framework with:
- role contracts
- project-local skills with explicit I/O contracts
- structured requirements/design/review/DoD artifacts
- a runtime orchestration layer for bounded specialist work
- repository exploration support and reusable repository knowledge storage

## Version
- Current release: `0.3`

## What This Repo Is
This repo is a reusable project skeleton.

Copy it for a new project, run `python init.py`, and then give the coordinator a feature request or user need. The system is designed to move through:
1. requirements
2. architecture
3. development
4. review
5. testing
6. DoD review

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
### 1. Start Codex
Start Codex in the repo root.

The root [AGENTS.md](AGENTS.md) tells Codex to use:
- the coordinator workflow in [framework/AGENTS.md](framework/AGENTS.md)
- role mappings in [framework/skills.md](framework/skills.md)
- the runtime contract in [framework/runtime/](framework/runtime/)

### 2. Give a Feature Request
Example:

```text
Build a small REST API in src for managing tasks with create/list/update/delete, persist data in SQLite, and add tests.
```

### 3. Use the Runtime Commands
Start a new feature flow:

```powershell
python framework/runtime/orchestrator.py start --feature "Build a small REST API for tasks"
```

Show current runtime state:

```powershell
python framework/runtime/orchestrator.py status
```

Show raw JSON runtime state:

```powershell
python framework/runtime/orchestrator.py status --json
```

Generate the bounded task payload for the current or a specified phase:

```powershell
python framework/runtime/orchestrator.py next-task
python framework/runtime/orchestrator.py next-task --phase requirements
```

Generate a bounded support-specialist task payload, such as repository exploration support:

```powershell
python framework/runtime/orchestrator.py specialist-task --role requirements-engineer --objective "Clarify the next feature request"
```

Repository exploration support is now invoked internally by the coordinator when a task needs repository grounding; it is no longer exposed as a standalone active role command.

Validate the current or a specified phase:

```powershell
python framework/runtime/orchestrator.py validate
python framework/runtime/orchestrator.py validate --phase requirements --check-status
```

Validate repository knowledge artifacts:

```powershell
python framework/runtime/orchestrator.py validate-repository-knowledge
```

Advance when the current phase is complete:

```powershell
python framework/runtime/orchestrator.py continue
```

Manually set a phase for recovery or controlled testing:

```powershell
python framework/runtime/orchestrator.py set-phase --phase review
```

Sync markdown status from machine-readable runtime state:

```powershell
python framework/runtime/orchestrator.py sync-status
```

Run runtime tests:

```powershell
python -m unittest discover framework/runtime/tests
```

## Runtime Behavior
- The coordinator is the only top-level user-facing agent.
- Specialist work is executed through bounded dispatch payloads.
- Repository exploration is a shared support capability rather than a mandatory workflow phase owner.
- Runtime specs live in `framework/runtime/`.
- The runtime maintains:
  - `framework/runtime/state.json`
  - `framework/flows/current-status.md`

The runtime contract:
- loads `team.yaml` and `workflow.yaml`
- builds bounded task payloads
- builds support-specialist task payloads
- validates phase artifacts
- validates repository knowledge artifacts
- advances or blocks phase progression

## Skills
- Roles define ownership and decision boundaries.
- Skills define how recurring work is performed.
- Project-local skills live in `.github/skills/`.
- Role-to-skill mapping lives in [framework/skills.md](framework/skills.md).

## Installed External Skills
Useful OpenAI skills have been installed in the current Codex environment:
- `openai-docs`
- `playwright`
- `security-best-practices`
- `security-threat-model`
- `doc`

Restart Codex after installing skills so they are available in a fresh session.

## Release Notes
- See [CHANGELOG.md](CHANGELOG.md) for release history.
