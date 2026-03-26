from __future__ import annotations

import argparse
import json
import sys

from spec_loader import load_team_spec, load_workflow_spec
from state_manager import (
    load_state,
    mark_phase_validation,
    save_and_sync,
    sync_status_markdown,
    transition_state,
)
from task_builder import build_specialist_task_payload, build_task_payload
from validators import validate_phase, validate_repository_knowledge_store, validate_status_sync


PHASE_STATE_TEXT = {
    "requirements": "requirements clarification in progress",
    "architecture": "architecture design in progress",
    "development": "implementation in progress",
    "review": "technical review in progress",
    "testing": "validation in progress",
    "dod-review": "awaiting user review",
    "done": "feature approved",
}


PHASE_NEXT_ACTION = {
    "requirements": "spawn requirements engineer task",
    "architecture": "spawn architect task",
    "development": "spawn developer task",
    "review": "spawn reviewer task",
    "testing": "spawn tester task",
    "dod-review": "present DoD review to the user",
    "done": "wait for a new user need",
}


def _owner_for_phase(phase: str, workflow_spec: dict) -> str:
    return workflow_spec["phase_specs"][phase]["owner"]


def cmd_status(args: argparse.Namespace) -> int:
    state = load_state()
    if args.json:
        print(json.dumps(state, indent=2))
        return 0

    print(f"Phase: {state['phase']}")
    print(f"Owner: {state['owner']}")
    print(f"State: {state['state']}")
    print(f"Next action: {state['next_action']}")
    print(f"Active feature: {state['active_feature']}")
    print(f"User input required: {state['user_input_required']}")
    return 0


def cmd_sync_status(_: argparse.Namespace) -> int:
    state = load_state()
    sync_status_markdown(state)
    print("Synchronized framework/flows/current-status.md from runtime state.")
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    workflow = load_workflow_spec()
    state = load_state()

    if state["phase"] != "idle" and not args.force:
        print("Runtime is not idle. Use --force to start a new feature anyway.", file=sys.stderr)
        return 1

    phase = "requirements"
    owner = _owner_for_phase(phase, workflow)
    state["active_feature"] = args.feature
    state["active_subagents"] = []
    state["pending_rollback_target"] = None
    state["user_input_required"] = False
    transition_state(
        state,
        phase=phase,
        owner=owner,
        state_text=PHASE_STATE_TEXT[phase],
        next_action=PHASE_NEXT_ACTION[phase],
        last_completed_phase=None,
        pending_rollback_target=None,
        user_input_required=False,
    )
    save_and_sync(state)
    print(build_task_payload(phase, load_team_spec(), workflow, args.feature))
    return 0


def cmd_next_task(args: argparse.Namespace) -> int:
    state = load_state()
    workflow = load_workflow_spec()
    team = load_team_spec()
    phase = args.phase or state["phase"]
    print(build_task_payload(phase, team, workflow, state.get("active_feature")))
    return 0


def cmd_specialist_task(args: argparse.Namespace) -> int:
    team = load_team_spec()
    state = load_state()
    role = args.role
    if role not in team.get("roles", {}):
        print(f"Unknown role: {role}", file=sys.stderr)
        return 1

    payload = build_specialist_task_payload(
        role,
        team,
        objective=args.objective,
        active_feature=args.feature or state.get("active_feature"),
        inputs=list(args.input or []) or None,
        owned_outputs=list(args.output or []) or None,
        completion=args.completion,
    )
    print(payload)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    state = load_state()
    phase = args.phase or state["phase"]
    result = validate_phase(phase)
    mark_phase_validation(state, phase, result.valid, result.messages)
    save_and_sync(state)
    for message in result.messages:
        print(message)
    if args.check_status:
        sync_result = validate_status_sync()
        for message in sync_result.messages:
            print(message)
        return 0 if result.valid and sync_result.valid else 1
    return 0 if result.valid else 1


def cmd_validate_repository_knowledge(_: argparse.Namespace) -> int:
    result = validate_repository_knowledge_store()
    for message in result.messages:
        print(message)
    return 0 if result.valid else 1


