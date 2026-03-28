# Runtime Orchestration

This folder defines the runtime orchestration contract for this repository.

## Purpose
- The repository files define the team and workflow.
- The coordinator uses bounded specialist dispatch to execute the workflow.
- These files provide the machine-readable and template-backed runtime contract.

## Files
- `team.yaml`: role registry, ownership, and dispatch defaults.
- `workflow.yaml`: state machine, transition rules, rollback rules, and required artifacts.
- `context_slices.yaml`: per-role context slice definitions.
- `task-template.md`: standard task payload for spawned specialist subagents.
- `review-template.md`: standard findings format for reviewer output.
- `framework/memory/repository-knowledge/`: durable repository briefs and machine-readable facts for support exploration work.
- `state.json`: machine-readable runtime state snapshot.
- `orchestrator.py`: CLI entrypoint for runtime execution.
- `state_manager.py`: runtime state loading, saving, and markdown sync.
- `spec_loader.py`: YAML spec loading.
- `task_builder.py`: bounded specialist task payload generation.
- `validators.py`: phase validators.
- `result_contract.py`: structured subagent result contract.
- `requirements.txt`: compatibility dependency list.

## Runtime Rule
- The coordinator is the only top-level user-facing agent.
- The coordinator should use bounded specialist dispatch for specialist work when the task is clear.
- Each spawned specialist gets one role, one bounded objective, explicit artifact ownership, and explicit completion criteria.
- Repository exploration is a shared support capability for grounding work; it is not part of the mandatory phase state machine.

## Prerequisites
- Python 3.12+
- `pip`

## Quickstart
Install dependencies:

```powershell
python -m pip install -e .
```

Start a feature flow:

```powershell
python framework/runtime/orchestrator.py start --feature "Describe the feature here"
```

Check runtime state:

```powershell
python framework/runtime/orchestrator.py status
```

Advance when the current phase artifact is ready:

```powershell
python framework/runtime/orchestrator.py continue
```

Repository exploration support is invoked by the coordinator when a task needs grounded repository analysis. It is not exposed as a standalone active role command in this runtime contract.

Release-only user docs are generated from the YAML templates with:

```powershell
python framework/runtime/orchestrator.py export-docs
```

or the wrapper script:

```powershell
pwsh -File framework/scripts/export-release-docs.ps1
```

Run that only on a release branch. The generated `docs/` output is intended for release check-in, not as an active source of truth.

Validate repository knowledge artifacts:

```powershell
python framework/runtime/orchestrator.py validate-repository-knowledge
```

Generate release-only user docs from `doc_templates/`:

```powershell
python framework/runtime/orchestrator.py export-docs
```

Or use the release wrapper:

```powershell
pwsh -File framework/scripts/export-release-docs.ps1
```

Run runtime tests:

```powershell
python -m unittest discover framework/runtime/tests
```
