from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from dataclasses import asdict, is_dataclass

if sys.version_info < (3, 12):
    raise SystemExit('framework/runtime/orchestrator.py requires Python 3.12+.')

from compaction import compact_phase
from execution import dispatch
from export_docs import export_all_docs
from repository_tool import repository_exploration_request
from spec_loader import default_trigger_for_phase, load_team_spec, load_workflow_spec, transition_spec
from state_manager import (
    load_state,
    mark_phase_validation,
    save_state,
    transition_state,
)
from task_builder import build_phase_dispatch_envelope, build_specialist_payload
from validators import validate_phase, validate_repository_knowledge_store, validate_transition


PHASE_STATE_TEXT = {
    'requirements': 'requirements clarification in progress',
    'architecture': 'architecture design in progress',
    'development': 'implementation in progress',
    'review': 'technical review in progress',
    'testing': 'validation in progress',
    'dod-review': 'awaiting user review',
    'done': 'feature approved',
    'idle': 'ready for first user need',
}


PHASE_NEXT_ACTION = {
    'requirements': 'dispatch requirements specialist',
    'architecture': 'dispatch architect',
    'development': 'dispatch developer',
    'review': 'dispatch reviewer',
    'testing': 'dispatch tester',
    'dod-review': 'present DoD review to the user',
    'done': 'wait for a new user need',
    'idle': 'receive a user need and start requirements clarification',
}


def _print_json(payload: object) -> None:
    def _default(value: object) -> object:
        if is_dataclass(value):
            return asdict(value)
        return str(value)

    print(json.dumps(payload, indent=2, default=_default))


def cmd_status(args: argparse.Namespace) -> int:
    state = load_state()
    if args.json:
        _print_json(state)
        return 0
    print(f"Phase: {state['phase']}")
    print(f"Owner: {state['owner']}")
    print(f"State: {state['state']}")
    print(f"Next action: {state['next_action']}")
    print(f"Active feature: {state['active_feature']}")
    print(f"User input required: {state['user_input_required']}")
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    state = load_state()
    if state['phase'] != 'idle' and not args.force:
        print('Runtime is not idle. Use --force to start a new feature anyway.', file=sys.stderr)
        return 1

    staged_state = deepcopy(state)
    transition_state(
        staged_state,
        phase='requirements',
        state_text=PHASE_STATE_TEXT['requirements'],
        next_action=PHASE_NEXT_ACTION['requirements'],
        last_completed_phase=None,
        pending_trigger='feature_received',
        user_input_required=False,
    )
    staged_state['active_feature'] = args.feature
    envelope = build_phase_dispatch_envelope('requirements', load_team_spec(), staged_state)
    save_state(staged_state)
    _print_json({'dispatch': envelope})
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    state = load_state()
    phase = args.phase or state['phase']
    result = validate_phase(phase)
    mark_phase_validation(state, phase, result.valid, result.messages)
    save_state(state)
    for message in result.messages:
        print(message)
    if args.trigger:
        transition_result = validate_transition(args.trigger, phase)
        for message in transition_result.messages:
            print(message)
        return 0 if result.valid and transition_result.valid else 1
    return 0 if result.valid else 1


def cmd_next_task(args: argparse.Namespace) -> int:
    state = load_state()
    phase = args.phase or state['phase']
    envelope = build_phase_dispatch_envelope(phase, load_team_spec(), state)
    _print_json({'dispatch': envelope})
    return 0


def cmd_dispatch(args: argparse.Namespace) -> int:
    state = load_state()
    phase = args.phase or state['phase']
    envelope = build_phase_dispatch_envelope(phase, load_team_spec(), state)
    receipt = dispatch(envelope)
    _print_json({'dispatch': envelope, 'receipt': receipt.as_dict()})
    return 0


def cmd_specialist_task(args: argparse.Namespace) -> int:
    payload = build_specialist_payload(args.role, load_team_spec(), load_state(), args.objective)
    _print_json(payload)
    return 0


def cmd_repository_tool(args: argparse.Namespace) -> int:
    _print_json(repository_exploration_request(args.target_path, args.objective))
    return 0


def cmd_validate_repository_knowledge(_: argparse.Namespace) -> int:
    result = validate_repository_knowledge_store()
    for message in result.messages:
        print(message)
    return 0 if result.valid else 1