def cmd_continue(_: argparse.Namespace) -> int:
    workflow = load_workflow_spec()
    team = load_team_spec()
    state = load_state()
    phase = state["phase"]

    if phase == "idle":
        print("Runtime is idle. Start a feature first with the start command.", file=sys.stderr)
        return 1

    if phase in {"dod-review", "done"}:
        print("Current phase requires user input or a new feature; runtime will not auto-advance.", file=sys.stderr)
        return 1

    result = validate_phase(phase)
    mark_phase_validation(state, phase, result.valid, result.messages)

    if not result.valid:
        save_and_sync(state)
        print(f"Phase '{phase}' is not ready to advance.")
        for message in result.messages:
            print(f"- {message}")
        print()
        print(build_task_payload(phase, team, workflow, state.get("active_feature")))
        return 1

    next_phase = workflow["phase_specs"][phase]["next_phase"]
    owner = _owner_for_phase(next_phase, workflow)
    transition_state(
        state,
        phase=next_phase,
        owner=owner,
        state_text=PHASE_STATE_TEXT[next_phase],
        next_action=PHASE_NEXT_ACTION[next_phase],
        last_completed_phase=phase,
        pending_rollback_target=None,
        user_input_required=(next_phase == "dod-review"),
    )
    save_and_sync(state)

    print(f"Advanced from '{phase}' to '{next_phase}'.")
    if next_phase not in {"dod-review", "done"}:
        print()
        print(build_task_payload(next_phase, team, workflow, state.get("active_feature")))
    return 0


def cmd_set_phase(args: argparse.Namespace) -> int:
    workflow = load_workflow_spec()
    state = load_state()
    phase = args.phase
    owner = _owner_for_phase(phase, workflow)
    transition_state(
        state,
        phase=phase,
        owner=owner,
        state_text=args.state or PHASE_STATE_TEXT.get(phase, phase),
        next_action=args.next_action or PHASE_NEXT_ACTION.get(phase, "continue workflow"),
        pending_rollback_target=args.rollback_target,
        user_input_required=(phase == "dod-review"),
    )
    save_and_sync(state)
    print(f"Set runtime phase to '{phase}'.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Codex-first runtime orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", help="Start a new feature flow")
    start.add_argument("--feature", required=True, help="Feature description or feature id")
    start.add_argument("--force", action="store_true", help="Start even if runtime is not idle")
    start.set_defaults(func=cmd_start)

    cont = sub.add_parser("continue", help="Validate current phase and advance when ready")
    cont.set_defaults(func=cmd_continue)

    status = sub.add_parser("status", help="Show runtime state")
    status.add_argument("--json", action="store_true", help="Print raw JSON state")
    status.set_defaults(func=cmd_status)

    sync = sub.add_parser("sync-status", help="Sync markdown status from runtime state")
    sync.set_defaults(func=cmd_sync_status)

    validate = sub.add_parser("validate", help="Validate the current or specified phase")
    validate.add_argument("--phase", help="Phase to validate")
    validate.add_argument("--check-status", action="store_true", help="Also validate markdown/json status sync")
    validate.set_defaults(func=cmd_validate)

    validate_repo = sub.add_parser("validate-repository-knowledge", help="Validate repository knowledge artifacts")
    validate_repo.set_defaults(func=cmd_validate_repository_knowledge)

    next_task = sub.add_parser("next-task", help="Print the bounded task payload for a phase")
    next_task.add_argument("--phase", help="Phase to build a task for")
    next_task.set_defaults(func=cmd_next_task)

    specialist_task = sub.add_parser("specialist-task", help="Print a bounded task payload for a support specialist role")
    specialist_task.add_argument("--role", required=True, help="Role key from framework/runtime/team.yaml")
    specialist_task.add_argument("--objective", required=True, help="Bounded task objective")
    specialist_task.add_argument("--feature", help="Override active feature text")
    specialist_task.add_argument("--input", action="append", help="Additional input path or note", default=[])
    specialist_task.add_argument("--output", action="append", help="Override owned output path", default=[])
    specialist_task.add_argument("--completion", help="Override completion criteria")
    specialist_task.set_defaults(func=cmd_specialist_task)

    set_phase = sub.add_parser("set-phase", help="Manually set the active phase")
    set_phase.add_argument("--phase", required=True, help="Phase to set")
    set_phase.add_argument("--state", help="Override state text")
    set_phase.add_argument("--next-action", dest="next_action", help="Override next action")
    set_phase.add_argument("--rollback-target", help="Set pending rollback target")
    set_phase.set_defaults(func=cmd_set_phase)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
