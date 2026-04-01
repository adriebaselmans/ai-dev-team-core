from __future__ import annotations

import json

from agents.registry import build_default_agent_registry
from flows import default_flow_path
from state.factory import create_initial_state
from team_orchestrator.engine import Orchestrator
from team_orchestrator.flow_loader import load_flow


def main() -> int:
    flow = load_flow(default_flow_path())
    agents = build_default_agent_registry()
    initial_state = create_initial_state(
        "Refactor ai-dev-team-core into a data-driven multi-agent orchestration system.",
        overrides={
            "repository": {"path": "."},
            "coordination": {
                "parallel_development": True,
                "work_items": [
                    {"id": "engine", "description": "Implement the orchestration engine."},
                    {"id": "tests", "description": "Implement the orchestration test suite."},
                ],
            },
        },
    )
    final_state = Orchestrator(flow, agents).run(initial_state)
    print(json.dumps(final_state, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
