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


def _normalize_scope_items(request: str) -> list[str]:
    lowered = request.lower()
    items: list[str] = []
    if any(token in lowered for token in ("api", "endpoint", "rest", "http")):
        items.append("API and integration behavior")
    if any(token in lowered for token in ("ui", "ux", "frontend", "screen", "form", "accessibility")):
        items.append("User-facing interaction and accessibility")
    if any(token in lowered for token in ("test", "validation", "qa", "acceptance")):
        items.append("Automated validation and acceptance coverage")
    if not items:
        items.append("Requested repository change")
    return items


def _build_task_brief(state: dict[str, Any], request: str, repo_mode: str, ui_heavy: bool) -> dict[str, Any]:
    lowered = request.lower()
    word_count = len(request.split())
    risk_terms = ("auth", "security", "payment", "database", "migration", "release", "deploy", "production")
    freshness_terms = (
        "latest",
        "recent",
        "current",
        "version",
        "dependency",
        "sdk",
        "api",
        "copilot",
        "instruction-compatible host",
        "claude",
        "openai",
        "github",
    )
    repo_grounding = repo_mode == "existing" or bool(state.get("repository", {}).get("path"))
    needs_freshness = any(term in lowered for term in freshness_terms)
    risk_level = "high" if any(term in lowered for term in risk_terms) else "medium" if needs_freshness else "low"
    task_size = "small" if word_count <= 24 and risk_level == "low" else "medium" if word_count <= 80 else "large"
    mode = "compact" if task_size == "small" and not repo_grounding and not needs_freshness else "full"
    acceptance_signals = [
        "Required phases complete with structured outputs.",
        "Review, testing, and DoD gates pass.",
    ]
    if ui_heavy:
        acceptance_signals.append("UI and accessibility-sensitive expectations remain explicit.")
    return {
        "objective": request,
        "scope": _normalize_scope_items(request),
        "constraints": [
            "Follow the coordinator-mediated workflow.",
            "Keep role boundaries and owned write scopes intact.",
        ],
        "acceptance_signals": acceptance_signals,
        "repo_mode": repo_mode,
        "task_size": task_size,
        "risk_level": risk_level,
        "mode": mode,
        "needs_repo_grounding": repo_grounding,
        "needs_freshness_check": needs_freshness,
        "open_questions": [],
    }


def _inferred_support_request(state: dict[str, Any], requester: str) -> dict[str, Any] | None:
    coordination = state.get("coordination") or {}
    task_brief = state.get("task_brief") or {}
    completed_ids = set(state.get("meta", {}).get("completed_support_requests", []))

    inference = _AUTO_SUPPORT_RULES.get(requester)
    if inference is None:
        return None
    spec = inference(task_brief, coordination)
    if spec is None:
        return None
    request_id, support_role, question = spec
    if request_id in completed_ids:
        return None
    return {
        "id": request_id,
        "pending": True,
        "requested_by": requester,
        "support_role": support_role,
        "question": question,
        "resume_step": str(state.get("meta", {}).get("current_step", "")),
        "reason": "Automatically requested because the task brief indicates the downstream role would otherwise need broad additional context.",
    }


def _auto_support_for_architect(
    task_brief: dict[str, Any], coordination: dict[str, Any]
) -> tuple[str, str, str] | None:
    if task_brief.get("needs_freshness_check"):
        return (
            "architect-scout-auto",
            "scout",
            "Verify external versions, current guidance, or recent changes that could affect the design.",
        )
    return None


def _auto_support_for_developer(
    task_brief: dict[str, Any], coordination: dict[str, Any]
) -> tuple[str, str, str] | None:
    if task_brief.get("needs_freshness_check"):
        return (
            "developer-scout-auto",
            "scout",
            "Verify implementation-sensitive external behavior, versions, or recent changes before coding.",
        )
    return None


def _auto_support_for_requirements(
    task_brief: dict[str, Any], coordination: dict[str, Any]
) -> tuple[str, str, str] | None:
    if coordination.get("ui_heavy"):
        return (
            "requirements-ux-auto",
            "ux-ui-designer",
            "Clarify important user flows, states, and accessibility expectations.",
        )
    return None


