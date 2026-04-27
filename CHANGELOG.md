# Changelog

## Unreleased
- Clarified active phase artifacts under `phase_artifacts/` for skeleton/project boundaries.
- Moved project memory to `.ai-team/memory/` so bootstrapped project knowledge is not framed as framework internals.
- Removed provider-specific compatibility language and replaced it with host-agnostic runtime terminology.
- Added RTK context profile policy for token-aware phase execution.
- Added self-describing context activation under `.ai-team/context/` with status and doctor CLI commands.
- Moved mutable orchestration state to ignored `.ai-team/runtime/state.json`.
- Added version metadata consistency checks for bootstrap and CLI diagnostics.

## 1.0.5
- Baseline native-agent skeleton with flow-driven orchestration, structured phase artifacts, project-local skills, and validation harness coverage.
