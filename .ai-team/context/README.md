# Context Optimization

This directory explains how the skeleton manages context, output size, memory retrieval, and optional token-saving adapters. The framework must remain useful when no external adapter is installed.

## Files

- `policy.yaml`: canonical context, output, command, memory, and phase-profile policy.
- `adapters.yaml`: optional adapter registry with modes, detection hints, activation notes, and fallbacks.

## Default Behavior

The skeleton uses dependency-free defaults:

- compact status and handoff prose
- success-first command summaries
- phase-scoped artifact loading
- wiki index-first memory retrieval
- native host search and symbol tools

Formal artifacts, safety warnings, legal/compliance text, destructive action prompts, and sensitive clarifications are never compressed by optional style adapters.

## Adapter Modes

- `disabled`: never use this adapter.
- `detected`: use the adapter only when it is already available; otherwise use its fallback.
- `enabled`: prefer the adapter and warn when it is unavailable.
- `required`: fail doctor checks when unavailable.

The skeleton should default optional external adapters to `detected` or `disabled`, not `required`.

## Current Optional Adapters

- `rtk`: command-output compression for tests, builds, logs, package managers, and diffs.
- `caveman`: terse output style for routine handoffs and status updates.
- `headroom`: local reversible context compression/proxy for projects that explicitly adopt it.
- `serena`: semantic code tools through MCP/LSP when available.
- `memory-index`: generated local wiki search index; generated data must stay uncommitted.

## Activation

1. Edit `adapters.yaml` and choose a mode for the adapter.
2. Install or configure the external tool if the adapter requires one.
3. Run `python -m team_orchestrator.cli context status` to see the active layer.
4. Run `python -m team_orchestrator.cli context doctor` before requiring an adapter.

Use `detected` for convenience, `enabled` for project preference, and `required` only when the project cannot operate correctly without the adapter.

## Verification

`context status` prints the configured mode, availability, and fallback for each adapter.

`context doctor` validates that:

- `policy.yaml` and `adapters.yaml` are present and readable
- every adapter has a valid mode, kind, and fallback when optional
- required adapters are available
- the generated memory index is ignored by git when present
- phase profiles cover the active delivery flow roles

## Agent Protocol

Agents should load the `context-optimization` skill when doing token-sensitive work, repository exploration, phase handoffs, command summarization, or adapter diagnosis. The skill tells agents to explain which layer is active and to use fallbacks quietly when optional adapters are missing.