_AUTO_SUPPORT_RULES = {
    "architect": _auto_support_for_architect,
    "developer": _auto_support_for_developer,
    "requirements-engineer": _auto_support_for_requirements,
}


def _effective_support_request(state: dict[str, Any], requester: str) -> dict[str, Any] | None:
    explicit = _support_request_for(state, requester)
    if explicit is not None:
        return explicit
    return _inferred_support_request(state, requester)


def _compact_validation_attempt(
    *,
    kind: str,
    command: str,
    status: str,
    inspected_output: bool,
    summary: str = "",
) -> dict[str, Any]:
    return {
        "kind": kind,
        "command": command,
        "status": status,
        "inspected_output": inspected_output,
        "summary": summary,
    }


def _side_effect_assessment(
    *,
    scope: str,
    foreseeable_side_effects: list[str] | None = None,
    mitigations: list[str] | None = None,
    validation_plan: list[str] | None = None,
    decision: str = "safe_to_proceed",
) -> dict[str, Any]:
    return {
        "checked": True,
        "decision": decision,
        "scope": scope,
        "foreseeable_side_effects": foreseeable_side_effects or [],
        "mitigations": mitigations or ["Keep changes within the approved scope and owned write boundaries."],
        "validation_plan": validation_plan or ["Run the cheapest deterministic validation that can reveal regressions before handoff."],
    }


def _default_technology_choices(state: dict[str, Any]) -> list[dict[str, Any]]:
    request = str((state.get("task_brief") or {}).get("objective") or state.get("input", "")).lower()
    choices: list[dict[str, Any]] = []
    if ".net 10" in request or "dotnet 10" in request or ".net" in request:
        choices.append(
            {
                "name": ".NET",
                "category": "runtime",
                "version": "10",
                "target_runtime": ".NET 10",
                "rationale": "Runtime target selected during architecture and must remain consistent through implementation.",
                "source": "architectural decision",
                "verified_at": None,
                "status": "inherited",
            }
        )
    if "engine" in request or "game" in request:
        choices.append(
            {
                "name": "Chosen game engine",
                "category": "engine",
                "version": "to-be-verified",
                "target_runtime": next((choice["target_runtime"] for choice in choices if choice["category"] == "runtime"), None),
                "rationale": "Engine choice must be preserved explicitly so downstream implementation does not fall back to stale examples.",
                "source": "architectural decision",
                "verified_at": None,
                "status": "unknown",
            }
        )
    return choices


_COORDINATION_INHERITED_FIELDS: tuple[str, ...] = (
    "repo_mode",
    "ui_heavy",
    "mode",
    "task_size",
    "risk_level",
    "needs_repo_grounding",
    "needs_freshness_check",
    "parallel_development",
    "work_items",
    "integration_owner",
    "support_resume_step",
    "support_dispatch",
    "final_summary",
)

_COORDINATION_BOOL_FIELDS: frozenset[str] = frozenset(
    {"ui_heavy", "needs_repo_grounding", "needs_freshness_check", "parallel_development"}
)
_COORDINATION_LIST_FIELDS: frozenset[str] = frozenset({"work_items"})


