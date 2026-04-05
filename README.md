# ai-dev-team-core

Native AI dev team skeleton with:
- GitHub Copilot in Visual Studio Code as the primary runtime
- Codex compatibility through the same role, flow, and prompt contracts
- flow-driven orchestration as the canonical framework model
- structured role outputs, artifacts, and reusable repository knowledge
- a small Python validation harness for contracts, state, artifacts, and tests

## Version
- Current release: `1.0.0`

## Runtime Priority
1. GitHub Copilot in Visual Studio Code via `.github/agents/*.agent.md`
2. Codex compatibility through repository `AGENTS.md` plus the canonical framework files
3. Python validation harness for tests, state simulation, artifact sync, and contract checks

The repo no longer treats API or CLI backends as a primary role-execution path.

## Canonical Framework Files
- `AGENTS.md`: root entry point for Codex compatibility
- `framework/AGENTS.md`: canonical coordinator workflow contract
- `flows/software_delivery.yaml`: active delivery flow
- `framework/runtime/team.yaml`: role registry and ownership metadata
- `framework/config/runtimes.yaml`: native host runtime mapping for roles
- `framework/roles/*.md`: role-specific behavior contracts
- `framework/prompts/*`: layered prompt assets
- `framework/schemas/role_outputs.schema.yaml`: structured role output contract
- `.github/skills/*`: reusable skill guidance
- `.github/agents/*.agent.md`: native Copilot custom agent profiles

## What This Repo Is
This repo is a reusable skeleton for AI-assisted software delivery.

The framework contract is defined once and consumed in two ways:
- natively by GitHub Copilot in Visual Studio Code through custom agent profiles and handoff conventions
- compatibly by Codex through the repo instructions and the same role, prompt, and flow files

The Python code in this repo exists to:
- validate the flow and contracts
- simulate the role pipeline for tests
- persist structured artifacts and reusable memory in bootstrapped project repos
- keep the framework coherent outside a specific host runtime

It is not the preferred day-to-day specialist execution path.

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
- `.github/agents/`: native Copilot custom agent profiles
- `.github/skills/`: project-local skills and role procedures
- `agents/`: deterministic validation-harness role stubs for tests
- `team_orchestrator/`: flow engine, trace logging, artifact sync, runtime metadata loaders
- `flows/`: YAML flow definitions
- `state/`: shared state factory, merge logic, and persistence helpers
- `framework/`: team rules, prompts, roles, runtime metadata, schemas, and helper scripts
- `framework/runtime/`: runtime support utilities for snapshots, artifacts, memory, and repository tooling
- `src/`: implementation code
- `tests/`: automated validation for the skeleton

## Prerequisites
- Python 3.12+
- `pip`
- GitHub Copilot in Visual Studio Code for the primary runtime experience

## Setup
Run the guided bootstrap:

```powershell
python init.py
```

That script checks Python 3.12+, installs dependencies from `pyproject.toml`, validates the repository structure, and captures project metadata for the bootstrap flow.

## Primary Use: GitHub Copilot in VS Code
Open the repo in Visual Studio Code with GitHub Copilot enabled.

The native agent profiles in `.github/agents/` mirror the canonical framework roles. The intended operating model is:
- use the coordinator profile as the top-level entry point
- hand off to specialist roles through the flow contract
- keep support roles coordinator-mediated
- keep specialist profiles hidden from direct user selection
- keep structured artifact expectations aligned with the framework schemas

## Compatible Use: Codex
Start Codex in the repo root.

The root [AGENTS.md](AGENTS.md) directs Codex to the same canonical framework files used by Copilot:
- [framework/AGENTS.md](framework/AGENTS.md)
- [flows/software_delivery.yaml](flows/software_delivery.yaml)
- [framework/runtime/team.yaml](framework/runtime/team.yaml)
- [framework/config/runtimes.yaml](framework/config/runtimes.yaml)
- [framework/roles](framework/roles)
- [framework/prompts](framework/prompts)

Codex should follow the same role and flow contracts rather than a separate team model.

## Validation Harness
The Python harness remains useful for:
- contract validation
- orchestration simulation
- artifact export
- reusable memory sync
- automated tests

Run the validation harness with:

```powershell
python -m team_orchestrator.cli run --input "Build a small REST API for tasks"
python -m team_orchestrator.cli status
python -m pytest -q
```

## Runtime Behavior
- The canonical flow remains data-driven and lives in `flows/`.
- Shared state is the single source of truth for routing, gating, and artifact sync.
- Trace entries record runtime metadata from `framework/config/runtimes.yaml` and layered prompt metadata.
- Native Copilot agent profiles are the preferred execution surface.
- Codex compatibility uses the same contracts, not a separate framework fork.
- Support roles remain coordinator-mediated.
- Review, testing, and DoD gates return structured decisions with explicit rework targets.
- In bootstrapped project repos, durable phase artifacts are written to `doc_templates/*/current.yaml`.
- In the bare skeleton repo, `doc_templates/` and `docs/` remain pristine placeholders.
