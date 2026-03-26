# Runtime Orchestration

This folder defines the Codex-first runtime orchestration model for this repository.

## Purpose
- The repository files define the team and workflow.
- The coordinator uses native Codex subagent spawning to execute the workflow.
- These files provide the machine-readable and template-backed runtime contract.

## Files
- `team.yaml`: role registry, ownership, and default subagent model.
- `workflow.yaml`: phase state machine, exit rules, rollback rules, and required artifacts.
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
- `requirements.txt`: Python runtime dependencies.

## Codex-First Rule
- The coordinator is the only top-level user-facing agent.
- The coordinator should use native subagent spawning for specialist work when the task is bounded.
- Each spawned specialist gets one role, one bounded objective, explicit artifact ownership, and explicit completion criteria.
- The explorer is a conditional support specialist for repository grounding; it is not part of the mandatory phase state machine.

## Prerequisites
- Python 3.12+
- `pip`
- Dependencies from `requirements.txt`

## Quickstart
Install dependencies:

```powershell
python -m pip install -r framework/runtime/requirements.txt
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

Print a bounded task payload for a support specialist such as the explorer:

```powershell
python framework/runtime/orchestrator.py specialist-task --role explorer --objective "Analyze the target repository and produce a reusable repo brief"
```

Validate repository knowledge artifacts:

```powershell
python framework/runtime/orchestrator.py validate-repository-knowledge
```

Run runtime tests:

```powershell
python -m unittest discover framework/runtime/tests
```
