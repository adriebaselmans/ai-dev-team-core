# ai-dev-team-core

Codex-first skeleton for an AI-driven development team with:
- role contracts
- project-local skills
- durable requirements/design/review/DoD artifacts
- a runtime orchestration layer for specialist subagent work
- repository exploration and reusable repository knowledge storage

## Version
- Current release: `0.2`

## What This Repo Is
This repo is a reusable project skeleton.

Copy it for a new project, start Codex in the repo root, and give the coordinator a feature request or user need. The system is designed to move through:
1. requirements
2. architecture
3. development
4. review
5. testing
6. DoD review

The coordinator can also invoke the Explorer as a conditional support specialist when work must be grounded in an existing repository or application.

The active project artifacts start empty on purpose:
- `docs/requirements/current.md`
- `docs/design/current.md`
- `docs/review/current.md`
- `docs/dod/current.md`
- `framework/memory/*`

## Team
- Coordinator
- Explorer
- Requirements Engineer
- Architect
- Developer
- Reviewer
- Tester

## Repo Structure
- `AGENTS.md`: root entry point for Codex.
- `.github/skills/`: project-local skills for repeatable role behavior.
- `framework/`: team rules, roles, flow state, memory, and helper scripts.
- `framework/runtime/`: Codex-first runtime orchestration contract and Python runtime modules.
- `docs/`: active project artifacts.
- `src/`: implementation code.

## Prerequisites
For the repo contract itself:
- Codex can still use the repo structure and instructions without Python.

For the executable runtime orchestrator:
- Python 3.12+
- `pip`
- Python package dependency in [requirements.txt](/C:/github/ai-dev-team-core/framework/runtime/requirements.txt): `PyYAML`

If a user does not have Python, the repo still works as a skeleton, but the Python runtime commands will not run.

## Setup
Install runtime dependencies with either:

```powershell
python -m pip install -r framework/runtime/requirements.txt
```

or:

```powershell
pwsh -File framework/scripts/install-runtime-deps.ps1
```

If Python is installed under a different command name:

```powershell
pwsh -File framework/scripts/install-runtime-deps.ps1 -Python py
```

## How To Use
### 1. Start Codex
Start Codex in the repo root.

The root [AGENTS.md](/C:/github/ai-dev-team-core/AGENTS.md) tells Codex to use:
- the coordinator workflow in [framework/AGENTS.md](/C:/github/ai-dev-team-core/framework/AGENTS.md)
- role mappings in [skills.md](/C:/github/ai-dev-team-core/framework/skills.md)
- the runtime contract in [framework/runtime](/C:/github/ai-dev-team-core/framework/runtime)

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

Generate a bounded support-specialist task payload, such as a repository exploration task:

```powershell
python framework/runtime/orchestrator.py specialist-task --role explorer --objective "Analyze the target repository and produce a reusable repo brief"
```

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
- Specialist work should be executed through native Codex subagent spawning.
- Explorer is a conditional support specialist rather than a mandatory workflow phase owner.
- Runtime specs live in `framework/runtime/`.
- The runtime maintains:
  - `framework/runtime/state.json`
  - `framework/flows/current-status.md`

The current runtime implementation:
- loads `team.yaml` and `workflow.yaml`
- builds bounded task payloads
- builds support-specialist task payloads
- validates phase artifacts
- validates repository knowledge artifacts
- advances or blocks phase progression

It does not yet fully automate Codex subagent spawning by itself outside the active Codex runtime. The repo and runtime together provide the execution contract the coordinator should follow.

## Skills
- Roles define ownership and decision boundaries.
- Skills define how recurring work is performed.
- Project-local skills live in `.github/skills/`.
- Role-to-skill mapping lives in [skills.md](/C:/github/ai-dev-team-core/framework/skills.md).

## Installed External Skills
Useful OpenAI skills have been installed in the current Codex environment:
- `openai-docs`
- `playwright`
- `security-best-practices`
- `security-threat-model`
- `doc`

Restart Codex after installing skills so they are available in a fresh session.

## Release Notes
- See [CHANGELOG.md](/C:/github/ai-dev-team-core/CHANGELOG.md) for release history.
