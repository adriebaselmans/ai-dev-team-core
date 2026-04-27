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

## Project Data Locations

- `phase_artifacts/*/current.yaml`: current phase outputs in bootstrapped projects; pristine placeholders here.
- `.ai-team/memory/wiki/`: living project wiki for reusable knowledge; empty here except indexes and schema.
- `.ai-team/memory/changelog/`: audit trail for wiki writes.
- `docs/`: generated release docs only.
- `src/`: application source in bootstrapped projects; placeholder here.

## Context Optimization Policy

The source of truth is `.ai-team/context/policy.yaml`, with optional adapter activation in `.ai-team/context/adapters.yaml`.

Rules:
- Load wiki index first, then only phase-relevant pages.
- Prefer phase artifacts and compact handoff briefs over transcript rereads.
- Cache indexes in runtime state when useful; do not commit cached page content.
- Use compact modes only for routine handoffs, command summaries, or explicit token-saving requests.
- Keep formal artifacts, safety warnings, and irreversible-operation messages uncompressed.
- Use fallback behavior when optional external adapters are unavailable.

## Skeleton Invariants

- No provider-specific compatibility branch may become a second framework contract.
- No project wiki pages should be committed to this skeleton.
- No generated docs should be hand-maintained under `docs/`.
- No phase artifact path should use obsolete template-oriented naming.
- Agent profiles may be host-specific adapters, but the framework contract stays host-agnostic.
