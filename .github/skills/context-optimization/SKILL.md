---
name: context-optimization
description: "Use when: minimizing token usage, summarizing command output, choosing compact output style, loading phase context, checking optional adapters, diagnosing context status, or explaining how the skeleton activates RTK, caveman, Headroom, Serena, memory index, and fallback layers."
---

# Context Optimization

Use this skill when work is token-sensitive, when a phase handoff is being prepared, when command output must be summarized, or when the user asks how context, memory, or optional adapters are activated.

## Required Inputs

- `.ai-team/context/policy.yaml`
- `.ai-team/context/adapters.yaml`
- `.ai-team/memory/wiki/_index.yaml` when memory retrieval is needed
- Active phase artifact paths listed by the selected profile

## Procedure

1. Read `.ai-team/context/policy.yaml` and choose the profile for the active role or phase.
2. Read `.ai-team/context/adapters.yaml` before assuming an external token tool is active.
3. Treat external adapters as optional unless their mode is `required`.
4. If an adapter is `disabled`, do not use it.
5. If an adapter is `detected`, use it only when it is already available; otherwise use its fallback silently.
6. If an adapter is `enabled`, prefer it and mention its fallback when unavailable.
7. If an adapter is `required` and unavailable, stop the adapter-dependent action and report the setup gap.
8. Keep formal artifacts, safety warnings, legal/compliance text, destructive action prompts, and sensitive clarifications in normal prose.
9. For successful commands, summarize outcome first and avoid raw logs unless warnings are material.
10. For failures, report the failing command, core error, affected file or component, and next action.

## Output Classes

- `formal_artifact`: never compress beyond the artifact schema.
- `user_final`: concise but complete user-facing summary.
- `phase_handoff`: compact structured handoff.
- `routine_status`: short progress update.
- `command_summary`: success-first, failures-only, deduplicated logs.
- `review_comment`: compact findings with clear severity.
- `safety_warning`: uncompressed and explicit.

## Adapter Notes

- `rtk` compresses command output when available; fallback is `builtin-command-summary`.
- `caveman` is for terse routine updates and handoffs only; fallback is `builtin-compact`.
- `headroom` is disabled by default and should be used only after explicit project adoption.
- `serena` can assist semantic code navigation when available; fallback is native search and symbol tools.
- `memory-index` is generated local search state; fallback is wiki index-only retrieval.

## Verification

Use the CLI when available:

```bash
python -m team_orchestrator.cli context status
python -m team_orchestrator.cli context doctor
```

Report the active layer only when it helps the user or affects behavior. Do not spend tokens explaining inactive optional adapters during normal implementation work.