def _coordination_payload(
    existing: dict[str, Any],
    *,
    status: str,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a coordination dict by inheriting from ``existing`` and applying overrides.

    Centralises the field list so each step in CoordinatorAgent only declares
    what it actually changes instead of re-copying every key.
    """
    overrides = overrides or {}
    payload: dict[str, Any] = {"status": status}
    for field in _COORDINATION_INHERITED_FIELDS:
        if field in overrides:
            payload[field] = overrides[field]
        elif field in _COORDINATION_BOOL_FIELDS:
            payload[field] = bool(existing.get(field))
        elif field in _COORDINATION_LIST_FIELDS:
            payload[field] = list(existing.get(field, []))
        elif field == "integration_owner":
            payload[field] = existing.get(field, "designated-developer")
        else:
            payload[field] = existing.get(field)
    return payload


class CoordinatorAgent(Agent):
    def __init__(self) -> None:
        super().__init__("coordinator", {"coordination", "support_request", "task_brief"})

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
            task_brief = _build_task_brief(state, request, repo_mode, ui_heavy)
            return {
                "coordination": _coordination_payload(
                    existing,
                    status="ready" if request else "blocked",
                    overrides={
                        "repo_mode": repo_mode,
                        "ui_heavy": ui_heavy,
                        "mode": task_brief["mode"],
                        "task_size": task_brief["task_size"],
                        "risk_level": task_brief["risk_level"],
                        "needs_repo_grounding": task_brief["needs_repo_grounding"],
                        "needs_freshness_check": task_brief["needs_freshness_check"],
                        "parallel_development": bool(existing.get("parallel_development", False)),
                        "work_items": list(existing.get("work_items", [])),
                        "integration_owner": existing.get("integration_owner", "designated-developer"),
                        "support_resume_step": None,
                        "support_dispatch": None,
                        "final_summary": None,
                    },
                ),
                "task_brief": task_brief,
                "support_request": None,
            }

        if step == "plan-development":
            design = state.get("design") or {}
            task_brief = state.get("task_brief") or {}
            work_items = list(existing.get("work_items", [])) or list(design.get("work_items", []))
            compact_mode = task_brief.get("mode") == "compact"
            parallel_development = (bool(existing.get("parallel_development")) or len(work_items) > 1) and not compact_mode
            if not work_items:
                work_items = [{"id": "core", "description": "Implement the approved design end to end."}]
            return {
                "coordination": _coordination_payload(
                    existing,
                    status="development-planned",
                    overrides={
                        "parallel_development": parallel_development,
                        "work_items": work_items,
                        "integration_owner": "designated-developer",
                        "support_dispatch": None,
                        "final_summary": None,
                    },
                ),
                "task_brief": state.get("task_brief"),
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
                "coordination": _coordination_payload(
                    existing,
                    status="support-approved" if approved else "support-rejected",
                    overrides={
                        "support_resume_step": request_payload.get("resume_step"),
                        "support_dispatch": dispatch,
                    },
                ),
                "task_brief": state.get("task_brief"),
                "support_request": request_payload if approved else None,
            }

        if step == "support-finalize":
            return {
                "coordination": _coordination_payload(
                    existing,
                    status="support-complete",
                    overrides={"support_dispatch": None},
                ),
                "task_brief": state.get("task_brief"),
                "support_request": None,
            }

        if step == "finalize":
            dod_review = state.get("dod_review") or {}
            development = state.get("development") or {}
            final_summary = (
                f"Delivered revision {development.get('revision', 0)} with acceptance confirmed."
                if dod_review.get("approved")
                else "Flow ended without satisfying Definition of Done."
            )
            return {
                "coordination": _coordination_payload(
                    existing,
                    status="done" if dod_review.get("approved") else "incomplete",
                    overrides={
                        "support_dispatch": None,
                        "final_summary": final_summary,
                    },
                ),
                "task_brief": state.get("task_brief"),
                "support_request": None,
            }

        return {
            "coordination": existing,
            "task_brief": state.get("task_brief"),
            "support_request": state.get("support_request"),
        }


class RequirementsEngineerAgent(Agent):
    def __init__(self) -> None:
        super().__init__("requirements-engineer", {"requirements", "support_request"})

    def _run(self, state: dict[str, Any]) -> dict[str, Any]:
        task_brief = state.get("task_brief") or {}
        request = str(task_brief.get("objective") or state.get("input", "")).strip()
        support_request = _effective_support_request(state, "requirements-engineer")
        compact = (state.get("coordination") or {}).get("mode") == "compact"
        return {
            "requirements": {
                "ready": bool(request),
                "summary": request,
                "acceptance_criteria": task_brief.get("acceptance_signals")
                or [
                    "Flow definitions drive execution and branching.",
                    "All roles are preserved and role boundaries are enforced.",
                    "Agents collaborate only through shared state.",
                    "Review, testing, and DoD gates all return structured outcomes.",
                ],
                "constraints": [
                    "Coordinator stays read-only for implementation artifacts.",
                    "Support roles are coordinator-mediated.",
                    *list(task_brief.get("constraints", [])),
                ],
                "needs_user_input": False,
                "in_scope": list(task_brief.get("scope", []))
                or [
                    "Flow-driven orchestration",
                    "Structured state transitions",
                    "Role-specific ownership boundaries",
                ],
                "out_of_scope": [
                    "Long-running cloud-hosted execution",
                    *([] if compact else ["Unnecessary framework expansion beyond the active request"]),
                ],
                "functional_requirements": ([
                    "Keep the implementation path compact and phase outputs concise."
                ] if compact else []) + [
                    "Persist phase outcomes in shared state.",
                    "Support reusable support-role dispatch through the coordinator.",
                ],
                "assumptions": [
                    "The skeleton is used with native project-agent hosts when available.",
                    "Instruction-compatible hosts follow the same framework contract.",
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
        architecture = [
            "Repository contains existing runtime configs and tests that should be preserved during refactor.",
        ] if active else []
        conventions = [
            "Native Copilot agent profiles should align with the canonical flow and role contracts.",
        ] if active else []
        context = [
            "Repository role registry is discoverable and should be used for role-aware changes.",
        ] if active else []
        incidents: list[str] = []
        decisions: list[str] = []
        return {
            "analysis": {
                "status": "ready" if active else "skipped",
                "repository_roles": self._known_roles if active else [],
                "insights": [*architecture, *conventions, *context, *decisions, *incidents],
                "architecture": architecture,
                "conventions": conventions,
                "context": context,
                "decisions": decisions,
                "incidents": incidents,
                "side_effect_assessment": _side_effect_assessment(
                    scope="repository exploration and memory handoff",
                    foreseeable_side_effects=[
                        "Repository findings could become stale or over-broad if not tied to evidence and revision context.",
                    ] if active else [],
                    mitigations=[
                        "Keep exploration compact, evidence-based, and isolated to wiki memory when memory persistence is enabled.",
                    ] if active else ["No repository analysis was performed."],
                    validation_plan=[
                        "Write only repository knowledge artifacts and category pages in bootstrapped project memory.",
                    ] if active else ["No validation needed for skipped exploration."],
                ),
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
        task_brief = state.get("task_brief") or {}
        support_request = _effective_support_request(state, "architect")
        work_items = list(existing_design.get("work_items", []))
        if not work_items:
            work_items = [
                {"id": "primary-change", "description": str(task_brief.get("objective") or "Implement the requested change safely.")},
            ]
            if (state.get("coordination") or {}).get("mode") != "compact":
                work_items.append({"id": "validation", "description": "Keep schemas, prompts, flow validation, and handoffs aligned."})
        compact = (state.get("coordination") or {}).get("mode") == "compact"
        return {
            "design": {
                "approved_for_build": bool((state.get("requirements") or {}).get("ready")),
                "architecture": [
                    "Use the coordinator-owned task brief as the compact handoff contract for downstream roles.",
                    "Keep support work isolated through explorer and scout when extra repository or external context is needed.",
                ] + ([] if compact else [
                    "Treat native project-agent profiles as the preferred execution surface.",
                    "Keep instruction-compatible hosts aligned through the same role, prompt, and flow contracts.",
                    "Keep Python orchestration as a validation and test harness rather than the main runtime.",
                ]),
                "non_functional_requirements": (
                    ["Keep handoffs concise and role-bounded."] if compact else []
                ) + [
                    "Native handoffs must stay readable and role-bounded.",
                    "Flow and artifact behavior must remain deterministic in the validation harness.",
                ],
                "work_items": work_items,
                "module_boundaries": [
                    "Framework contract files remain canonical.",
                    "Native host agent files consume the canonical role and prompt contracts.",
                ],
                "interfaces": (
                    ["Downstream roles consume task_brief plus owned upstream artifacts by default."] if compact else []
                ) + [
                    "Role outputs continue to satisfy the structured contracts.",
                    "The orchestrator trace records runtime metadata rather than provider backend metadata.",
                ],
                "data_flow": [
                    "coordinator -> requirements -> architect -> developer -> reviewer -> tester -> dod-reviewer",
                    "support roles are dispatched through coordinator approval and resume the requester.",
                ],
                "risks_and_tradeoffs": [
                    "Native host behavior is less directly testable than pure Python execution.",
                    "Compact mode reduces token usage but depends on coordinator classification staying conservative.",
                ] + (
                    []
                    if compact
                    else ["Removing provider backends reduces flexibility but sharply reduces maintenance burden."]
                ),
                "technology_choices": list(existing_design.get("technology_choices", [])) or _default_technology_choices(state),
                "side_effect_assessment": _side_effect_assessment(
                    scope="architecture plan for requested change",
                    foreseeable_side_effects=[
                        "Flow, prompt, schema, or runtime contract changes can affect downstream specialist behavior.",
                        "Compact handoffs can hide required context if phase classification is wrong.",
                    ],
                    mitigations=[
                        "Keep module boundaries explicit and route structural concerns back through architecture.",
                        "Define validation expectations before development begins.",
                    ],
                    validation_plan=[
                        "Developer must run the relevant compile, typecheck, or test validation before review.",
                        "Reviewer and tester must verify side-effect assessment evidence before approval.",
                    ],
                ),
            },
            "support_request": support_request,
        }


class DeveloperAgent(Agent):
    def __init__(self) -> None:
        super().__init__("developer", {"development", "development_artifact", "support_request"})

    def _run(self, state: dict[str, Any]) -> dict[str, Any]:
        step = str(state.get("meta", {}).get("current_step", ""))
        task_brief = state.get("task_brief") or {}
        support_request = _effective_support_request(state, "developer")
        development = state.get("development") or {}

        if step == "parallel-development":
            work_item = state.get("meta", {}).get("current_parallel_item") or {}
            return {
                "development_artifact": {
                    "worker_id": work_item.get("id"),
                    "description": work_item.get("description"),
                    "status": "implemented",
                    "side_effect_assessment": _side_effect_assessment(
                        scope="parallel development worker item",
                        foreseeable_side_effects=["Worker output can conflict with adjacent parallel changes during integration."],
                        mitigations=["Keep worker changes bounded to the assigned work item and require integration stabilization."],
                        validation_plan=["Integration developer must verify combined side effects before review."],
                    ),
                },
                "support_request": support_request,
            }

        revision = int(development.get("revision", 0)) + 1
        review = state.get("review") or {}
        test_results = state.get("test_results") or {}
        changes = [f"Prepared development revision {revision}."]
        if task_brief.get("mode") == "compact":
            changes.append("Worked from the compact task brief and relevant upstream artifacts only.")
        if review and not review.get("approved", True):
            changes.append(f"Addressed review findings: {review.get('feedback', 'unspecified')}")
        if test_results and not test_results.get("passed", True):
            errors = test_results.get("errors") or ["unspecified test failure"]
            changes.append("Addressed failing tests: " + ", ".join(errors))

        worker_results = list(development.get("worker_results", []))
        if step == "integrate-development":
            changes.append("Integrated and stabilized worker results from parallel development.")
        technology_choices = list((state.get("design") or {}).get("technology_choices", []))
        technology_alignment = [
            {
                "name": str(choice.get("name", "")),
                "expected_version": str(choice.get("version", "")),
                "actual_version": str(choice.get("version", "")) if choice.get("version") else None,
                "status": "aligned" if choice.get("version") and choice.get("version") != "to-be-verified" else "unverified",
                "summary": (
                    "Implementation stayed aligned with the architect-selected version."
                    if choice.get("version") and choice.get("version") != "to-be-verified"
                    else "Version was not yet concretely verified from project files or fresh sources."
                ),
            }
            for choice in technology_choices
        ]
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
                "validation_attempts": [
                    _compact_validation_attempt(
                        kind="typecheck",
                        command="run the primary compile/build/typecheck command for the stack",
                        status="passed",
                        inspected_output=False,
                    ),
                    _compact_validation_attempt(
                        kind="lint",
                        command="run the primary lint command when available",
                        status="passed",
                        inspected_output=False,
                    ),
                ],
                "technology_alignment": technology_alignment,
                "side_effect_assessment": _side_effect_assessment(
                    scope="implementation revision before handoff",
                    foreseeable_side_effects=[
                        "Schema or contract changes can break native agent profile validation or orchestration tests.",
                        "Runtime memory writes can accidentally dirty the pristine skeleton if persistence guards fail.",
                    ],
                    mitigations=[
                        "Keep implementation inside approved write scopes and preserve bootstrapped-project guards for memory/artifacts.",
                        "Update role output schemas, native profiles, and tests together when contracts change.",
                    ],
                    validation_plan=[
                        "Run focused contract tests first, then the full test suite for framework/runtime changes.",
                    ],
                ),
            },
            "support_request": support_request,
        }


class ReviewerAgent(Agent):
    def __init__(self) -> None:
        super().__init__("reviewer", {"review", "support_request"})

    def _run(self, state: dict[str, Any]) -> dict[str, Any]:
        support_request = _effective_support_request(state, "reviewer")
        revision = int((state.get("development") or {}).get("revision", 0))
        scenario = _scenario_for_revision(state, "review", revision)
        approved = bool(scenario.get("approved", revision > 0))
        technology_mismatches = [
            str(item.get("summary", "Technology version alignment is not verified."))
            for item in (state.get("development") or {}).get("technology_alignment", [])
            if item.get("status") == "mismatch"
        ]
        if not technology_mismatches:
            technology_mismatches = [
                str(item.get("summary", "Technology version alignment is not verified."))
                for item in (state.get("development") or {}).get("technology_alignment", [])
                if item.get("status") == "unverified"
            ]
        if technology_mismatches and approved:
            approved = False
        return {
            "review": {
                "decision": "approved" if approved else "rework",
                "approved": approved,
                "feedback": str(
                    scenario.get(
                        "feedback",
                        "Approved for testing." if approved else "Implementation requires rework or explicit version alignment."
                    )
                ),
                "score": float(scenario.get("score", 0.94 if approved else 0.51)),
                "blocking_findings": list(
                    scenario.get(
                        "blocking_findings",
                        [] if approved else ["Reviewer requested changes.", *technology_mismatches],
                    )
                ),
                "rework_target": str(scenario.get("rework_target", "developer")),
                "residual_risks": list(scenario.get("residual_risks", [])),
                "technology_mismatches": technology_mismatches,
                "side_effect_assessment": _side_effect_assessment(
                    scope="technical review of side-effect controls",
                    foreseeable_side_effects=[] if approved else ["Implementation may have unmitigated side-effect or version-alignment risks."],
                    mitigations=["Block approval when validation, version alignment, or side-effect evidence is missing."],
                    validation_plan=["Review development side-effect assessment and validation attempts before testing proceeds."],
                    decision="safe_to_proceed" if approved else "needs_review",
                ),
            },
            "support_request": support_request,
        }


class TesterAgent(Agent):
    def __init__(self) -> None:
        super().__init__("tester", {"test_results", "support_request"})

    def _run(self, state: dict[str, Any]) -> dict[str, Any]:
        support_request = _effective_support_request(state, "tester")
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
                "validation_attempts": [
                    _compact_validation_attempt(
                        kind="test",
                        command="run the primary automated acceptance or regression command",
                        status="passed" if passed else "failed",
                        inspected_output=not passed,
                        summary="" if passed else ", ".join(errors),
                    )
                ],
                "side_effect_assessment": _side_effect_assessment(
                    scope="acceptance and regression validation",
                    foreseeable_side_effects=[] if passed else errors,
                    mitigations=["Use acceptance and regression coverage to detect user-visible side effects."],
                    validation_plan=["Validate happy paths, error paths, and relevant regressions before DoD review."],
                    decision="safe_to_proceed" if passed else "needs_review",
                ),
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
                "side_effect_assessment": _side_effect_assessment(
                    scope="definition of done side-effect acceptance",
                    foreseeable_side_effects=[] if approved else list(scenario.get("blocking_findings", [])),
                    mitigations=["Accept only when functional, non-functional, design, validation, and side-effect evidence are sufficient."],
                    validation_plan=["Confirm reviewer and tester evidence before final acceptance."],
                    decision="safe_to_proceed" if approved else "blocked",
                ),
            }
        }
