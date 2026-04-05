from __future__ import annotations

from typing import Any

from agents.base import Agent
from agents.discovery import discover_roles


def _scenario_entries(state: dict[str, Any], key: str) -> list[dict[str, Any]]:
    scenarios = state.get("scenarios", {})
    entries = scenarios.get(key, [])
    if isinstance(entries, list):
        return [entry for entry in entries if isinstance(entry, dict)]
    return []


def _scenario_for_revision(
    state: dict[str, Any],
    key: str,
    revision: int,
) -> dict[str, Any]:
    fallback: dict[str, Any] | None = None
    for entry in _scenario_entries(state, key):
        if entry.get("revision") == revision:
            return entry
        if entry.get("default"):
            fallback = entry
    return fallback or {}


def _support_request_for(state: dict[str, Any], requester: str) -> dict[str, Any] | None:
    completed_ids = set(state.get("meta", {}).get("completed_support_requests", []))
    for entry in _scenario_entries(state, "support_requests"):
        if entry.get("requested_by") != requester:
            continue
        request_id = str(entry.get("id", ""))
        if request_id and request_id in completed_ids:
            continue
        return {
            "id": request_id or f"{requester}-{entry.get('support_role', 'support')}",
            "pending": True,
            "requested_by": requester,
            "support_role": str(entry["support_role"]),
            "question": str(entry["question"]),
            "resume_step": str(entry.get("resume_step", state.get("meta", {}).get("current_step", ""))),
            "reason": str(entry.get("reason", "Additional specialist clarification is required.")),
        }
    return None


class CoordinatorAgent(Agent):
    def __init__(self) -> None:
        super().__init__("coordinator", {"coordination", "support_request"})

    def _run(self, state: dict[str, Any]) -> dict[str, Any]:
        step = str(state.get("meta", {}).get("current_step", ""))
        existing = state.get("coordination") or {}
        request = str(state.get("input", "")).strip()

        if step == "intake":
            repo_mode = existing.get("repo_mode")
            if not repo_mode:
                repo_mode = "existing" if state.get("repository", {}).get("path") else "greenfield"
            ui_heavy = bool(existing.get("ui_heavy")) or any(
                token in request.lower() for token in ("ui", "ux", "frontend", "screen", "accessibility")
            )
            return {
                "coordination": {
                    "status": "ready" if request else "blocked",
                    "repo_mode": repo_mode,
                    "ui_heavy": ui_heavy,
                    "parallel_development": bool(existing.get("parallel_development", False)),
                    "work_items": list(existing.get("work_items", [])),
                    "integration_owner": existing.get("integration_owner", "designated-developer"),
                    "support_resume_step": None,
                    "support_dispatch": None,
                    "final_summary": None,
                },
                "support_request": None,
            }

        if step == "plan-development":
            design = state.get("design") or {}
            work_items = list(existing.get("work_items", [])) or list(design.get("work_items", []))
            parallel_development = bool(existing.get("parallel_development")) or len(work_items) > 1
            if not work_items:
                work_items = [{"id": "core", "description": "Implement the approved design end to end."}]
            return {
                "coordination": {
                    "status": "development-planned",
                    "repo_mode": existing.get("repo_mode"),
                    "ui_heavy": bool(existing.get("ui_heavy")),
                    "parallel_development": parallel_development,
                    "work_items": work_items,
                    "integration_owner": "designated-developer",
                    "support_resume_step": existing.get("support_resume_step"),
                    "support_dispatch": None,
                    "final_summary": None,
                },
                "support_request": None,
            }

        if step == "support-approval":
            request_payload = state.get("support_request") or {}
            approved = request_payload.get("support_role") in {"explorer", "scout", "ux-ui-designer"}
            dispatch = {
                "approved": approved,
                "support_role": request_payload.get("support_role"),
                "resume_step": request_payload.get("resume_step"),
                "requested_by": request_payload.get("requested_by"),
                "question": request_payload.get("question"),
            }
            return {
                "coordination": {
                    "status": "support-approved" if approved else "support-rejected",
                    "repo_mode": existing.get("repo_mode"),
                    "ui_heavy": bool(existing.get("ui_heavy")),
                    "parallel_development": bool(existing.get("parallel_development")),
                    "work_items": list(existing.get("work_items", [])),
                    "integration_owner": existing.get("integration_owner", "designated-developer"),
                    "support_resume_step": request_payload.get("resume_step"),
                    "support_dispatch": dispatch,
                    "final_summary": existing.get("final_summary"),
                },
                "support_request": request_payload if approved else None,
            }

        if step == "support-finalize":
            return {
                "coordination": {
                    "status": "support-complete",
                    "repo_mode": existing.get("repo_mode"),
                    "ui_heavy": bool(existing.get("ui_heavy")),
                    "parallel_development": bool(existing.get("parallel_development")),
                    "work_items": list(existing.get("work_items", [])),
                    "integration_owner": existing.get("integration_owner", "designated-developer"),
                    "support_resume_step": existing.get("support_resume_step"),
                    "support_dispatch": None,
                    "final_summary": existing.get("final_summary"),
                },
                "support_request": None,
            }

        if step == "finalize":
            dod_review = state.get("dod_review") or {}
            development = state.get("development") or {}
            return {
                "coordination": {
                    "status": "done" if dod_review.get("approved") else "incomplete",
                    "repo_mode": existing.get("repo_mode"),
                    "ui_heavy": bool(existing.get("ui_heavy")),
                    "parallel_development": bool(existing.get("parallel_development")),
                    "work_items": list(existing.get("work_items", [])),
                    "integration_owner": existing.get("integration_owner", "designated-developer"),
                    "support_resume_step": existing.get("support_resume_step"),
                    "support_dispatch": None,
                    "final_summary": (
                        f"Delivered revision {development.get('revision', 0)} with acceptance confirmed."
                        if dod_review.get("approved")
                        else "Flow ended without satisfying Definition of Done."
                    ),
                },
                "support_request": None,
            }

        return {"coordination": existing, "support_request": state.get("support_request")}


