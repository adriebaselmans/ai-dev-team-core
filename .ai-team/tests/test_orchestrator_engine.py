from __future__ import annotations

from agents.registry import build_default_agent_registry
from flows import default_flow_path
from state.factory import create_initial_state
from team_orchestrator.engine import Orchestrator
from team_orchestrator.flow_loader import load_flow


def build_runtime() -> Orchestrator:
    return Orchestrator(load_flow(default_flow_path()), build_default_agent_registry())


def test_full_flow_executes_to_done_with_parallel_development() -> None:
    orchestrator = build_runtime()
    final_state = orchestrator.run(
        create_initial_state(
            "Refactor the system into a flow-driven orchestrator.",
            overrides={
                "repository": {"path": "."},
                "coordination": {
                    "parallel_development": True,
                    "work_items": [
                        {"id": "engine", "description": "Implement the engine."},
                        {"id": "tests", "description": "Implement the tests."},
                    ],
                },
            },
        )
    )

    steps = [entry["step"] for entry in final_state["trace"]]
    assert final_state["meta"]["completed"] is True
    assert "initial-exploration" in steps
    assert "parallel-development" in steps
    assert "integrate-development" in steps
    assert "dod-review" in steps
    assert len(final_state["development"]["worker_results"]) == 2
    assert final_state["dod_review"]["approved"] is True


def test_review_rejection_triggers_rework_loop() -> None:
    orchestrator = build_runtime()
    final_state = orchestrator.run(
        create_initial_state(
            "Refactor with one review rejection first.",
            overrides={
                "scenarios": {
                    "review": [
                        {"revision": 1, "approved": False, "score": 0.41, "feedback": "Missing loop handling."},
                        {"revision": 2, "approved": True, "score": 0.93, "feedback": "Ready for testing."},
                    ]
                }
            },
        )
    )

    review_steps = [entry for entry in final_state["trace"] if entry["step"] == "review"]
    development_steps = [
        entry for entry in final_state["trace"] if entry["step"] in {"development", "integrate-development"}
    ]
    assert len(review_steps) == 2
    assert len(development_steps) == 2
    assert final_state["development"]["revision"] == 2


def test_test_failure_triggers_retry() -> None:
    orchestrator = build_runtime()
    final_state = orchestrator.run(
        create_initial_state(
            "Refactor with one failing validation cycle.",
            overrides={
                "scenarios": {
                    "test": [
                        {"revision": 1, "passed": False, "errors": ["Acceptance suite failed."]},
                        {"revision": 2, "passed": True, "errors": []},
                    ]
                }
            },
        )
    )

    testing_steps = [entry for entry in final_state["trace"] if entry["step"] == "testing"]
    assert len(testing_steps) == 2
    assert final_state["test_results"]["passed"] is True
    assert final_state["development"]["revision"] == 2


def test_dod_failure_can_route_back_to_architecture() -> None:
    orchestrator = build_runtime()
    final_state = orchestrator.run(
        create_initial_state(
            "Refactor with one DoD failure.",
            overrides={
                "scenarios": {
                    "dod_review": [
                        {
                            "revision": 1,
                            "approved": False,
                            "feedback": "A non-functional requirement is not met.",
                            "rework_target": "architect",
                        },
                        {"revision": 2, "approved": True},
                    ]
                }
            },
        )
    )

    architecture_steps = [entry for entry in final_state["trace"] if entry["step"] == "architecture"]
    assert len(architecture_steps) == 2
    assert final_state["dod_review"]["approved"] is True


def test_support_request_is_coordinator_mediated_and_resumes_requester() -> None:
    orchestrator = build_runtime()
    final_state = orchestrator.run(
        create_initial_state(
            "Refactor with UI ambiguity during development.",
            overrides={
                "coordination": {"ui_heavy": True},
                "scenarios": {
                    "support_requests": [
                        {
                            "id": "dev-ui-clarification",
                            "requested_by": "developer",
                            "support_role": "ux-ui-designer",
                            "question": "Clarify the developer-facing UI expectations.",
                            "resume_step": "development",
                        }
                    ]
                },
            },
        )
    )

    steps = [entry["step"] for entry in final_state["trace"]]
    roles = [entry["role"] for entry in final_state["trace"]]
    assert "support-approval" in steps
    assert "support-finalize" in steps
    assert "ux-ui-designer" in roles
    assert final_state["meta"]["completed"] is True
    assert "dev-ui-clarification" in final_state["meta"]["completed_support_requests"]


