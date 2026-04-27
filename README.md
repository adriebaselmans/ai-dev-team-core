# ai-dev-team-core

Reusable, host-agnostic AI dev team skeleton for flow-driven software delivery.

## Version
- Current release: `1.0.5`

## What This Repo Is
This repository is a pristine framework skeleton, not an application repo. It provides:
- a canonical role and flow contract for AI-assisted delivery
- native agent profiles for hosts that support project agents
- instruction-file compatibility for hosts that read repository guidance
- structured phase artifacts under `phase_artifacts/`
- project memory under `.ai-team/memory/wiki/`
- a small Python validation harness for contracts, state, artifacts, memory, and tests

The skeleton must stay reusable. Project-specific knowledge belongs in bootstrapped project repos, not in this core repo.

## Canonical Map
- [AGENTS.md](AGENTS.md): thin host entry point.
- [.ai-team/framework/AGENTS.md](.ai-team/framework/AGENTS.md): authoritative workflow, memory, artifact, and role-boundary contract.
- [.ai-team/ARCHITECTURE.md](.ai-team/ARCHITECTURE.md): compact framework structure and invariants.
- [.ai-team/flows/software_delivery.yaml](.ai-team/flows/software_delivery.yaml): active delivery flow.
- [.ai-team/framework/runtime/team.yaml](.ai-team/framework/runtime/team.yaml): role registry and ownership metadata.
- [.ai-team/framework/config/runtimes.yaml](.ai-team/framework/config/runtimes.yaml): host runtime capability map.
- [.ai-team/context](.ai-team/context): context optimization policy, optional adapters, activation docs, and fallbacks.
- [.ai-team/framework/config/copilot_role_models.yaml](.ai-team/framework/config/copilot_role_models.yaml): VS Code Copilot model preferences when that host is used.
- [.ai-team/framework/roles](.ai-team/framework/roles): role-specific behavior contracts.
- [.ai-team/framework/prompts](.ai-team/framework/prompts): shared prompt layers.
- [.github/agents](.github/agents): native project-agent profiles.
- [.github/skills](.github/skills): reusable skill guidance.
- [phase_artifacts](phase_artifacts): current phase artifacts in bootstrapped projects; pristine placeholders here.
- [.ai-team/memory/wiki](.ai-team/memory/wiki): living project wiki in bootstrapped projects; empty here.
- [docs](docs): generated user-facing release docs only.

## Runtime Model
1. Native project-agent hosts use `.github/agents/*.agent.md` when supported.
2. Instruction-compatible hosts use [AGENTS.md](AGENTS.md) and the same canonical framework files.
3. The Python harness validates contracts, simulates the flow, persists phase artifacts, exports docs, and checks memory behavior.

No provider-specific compatibility path owns the framework. Host-specific profiles are adapters over the same role, flow, prompt, and artifact contracts.

## Prerequisites
- Python 3.12+
- `pip`
- Optional: a host that supports project agent profiles, such as GitHub Copilot in Visual Studio Code

## Setup
Run the guided bootstrap:

```powershell
python init.py
```

That script checks Python 3.12+, installs dependencies from `pyproject.toml`, validates the repository structure, and captures project metadata for bootstrapped project behavior.

## Validation Harness
Run the harness with:

```powershell
python -m team_orchestrator.cli run --input "Build a small REST API for tasks"
python -m team_orchestrator.cli status
python -m team_orchestrator.cli version
python -m team_orchestrator.cli context status
python -m team_orchestrator.cli context doctor
python -m pytest -q
```

## Context Optimization
The skeleton works without external token tools. Optional adapters for command summaries, output style, context compression, semantic code navigation, and generated memory search are documented in [.ai-team/context/README.md](.ai-team/context/README.md).

## Skeleton Invariants
- Keep `.ai-team/memory/wiki/` empty except indexes and schema in this skeleton.
- Keep `phase_artifacts/*/current.yaml` as pristine placeholders in this skeleton.
- Keep `docs/` generated-only; do not edit release docs by hand.
- Keep host-specific files as adapters, not alternate framework contracts.
- Keep reusable knowledge in wiki pages only after a project is bootstrapped from the skeleton.