class RequirementsEngineerAgent(Agent):
    def __init__(self) -> None:
        super().__init__("requirements-engineer", {"requirements", "support_request"})

    def _run(self, state: dict[str, Any]) -> dict[str, Any]:
        request = str(state.get("input", "")).strip()
        support_request = _support_request_for(state, "requirements-engineer")
        ui_heavy = bool((state.get("coordination") or {}).get("ui_heavy"))
        return {
            "requirements": {
                "ready": bool(request),
                "summary": request,
                "acceptance_criteria": [
                    "Flow definitions drive execution and branching.",
                    "All roles are preserved and role boundaries are enforced.",
                    "Agents collaborate only through shared state.",
                    "Review, testing, and DoD gates all return structured outcomes.",
                ],
                "constraints": [
                    "Coordinator stays read-only for implementation artifacts.",
                    "Support roles are coordinator-mediated.",
                ],
                "needs_user_input": False,
                "in_scope": [
                    "Flow-driven orchestration",
                    "Structured state transitions",
                    "Role-specific ownership boundaries",
                ],
                "out_of_scope": [
                    "Long-running cloud-hosted execution",
                ],
                "functional_requirements": [
                    "Persist phase outcomes in shared state.",
                    "Support reusable support-role dispatch through the coordinator.",
                ],
                "assumptions": [
                    "The skeleton is used primarily in GitHub Copilot in Visual Studio Code.",
                    "Codex remains a compatible secondary runtime.",
                ]
                if ui_heavy
                else [
                    "The skeleton is used primarily in GitHub Copilot in Visual Studio Code.",
                    "Codex remains a compatible secondary runtime.",
                ],
                "open_questions": [],
            },
            "support_request": support_request,
        }


