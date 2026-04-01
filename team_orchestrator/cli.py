from __future__ import annotations

import argparse
import json
from pathlib import Path

from agents.registry import build_default_agent_registry
from state.factory import create_initial_state
from team_orchestrator.engine import Orchestrator
from team_orchestrator.flow_loader import load_flow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the ai-dev-team-core orchestration flow.")
    parser.add_argument("--input", required=True, help="User request or feature description.")
    parser.add_argument(
        "--flow",
        default=str(Path(__file__).resolve().parents[1] / "flows" / "software_delivery.yaml"),
        help="Path to the YAML flow definition.",
    )
    parser.add_argument("--max-iterations", type=int, default=5, help="Maximum loop iterations.")
    parser.add_argument("--max-steps", type=int, default=40, help="Maximum executed steps before termination.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    flow = load_flow(args.flow)
    agents = build_default_agent_registry()
    state = create_initial_state(
        args.input,
        max_iterations=args.max_iterations,
        max_steps=args.max_steps,
    )
    final_state = Orchestrator(flow, agents).run(state)
    print(json.dumps(final_state, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
