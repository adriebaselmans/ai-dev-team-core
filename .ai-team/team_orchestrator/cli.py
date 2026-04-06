from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agents.registry import build_default_agent_registry
from flows import default_flow_path
from framework.runtime.export_docs import export_all_docs
from framework.runtime.memory_export import render_memory_snapshot
from framework.runtime.repository_tool import repository_exploration_request
from state.factory import create_initial_state
from state.store import StateStore
from team_orchestrator.engine import Orchestrator
from team_orchestrator.flow_loader import load_flow
DEFAULT_STATE_PATH = Path(__file__).resolve().parents[2] / ".ai-team" / "framework" / "runtime" / "state.json"


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2))


def _status_payload(state: dict[str, object]) -> dict[str, object]:
    meta = state.get("meta", {}) if isinstance(state, dict) else {}
    return {
        "current_step": meta.get("current_step"),
        "completed": meta.get("completed"),
        "terminated": meta.get("terminated"),
        "termination_reason": meta.get("termination_reason"),
        "last_role": meta.get("last_role"),
        "flow_name": meta.get("flow_name"),
        "input": state.get("input") if isinstance(state, dict) else None,
    }


def cmd_run(args: argparse.Namespace) -> int:
    overrides: dict[str, object] = {}
    if args.repo_path:
        overrides["repository"] = {"path": args.repo_path}
    if args.parallel:
        coordination = dict(overrides.get("coordination", {})) if isinstance(overrides.get("coordination"), dict) else {}
        coordination["parallel_development"] = True
        overrides["coordination"] = coordination
    if args.work_item:
        coordination = dict(overrides.get("coordination", {})) if isinstance(overrides.get("coordination"), dict) else {}
        coordination["work_items"] = [
            {"id": f"item-{index + 1}", "description": item} for index, item in enumerate(args.work_item)
        ]
        overrides["coordination"] = coordination

    flow = load_flow(args.flow)
    state = create_initial_state(
        args.input,
        max_iterations=args.max_iterations,
        max_steps=args.max_steps,
        overrides=overrides or None,
    )
    final_state = Orchestrator(flow, build_default_agent_registry()).run(state)
    StateStore(args.state_path).save(final_state)
    _print_json(final_state if args.json else _status_payload(final_state))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    state = StateStore(args.state_path).load()
    _print_json(state if args.json else _status_payload(state))
    return 0


def cmd_export_docs(_: argparse.Namespace) -> int:
    try:
        written = export_all_docs(release_only=True)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    _print_json({"written": [str(path) for path in written]})
    return 0


def cmd_export_memory(args: argparse.Namespace) -> int:
    print(render_memory_snapshot(args.view, limit=args.limit), end="")
    return 0


def cmd_repository_tool(args: argparse.Namespace) -> int:
    _print_json(repository_exploration_request(args.target_path, args.objective))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the ai-dev-team-core orchestration system.")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the active flow-driven orchestrator.")
    run.add_argument("--input", required=True, help="User request or feature description.")
    run.add_argument("--flow", default=str(default_flow_path()), help="Path to the YAML flow definition.")
    run.add_argument("--repo-path", help="Optional repository path to mark the run as existing-repo mode.")
    run.add_argument("--parallel", action="store_true", help="Enable parallel development planning.")
    run.add_argument("--work-item", action="append", help="Optional development work item description. Repeat for multiple items.")
    run.add_argument("--max-iterations", type=int, default=5, help="Maximum loop iterations.")
    run.add_argument("--max-steps", type=int, default=40, help="Maximum executed steps before termination.")
    run.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH, help="Path to save final orchestration state.")
    run.add_argument("--json", action="store_true", help="Print full final state instead of a compact summary.")
    run.set_defaults(func=cmd_run)

    status = sub.add_parser("status", help="Show the last persisted orchestration state.")
    status.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH, help="Path to the saved state file.")
    status.add_argument("--json", action="store_true", help="Print the full saved state.")
    status.set_defaults(func=cmd_status)

    export_docs = sub.add_parser("export-docs", help="Generate release-only user-facing docs from doc_templates YAML.")
    export_docs.set_defaults(func=cmd_export_docs)

    export_memory = sub.add_parser("export-memory", help="Render an on-demand human-readable memory snapshot.")
    export_memory.add_argument("--view", required=True, choices=["project-log", "decisions", "known-context"])
    export_memory.add_argument("--limit", type=int, default=20, help="Maximum number of records to include.")
    export_memory.set_defaults(func=cmd_export_memory)

    repo_tool = sub.add_parser("repository-tool", help="Build a shared repository exploration tool request.")
    repo_tool.add_argument("--target-path", required=True, help="Repository path to explore.")
    repo_tool.add_argument("--objective", required=True, help="Exploration objective.")
    repo_tool.set_defaults(func=cmd_repository_tool)
    return parser


def main(argv: list[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    if not raw_args or raw_args[0].startswith("-"):
        raw_args = ["run", *raw_args]
    parser = build_parser()
    args = parser.parse_args(raw_args)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