class UXUIDesignerAgent(Agent):
    def __init__(self) -> None:
        super().__init__("ux-ui-designer", {"ux_ui"})

    def _run(self, state: dict[str, Any]) -> dict[str, Any]:
        request_payload = state.get("support_request") or {}
        ui_heavy = bool((state.get("coordination") or {}).get("ui_heavy"))
        guidance = []
        if ui_heavy or request_payload.get("support_role") == "ux-ui-designer":
            guidance = [
                "Keep role handoffs and agent choices readable in the IDE.",
                "Treat accessibility and interaction clarity as acceptance inputs when UI scope is material.",
            ]
        return {
            "ux_ui": {
                "status": "ready" if guidance else "skipped",
                "guidance": guidance,
                "requested_by": request_payload.get("requested_by"),
            }
        }


class ExplorerAgent(Agent):
    def __init__(self) -> None:
        super().__init__("explorer", {"analysis"})
        self._known_roles = [role.key for role in discover_roles()]

    def _run(self, state: dict[str, Any]) -> dict[str, Any]:
        request_payload = state.get("support_request") or {}
        repo_mode = (state.get("coordination") or {}).get("repo_mode")
        active = repo_mode == "existing" or request_payload.get("support_role") == "explorer"
        return {
            "analysis": {
                "status": "ready" if active else "skipped",
                "repository_roles": self._known_roles,
                "insights": [
                    "Repository contains existing runtime configs and tests that should be preserved during refactor.",
                    "Native Copilot agent profiles should align with the canonical flow and role contracts.",
                ]
                if active
                else [],
                "requested_by": request_payload.get("requested_by"),
            }
        }


class ScoutAgent(Agent):
    def __init__(self) -> None:
        super().__init__("scout", {"research"})

    def _run(self, state: dict[str, Any]) -> dict[str, Any]:
        request_payload = state.get("support_request") or {}
        active = request_payload.get("support_role") == "scout"
        question = str(request_payload.get("question") or "").strip()
        return {
            "research": {
                "status": "ready" if active else "skipped",
                "brief": [question] if active and question else [],
                "requested_by": request_payload.get("requested_by"),
                "verified_facts": [
                    "Fresh external evidence should be routed back through the coordinator into architecture or development."
                ]
                if active
                else [],
                "sources": [],
                "confidence": "medium" if active else None,
                "unknowns": [],
            }
        }


class ArchitectAgent(Agent):
    def __init__(self) -> None:
        super().__init__("architect", {"design", "support_request"})

    def _run(self, state: dict[str, Any]) -> dict[str, Any]:
        existing_design = state.get("design") or {}
        support_request = _support_request_for(state, "architect")
        work_items = list(existing_design.get("work_items", []))
        if not work_items:
            work_items = [
                {"id": "native-agents", "description": "Define native host agent roles and handoff behavior."},
                {"id": "validation", "description": "Keep schemas, prompts, and flow validation aligned."},
            ]
        return {
            "design": {
                "approved_for_build": bool((state.get("requirements") or {}).get("ready")),
                "architecture": [
                    "Treat Copilot VS Code custom agents as the primary execution surface.",
                    "Keep Codex compatible through the same role, prompt, and flow contracts.",
                    "Keep Python orchestration as a validation and test harness rather than the main runtime.",
                ],
                "non_functional_requirements": [
                    "Native handoffs must stay readable and role-bounded.",
                    "Flow and artifact behavior must remain deterministic in the validation harness.",
                ],
                "work_items": work_items,
                "module_boundaries": [
                    "Framework contract files remain canonical.",
                    "Native host agent files consume the canonical role and prompt contracts.",
                ],
                "interfaces": [
                    "Role outputs continue to satisfy the structured contracts.",
                    "The orchestrator trace records runtime metadata rather than provider backend metadata.",
                ],
                "data_flow": [
                    "coordinator -> requirements -> architect -> developer -> reviewer -> tester -> dod-reviewer",
                    "support roles are dispatched through coordinator approval and resume the requester.",
                ],
                "risks_and_tradeoffs": [
                    "Native host behavior is less directly testable than pure Python execution.",
                    "Removing provider backends reduces flexibility but sharply reduces maintenance burden.",
                ],
            },
            "support_request": support_request,
        }


