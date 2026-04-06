from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from agents.base import Agent
from state.factory import prepare_state
from state.merge import merge_state
from team_orchestrator.artifact_sync import ArtifactSynchronizer
from team_orchestrator.conditions import evaluate_condition, resolve_path, set_path
from team_orchestrator.logger import TraceLogger
from team_orchestrator.memory_sync import MemorySynchronizer
from team_orchestrator.prompts import RolePromptConfig, load_role_prompt_map, validate_role_prompt_map
from team_orchestrator.runtimes import (
    RoleRuntimeConfig,
    load_role_runtime_map,
    validate_role_runtime_map,
)


class Orchestrator:
    def __init__(
        self,
        flow: dict[str, Any],
        agents: Mapping[str, Agent],
        logger: TraceLogger | None = None,
        artifact_synchronizer: ArtifactSynchronizer | None = None,
        memory_synchronizer: MemorySynchronizer | None = None,
    ) -> None:
        self.flow = deepcopy(flow)
        self.agents = dict(agents)
        self.logger = logger or TraceLogger()
        self.artifact_synchronizer = artifact_synchronizer or ArtifactSynchronizer()
        self.memory_synchronizer = memory_synchronizer or MemorySynchronizer()
        self.role_runtimes = load_role_runtime_map()
        self.role_prompts = load_role_prompt_map()
        validate_role_runtime_map(self.role_runtimes, list(self.agents))
        validate_role_prompt_map(self.role_prompts, list(self.agents))
        self._validate_flow()

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        working_state = prepare_state(
            state,
            role_keys=list(self.agents),
            flow_name=str(self.flow.get("name", "unnamed-flow")),
        )
        working_state["meta"]["role_runtimes"] = {
            role_key: config.as_dict() for role_key, config in self.role_runtimes.items()
        }
        working_state["meta"]["role_prompts"] = {
            role_key: config.as_dict() for role_key, config in self.role_prompts.items()
        }
        current_step = str(working_state["meta"].get("current_step") or self.flow["start_at"])
        working_state["meta"]["visit_counts"][current_step] = int(
            working_state["meta"]["visit_counts"].get(current_step, 0)
        ) + 1

        while True:
            step = self.flow["steps"][current_step]
            working_state["meta"]["current_step"] = current_step

            if step.get("kind") == "terminal" or step.get("terminal"):
                return self._terminate(
                    working_state,
                    reason=str(step.get("reason", "completed")),
                    terminal_step=current_step,
                )

            if step.get("kind") == "decision":
                next_step = self._resolve_next_step(step, working_state)
                self._record_transition(working_state, current_step, "decision", {}, next_step, f"[DECISION] {current_step} -> {next_step}")
            elif step.get("kind") == "parallel-agent":
                role_key = str(step["agent"])
                next_step = str(step["next"])
                working_state = self._run_parallel_step(working_state, current_step, role_key, step)
                self._record_transition(
                    working_state,
                    current_step,
                    role_key,
                    {},
                    next_step,
                    f"[{role_key.upper()}] parallel={len(resolve_path(working_state, step['items_path'], []) or [])}",
                )
            elif step.get("kind") == "dynamic-agent":
                role_key = str(resolve_path(working_state, step["agent_path"]))
                agent = self.agents[role_key]
                update = agent.run(working_state)
                working_state = merge_state(working_state, update)
                self.artifact_synchronizer.sync(working_state, role_key=role_key, step_name=current_step)
                self.memory_synchronizer.sync(working_state, role_key=role_key, step_name=current_step)
                next_step = self._resolve_next_step(step, working_state)
                self._record_transition(working_state, current_step, role_key, update, next_step, self.logger.log(role_key, update))
            else:
                role_key = str(step["agent"])
                agent = self.agents[role_key]
                update = agent.run(working_state)
                support_request_before = working_state.get("support_request") or {}
                working_state = merge_state(working_state, update)
                if current_step == "support-finalize" and support_request_before.get("id"):
                    completed = list(working_state["meta"].get("completed_support_requests", []))
                    completed.append(str(support_request_before["id"]))
                    working_state["meta"]["completed_support_requests"] = completed
                self.artifact_synchronizer.sync(working_state, role_key=role_key, step_name=current_step)
                self.memory_synchronizer.sync(working_state, role_key=role_key, step_name=current_step)
                next_step = self._resolve_next_step(step, working_state)
                self._record_transition(working_state, current_step, role_key, update, next_step, self.logger.log(role_key, update))

            working_state["meta"]["executed_steps"] += 1
            if working_state["meta"]["executed_steps"] >= working_state["meta"]["max_steps"]:
                return self._terminate(
                    working_state,
                    reason=f"Reached max_steps={working_state['meta']['max_steps']}.",
                    terminal_step=current_step,
                )

            next_step_spec = self.flow["steps"].get(next_step, {})
            if next_step in working_state["meta"]["step_history"] and next_step_spec.get("counts_as_iteration"):
                working_state["meta"]["iteration"] += 1
                if working_state["meta"]["iteration"] > working_state["meta"]["max_iterations"]:
                    return self._terminate(
                        working_state,
                        reason=f"Reached max_iterations={working_state['meta']['max_iterations']}.",
                        terminal_step=current_step,
                    )

            visits = working_state["meta"]["visit_counts"]
            visits[next_step] = int(visits.get(next_step, 0)) + 1
            if visits[next_step] > working_state["meta"]["max_step_visits"]:
                return self._terminate(
                    working_state,
                    reason=(
                        f"Step '{next_step}' exceeded max_step_visits="
                        f"{working_state['meta']['max_step_visits']}."
                    ),
                    terminal_step=current_step,
                )

            current_step = next_step

    def _validate_flow(self) -> None:
        if "start_at" not in self.flow:
            raise ValueError("Flow must declare 'start_at'.")
        if "steps" not in self.flow or not isinstance(self.flow["steps"], dict):
            raise ValueError("Flow must declare a mapping of 'steps'.")
        if self.flow["start_at"] not in self.flow["steps"]:
            raise ValueError(f"Unknown start step '{self.flow['start_at']}'.")
        for step_name, step in self.flow["steps"].items():
            if not isinstance(step, dict):
                raise ValueError(f"Step '{step_name}' must be a mapping.")
            kind = step.get("kind", "agent")
            if kind == "terminal" or step.get("terminal"):
                continue
            if kind == "decision":
                continue
            if kind == "dynamic-agent":
                continue
            role_key = step.get("agent")
            if role_key not in self.agents:
                raise KeyError(f"Step '{step_name}' references unknown agent '{role_key}'.")

    def _run_parallel_step(
        self,
        state: dict[str, Any],
        step_name: str,
        role_key: str,
        step: dict[str, Any],
    ) -> dict[str, Any]:
        agent = self.agents[role_key]
        items = resolve_path(state, step["items_path"], [])
        if not isinstance(items, list):
            raise ValueError(f"Parallel step '{step_name}' expected list at {step['items_path']}.")
        collected: list[Any] = []
        updated_state = state
        for item in items:
            snapshot = merge_state(
                updated_state,
                {
                    "meta": {
                        "current_step": step_name,
                        "current_parallel_item": item,
                    }
                },
            )
            update = agent.run(snapshot)
            collected.append(update.get(step["collect_field"]))
            log_line = self.logger.log(role_key, update)
            updated_state["trace"].append(
                {
                    "step": step_name,
                    "role": role_key,
                    "runtime": self._runtime_payload(role_key),
                    "prompt": self._prompt_payload(role_key),
                    "parallel_item": deepcopy(item),
                    "update": deepcopy(update),
                    "next_step": step["next"],
                    "log": log_line,
                }
            )
        set_path(updated_state, step["store_path"], collected)
        return updated_state

    def _resolve_next_step(self, step: dict[str, Any], state: dict[str, Any]) -> str:
        if "next" in step:
            return str(step["next"])
        if "next_path" in step:
            value = resolve_path(state, step["next_path"])
            if not isinstance(value, str):
                raise ValueError(f"Expected string at next_path '{step['next_path']}'.")
            return value
        default_step: str | None = None
        for route in step.get("routes", []):
            if "when" in route and evaluate_condition(route["when"], state):
                return str(route["next"])
            if "default" in route:
                default_step = str(route["default"])
            if "next_path" in route and "when" not in route:
                value = resolve_path(state, route["next_path"])
                if not isinstance(value, str):
                    raise ValueError(f"Expected string at next_path '{route['next_path']}'.")
                default_step = value
        if default_step is not None:
            return default_step
        raise ValueError(f"Unable to resolve next step from step {step}.")

    def _record_transition(
        self,
        state: dict[str, Any],
        step_name: str,
        role_key: str,
        update: dict[str, Any],
        next_step: str,
        log_line: str,
    ) -> None:
        state["trace"].append(
            {
                "step": step_name,
                "role": role_key,
                "runtime": self._runtime_payload(role_key),
                "prompt": self._prompt_payload(role_key),
                "update": deepcopy(update),
                "next_step": next_step,
                "log": log_line,
            }
        )
        state["meta"]["step_history"].append(step_name)
        state["meta"]["last_role"] = role_key
        state["meta"]["last_next_step"] = next_step

    def _terminate(
        self,
        state: dict[str, Any],
        *,
        reason: str,
        terminal_step: str,
    ) -> dict[str, Any]:
        state["meta"]["terminated"] = True
        state["meta"]["termination_reason"] = reason
        state["meta"]["current_step"] = terminal_step
        state["meta"]["completed"] = terminal_step == "done"
        if terminal_step == "done":
            self.artifact_synchronizer.sync(state, role_key="coordinator", step_name="finalize")
        return state

    def _runtime_payload(self, role_key: str) -> dict[str, Any] | None:
        config: RoleRuntimeConfig | None = self.role_runtimes.get(role_key)
        if config is None:
            return None
        return config.as_dict()

    def _prompt_payload(self, role_key: str) -> dict[str, Any] | None:
        config: RolePromptConfig | None = self.role_prompts.get(role_key)
        if config is None:
            return None
        return config.as_dict()