def cmd_export_docs(_: argparse.Namespace) -> int:
    try:
        written = export_all_docs(release_only=True)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    _print_json({'written': [str(path) for path in written]})
    return 0


def cmd_continue(args: argparse.Namespace) -> int:
    workflow = load_workflow_spec()
    state = load_state()
    phase = state['phase']
    if phase in {'idle', 'done'}:
        print('Current phase requires a manual start or reset.', file=sys.stderr)
        return 1
    if phase == 'dod-review':
        print('Current phase requires user input; runtime will not auto-advance.', file=sys.stderr)
        return 1

    trigger = args.trigger or default_trigger_for_phase(phase)
    if trigger is None:
        print(f"No default transition trigger configured for phase '{phase}'.", file=sys.stderr)
        return 1

    phase_result = validate_phase(phase)
    transition_result = validate_transition(trigger, phase)
    mark_phase_validation(state, phase, phase_result.valid, phase_result.messages)
    if not phase_result.valid or not transition_result.valid:
        save_state(state)
        for message in phase_result.messages + transition_result.messages:
            print(message)
        return 1

    current_phase_spec = workflow['phases'][phase]
    compact_phase(phase, current_phase_spec.get('artifact'), state.get('active_feature'))
    next_phase = transition_spec(trigger)['to']
    transition_state(
        state,
        phase=next_phase,
        state_text=PHASE_STATE_TEXT[next_phase],
        next_action=PHASE_NEXT_ACTION[next_phase],
        last_completed_phase=phase,
        pending_trigger=trigger,
        user_input_required=(next_phase == 'dod-review'),
    )
    save_state(state)
    print(f"Advanced from '{phase}' to '{next_phase}' via '{trigger}'.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Model-agnostic runtime orchestrator')
    sub = parser.add_subparsers(dest='command', required=True)

    start = sub.add_parser('start', help='Start a new feature flow')
    start.add_argument('--feature', required=True, help='Feature description or feature id')
    start.add_argument('--force', action='store_true', help='Start even if runtime is not idle')
    start.set_defaults(func=cmd_start)

    cont = sub.add_parser('continue', help='Validate current phase and advance when ready')
    cont.add_argument('--trigger', help='Override the transition trigger')
    cont.set_defaults(func=cmd_continue)

    status = sub.add_parser('status', help='Show runtime state')
    status.add_argument('--json', action='store_true', help='Print raw JSON state')
    status.set_defaults(func=cmd_status)

    validate = sub.add_parser('validate', help='Validate the current or specified phase')
    validate.add_argument('--phase', help='Phase to validate')
    validate.add_argument('--trigger', help='Also validate a transition trigger')
    validate.set_defaults(func=cmd_validate)

    next_task = sub.add_parser('next-task', help='Print the bounded dispatch payload for a phase')
    next_task.add_argument('--phase', help='Phase to build a dispatch for')
    next_task.set_defaults(func=cmd_next_task)

    dispatch_cmd = sub.add_parser('dispatch', help='Build and dispatch the current or specified phase payload')
    dispatch_cmd.add_argument('--phase', help='Phase to dispatch')
    dispatch_cmd.set_defaults(func=cmd_dispatch)

    specialist_task = sub.add_parser('specialist-task', help='Print a bounded support-specialist payload')
    specialist_task.add_argument('--role', required=True, help='Role key from framework/runtime/team.yaml')
    specialist_task.add_argument('--objective', required=True, help='Bounded task objective')
    specialist_task.set_defaults(func=cmd_specialist_task)

    repo_tool = sub.add_parser('repository-tool', help='Build a shared repository exploration tool request')
    repo_tool.add_argument('--target-path', required=True, help='Repository path to explore')
    repo_tool.add_argument('--objective', required=True, help='Exploration objective')
    repo_tool.set_defaults(func=cmd_repository_tool)

    validate_repo = sub.add_parser('validate-repository-knowledge', help='Validate repository knowledge artifacts')
    validate_repo.set_defaults(func=cmd_validate_repository_knowledge)

    export_docs = sub.add_parser('export-docs', help='Generate release-only user-facing docs from doc_templates YAML')
    export_docs.set_defaults(func=cmd_export_docs)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