class DeveloperAgent(Agent):
    def __init__(self) -> None:
        super().__init__("developer", {"development", "development_artifact", "support_request"})

    def _run(self, state: dict[str, Any]) -> dict[str, Any]:
        step = str(state.get("meta", {}).get("current_step", ""))
        support_request = _support_request_for(state, "developer")
        development = state.get("development") or {}

        if step == "parallel-development":
            work_item = state.get("meta", {}).get("current_parallel_item") or {}
            return {
                "development_artifact": {
                    "worker_id": work_item.get("id"),
                    "description": work_item.get("description"),
                    "status": "implemented",
                },
                "support_request": support_request,
            }

        revision = int(development.get("revision", 0)) + 1
        review = state.get("review") or {}
        test_results = state.get("test_results") or {}
        changes = [f"Prepared development revision {revision}."]
        if review and not review.get("approved", True):
            changes.append(f"Addressed review findings: {review.get('feedback', 'unspecified')}")
        if test_results and not test_results.get("passed", True):
            errors = test_results.get("errors") or ["unspecified test failure"]
            changes.append("Addressed failing tests: " + ", ".join(errors))

        worker_results = list(development.get("worker_results", []))
        if step == "integrate-development":
            changes.append("Integrated and stabilized worker results from parallel development.")
        return {
            "development": {
                "status": "implemented",
                "revision": revision,
                "strategy": "parallel" if worker_results else "sequential",
                "worker_results": worker_results,
                "changes": changes,
                "integration_owner": (state.get("coordination") or {}).get("integration_owner", "designated-developer"),
                "blockers": [],
                "rework_target": None,
            },
            "support_request": support_request,
        }


class ReviewerAgent(Agent):
    def __init__(self) -> None:
        super().__init__("reviewer", {"review", "support_request"})

    def _run(self, state: dict[str, Any]) -> dict[str, Any]:
        support_request = _support_request_for(state, "reviewer")
        revision = int((state.get("development") or {}).get("revision", 0))
        scenario = _scenario_for_revision(state, "review", revision)
        approved = bool(scenario.get("approved", revision > 0))
        return {
            "review": {
                "decision": "approved" if approved else "rework",
                "approved": approved,
                "feedback": str(
                    scenario.get("feedback", "Approved for testing." if approved else "Implementation requires rework.")
                ),
                "score": float(scenario.get("score", 0.94 if approved else 0.51)),
                "blocking_findings": list(scenario.get("blocking_findings", [] if approved else ["Reviewer requested changes."])),
                "rework_target": str(scenario.get("rework_target", "developer")),
                "residual_risks": list(scenario.get("residual_risks", [])),
            },
            "support_request": support_request,
        }


class TesterAgent(Agent):
    def __init__(self) -> None:
        super().__init__("tester", {"test_results", "support_request"})

    def _run(self, state: dict[str, Any]) -> dict[str, Any]:
        support_request = _support_request_for(state, "tester")
        revision = int((state.get("development") or {}).get("revision", 0))
        scenario = _scenario_for_revision(state, "test", revision)
        passed = bool(scenario.get("passed", revision > 0))
        errors = list(scenario.get("errors", [] if passed else ["Automated validation failed."]))
        return {
            "test_results": {
                "decision": "passed" if passed else "failed",
                "passed": passed,
                "errors": errors,
                "automated": bool(scenario.get("automated", True)),
                "rework_target": str(scenario.get("rework_target", "developer")),
            },
            "support_request": support_request,
        }


class DodReviewerAgent(Agent):
    def __init__(self) -> None:
        super().__init__("dod-reviewer", {"dod_review"})

    def _run(self, state: dict[str, Any]) -> dict[str, Any]:
        revision = int((state.get("development") or {}).get("revision", 0))
        scenario = _scenario_for_revision(state, "dod_review", revision)
        approved = bool(scenario.get("approved", True))
        return {
            "dod_review": {
                "decision": "accepted" if approved else "rework",
                "approved": approved,
                "feedback": str(
                    scenario.get(
                        "feedback",
                        "All functional and non-functional acceptance criteria are satisfied."
                        if approved
                        else "Definition of Done is not yet satisfied.",
                    )
                ),
                "blocking_findings": list(scenario.get("blocking_findings", [])),
                "rework_target": str(scenario.get("rework_target", "developer")),
            }
        }
