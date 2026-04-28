# AI Team Architecture

This skeleton is a reusable framework core. Keep project-specific state out of this repository.

## Canonical Layers

- Entry: `AGENTS.md` is a thin host-agnostic launcher for instruction-compatible tools.
- Contract: `.ai-team/framework/AGENTS.md` owns the workflow, memory, artifact, and role-boundary rules.
- Flow: `.ai-team/flows/software_delivery.yaml` defines phase order and gates.
- Roles: `.ai-team/framework/roles/*.md` define role behavior.
- Native profiles: `.github/agents/*.agent.md` adapt roles to project-agent hosts.
- Skills: `.github/skills/*/SKILL.md` define reusable procedures.
- Context: `.ai-team/context/` explains token policy, optional adapters, activation modes, and fallbacks.
- Runtime harness: `.ai-team/team_orchestrator/`, `.ai-team/state/`, and `.ai-team/agents/` validate the contract locally.

For concrete paths and project data locations, see the Canonical Map in `README.md`.

## Context Optimization Policy

The source of truth is `.ai-team/context/policy.yaml`, with optional adapter activation in `.ai-team/context/adapters.yaml`. Runtime guidance lives in `.ai-team/framework/AGENTS.md` under "Token Policy" and "Memory Policy".

## Skeleton Invariants

- No provider-specific compatibility branch may become a second framework contract.
- Agent profiles may be host-specific adapters, but the framework contract stays host-agnostic.
- Keep `.ai-team/memory/wiki/` empty except indexes and schema in this skeleton.
- Keep reusable knowledge in wiki pages only after a project is bootstrapped from the skeleton.
- Keep `phase_artifacts/*/current.yaml` as pristine placeholders in this skeleton.
- No phase artifact path should use obsolete template-oriented naming.
- Keep `docs/` generated-only; do not edit release docs by hand.

