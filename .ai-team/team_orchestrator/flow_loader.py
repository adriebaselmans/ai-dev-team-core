from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_flow(path: str | Path) -> dict[str, Any]:
    flow_path = Path(path)
    with flow_path.open("r", encoding="utf-8") as handle:
        flow = yaml.safe_load(handle) or {}
    if not isinstance(flow, dict):
        raise ValueError(f"Expected a mapping flow definition in {flow_path}.")
    if "start_at" not in flow:
        raise ValueError(f"Flow {flow_path} must declare 'start_at'.")
    if "steps" not in flow or not isinstance(flow["steps"], dict):
        raise ValueError(f"Flow {flow_path} must declare a mapping of 'steps'.")
    return flow
