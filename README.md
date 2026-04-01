# ai-dev-team-core

Model-agnostic AI dev team framework with:
- flow-driven orchestration as the primary abstraction
- stateless role agents with strict output ownership
- a shared structured state as the single source of truth
- configurable branching, loops, support dispatch, and safe termination
- repository exploration support and reusable repository knowledge storage
- structured requirements/design/review/DoD artifacts for project delivery

## Version
- Current release: `0.9`

## What This Repo Is
This repo is a reusable project skeleton.

Copy it for a new project, run `python init.py`, and then give the coordinator a feature request or user need.

The current system is a true orchestration-based AI dev team. It is designed around:
- a coordinator that stays logically in control but remains read-only for product artifacts
- explicit role separation between requirements, design, implementation, review, testing, and DoD validation
- reusable support roles for repository exploration, UX/UI clarification, and external scouting
- data-driven flow definitions in YAML rather than hardcoded agent order
- structured gate results and rework routing instead of string parsing

The default flow supports:
1. coordinator intake and repo-mode classification
2. repository exploration for existing repos
3. requirements clarification
4. optional UX/UI clarification
5. architecture and optional support dispatch
6. development, including optional parallel worker fan-out plus designated integration
7. code review with structured rework decisions
8. testing with automated validation where sensible
9. DoD review against functional and non-functional requirements
10. final coordinator completion

> **WARNING**
> `start.bat` launches Codex with `--ask-for-approval never`. That suppresses approval prompts and can make destructive or unintended actions easier to execute in the wrong workspace. Use it only in a trusted local checkout where you are comfortable with fully autonomous execution.

The coordinator can invoke support roles when work needs repository grounding, UX/UI clarification, or current external research. Roles do not call each other directly; collaboration is mediated through shared state and coordinator-approved support requests.

The active AI-owned project artifacts start empty on purpose:
- `doc_templates/requirements/current.yaml`
- `doc_templates/design/current.yaml`
- `doc_templates/review/current.yaml`
- `doc_templates/dod/current.yaml`
- `framework/memory/*`

Generate user-facing docs only on a release branch with:

```powershell
python framework/runtime/orchestrator.py export-docs
```

or:

```powershell
pwsh -File framework/scripts/export-release-docs.ps1
```

That writes generated output under `docs/` and is intended to be checked in only when releasing.

## Team
- Coordinator
- Requirements Engineer
- UX/UI Designer
- Scout
- Architect
- Developer
- Reviewer
- Tester
- DoD Reviewer
- Repository Exploration Support

## Repo Structure
- `AGENTS.md`: root entry point for Codex.
- `agents/`: stateless role agents and role discovery.
- `team_orchestrator/`: flow execution engine, condition handling, trace logging, and CLI.
- `flows/`: YAML flow definitions.
- `state/`: shared state factory, merge logic, and persistence helpers.
- `.github/skills/`: project-local skills for repeatable role behavior.
- `framework/`: team rules, roles, flow state, memory, and helper scripts.
- `framework/runtime/`: legacy runtime contract, role registry, state helpers, and compatibility modules.
- `doc_templates/`: active AI-owned project artifacts.
- `docs/`: user-facing generated documentation output.
- `src/`: implementation code.
- `tests/`: end-to-end and unit coverage for the orchestration system.

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
- the flow-driven orchestration core in `agents/`, `team_orchestrator/`, `flows/`, and `state/`

Example feature request:

```text
Build a small REST API in src for managing tasks with create/list/update/delete, persist data in SQLite, and add tests.
```

Flow orchestration commands:

```powershell
python run_dev_team.py
python -m team_orchestrator.cli --input "Build a small REST API for tasks"
ai-dev-team-run --input "Build a small REST API for tasks"
```

Legacy runtime contract commands:

```powershell
python framework/runtime/orchestrator.py start --feature "Build a small REST API for tasks"
python framework/runtime/orchestrator.py status
python framework/runtime/orchestrator.py next-task
python framework/runtime/orchestrator.py validate
python framework/runtime/orchestrator.py continue
python -m unittest discover framework/runtime/tests
```

Generate release-only user-facing docs from `doc_templates/`:

```powershell
python framework/runtime/orchestrator.py export-docs
pwsh -File framework/scripts/export-release-docs.ps1
```

Repository exploration support is invoked internally by the coordinator when a task needs repository grounding. UX/UI and scout support follow the same coordinator-mediated support-request pattern.

## Runtime Behavior
- The coordinator is the only top-level user-facing agent.
- Flow definitions are data-driven and live in `flows/`.
- Agents are stateless and only return owned state fields.
- Shared state is the single source of truth for execution, trace, and routing decisions.
- Support roles are reusable and coordinator-mediated.
- Review, test, and DoD gates return structured decisions with explicit rework targets.
- The system supports loops, branching, parallel development fan-out, integration, and safe termination.
- Runtime specs and legacy compatibility modules remain in `framework/runtime/`.