def test_max_iterations_terminates_when_reviewer_always_rejects() -> None:
    orchestrator = build_runtime()
    final_state = orchestrator.run(
        create_initial_state(
            "Refactor with a permanently failing review gate.",
            max_iterations=2,
            overrides={
                "scenarios": {
                    "review": [
                        {"default": True, "approved": False, "score": 0.2, "feedback": "Still not good enough."}
                    ]
                }
            },
        )
    )

    assert final_state["meta"]["completed"] is False
    assert final_state["meta"]["terminated"] is True
    assert final_state["meta"]["termination_reason"] == "Reached max_iterations=2."


def test_trace_logging_is_readable() -> None:
    orchestrator = build_runtime()
    final_state = orchestrator.run(create_initial_state("Refactor trace logging."))

    logs = [entry["log"] for entry in final_state["trace"]]
    assert any(log.startswith("[REVIEWER] approved=") for log in logs)
    assert any(log.startswith("[TESTER] passed=") for log in logs)
    assert any(log.startswith("[DOD-REVIEWER] approved=") for log in logs)


def test_intake_builds_task_brief_and_compact_mode_for_small_low_risk_work() -> None:
    orchestrator = build_runtime()
    final_state = orchestrator.run(create_initial_state("Rename a runtime helper."))

    task_brief = final_state["task_brief"]
    coordination = final_state["coordination"]

    assert task_brief["objective"] == "Rename a runtime helper."
    assert task_brief["mode"] == "compact"
    assert task_brief["task_size"] == "small"
    assert coordination["mode"] == "compact"
    assert coordination["risk_level"] == "low"


def test_freshness_sensitive_task_auto_requests_scout_support() -> None:
    orchestrator = build_runtime()
    final_state = orchestrator.run(
        create_initial_state("Update the Copilot model mapping to the latest supported version.")
    )

    support_steps = [entry for entry in final_state["trace"] if entry["step"] == "support-approval"]
    scout_steps = [entry for entry in final_state["trace"] if entry["role"] == "scout"]

    assert support_steps
    assert scout_steps
    assert "architect-scout-auto" in final_state["meta"]["completed_support_requests"]


def test_compact_mode_avoids_parallel_development_for_small_tasks() -> None:
    orchestrator = build_runtime()
    final_state = orchestrator.run(
        create_initial_state(
            "Rename a runtime helper.",
            overrides={
                "coordination": {
                    "parallel_development": True,
                    "work_items": [
                        {"id": "one", "description": "Rename the helper."},
                        {"id": "two", "description": "Adjust the tests."},
                    ]
                }
            },
        )
    )

    steps = [entry["step"] for entry in final_state["trace"]]
    assert "parallel-development" not in steps
    assert final_state["coordination"]["parallel_development"] is False


def test_development_records_compact_validation_evidence() -> None:
    orchestrator = build_runtime()
    final_state = orchestrator.run(create_initial_state("Rename a runtime helper."))

    attempts = final_state["development"]["validation_attempts"]
    assert attempts
    assert attempts[0]["status"] == "passed"
    assert attempts[0]["inspected_output"] is False


def test_failed_test_validation_marks_output_as_inspected() -> None:
    orchestrator = build_runtime()
    final_state = orchestrator.run(
        create_initial_state(
            "Refactor with one failing validation cycle.",
            overrides={
                "scenarios": {
                    "test": [
                        {"revision": 1, "passed": False, "errors": ["Acceptance suite failed."]},
                        {"revision": 2, "passed": True, "errors": []},
                    ]
                }
            },
        )
    )

    attempts = final_state["test_results"]["validation_attempts"]
    assert attempts
    assert attempts[0]["status"] == "passed"
    assert attempts[0]["inspected_output"] is False


def test_version_sensitive_task_records_technology_choices_and_alignment() -> None:
    orchestrator = build_runtime()
    final_state = orchestrator.run(create_initial_state("Build a 3D game in .NET 10 with a modern engine."))

    assert final_state["design"]["technology_choices"]
    assert final_state["development"]["technology_alignment"]
