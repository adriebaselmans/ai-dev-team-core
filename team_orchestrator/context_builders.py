from __future__ import annotations

from typing import Any


class ExplorerContextBuilder:
    def build(self, *, role_key: str, state: dict[str, Any], step_name: str) -> dict[str, Any]:
        request = dict(state.get("support_request") or {})
        coordination = dict(state.get("coordination") or {})
        repository = dict(state.get("repository") or {})
        meta = dict(state.get("meta") or {})

        return {
            "request_id": request.get("id"),
            "question": request.get("question"),
            "reason": request.get("reason"),
            "requested_by": request.get("requested_by"),
            "resume_step": request.get("resume_step"),
            "user_input": state.get("input"),
            "coordination": {
                "repo_mode": coordination.get("repo_mode"),
                "ui_heavy": coordination.get("ui_heavy"),
            },
            "repository": {
                "path": repository.get("path"),
                "mode": repository.get("mode"),
                "facts": list(repository.get("facts", [])),
            },
            "roles": list(meta.get("roles", [])),
            "trace_length": len(list(state.get("trace", []))),
            "current_step": meta.get("current_step") or step_name,
        }


class UXUIContextBuilder:
    def build(self, *, role_key: str, state: dict[str, Any], step_name: str) -> dict[str, Any]:
        request = dict(state.get("support_request") or {})
        coordination = dict(state.get("coordination") or {})
        requirements = dict(state.get("requirements") or {})
        analysis = dict(state.get("analysis") or {})
        design = dict(state.get("design") or {})

        return {
            "request_id": request.get("id"),
            "question": request.get("question"),
            "reason": request.get("reason"),
            "requested_by": request.get("requested_by"),
            "resume_step": request.get("resume_step"),
            "user_input": state.get("input"),
            "ui_heavy": coordination.get("ui_heavy"),
            "requirements": {
                "summary": requirements.get("summary"),
                "acceptance_criteria": list(requirements.get("acceptance_criteria", [])),
                "constraints": list(requirements.get("constraints", [])),
            },
            "repository_analysis": {
                "status": analysis.get("status"),
                "insights": list(analysis.get("insights", [])),
            },
            "design": {
                "approved_for_build": design.get("approved_for_build"),
                "non_functional_requirements": list(
                    design.get("non_functional_requirements", [])
                ),
            },
        }


class RequirementsContextBuilder:
    def build(self, *, role_key: str, state: dict[str, Any], step_name: str) -> dict[str, Any]:
        coordination = dict(state.get("coordination") or {})
        repository = dict(state.get("repository") or {})
        analysis = dict(state.get("analysis") or {})
        ux_ui = dict(state.get("ux_ui") or {})

        return {
            "user_input": state.get("input"),
            "current_step": step_name,
            "coordination": {
                "repo_mode": coordination.get("repo_mode"),
                "ui_heavy": coordination.get("ui_heavy"),
            },
            "repository": {
                "path": repository.get("path"),
                "facts": list(repository.get("facts", [])),
            },
            "repository_analysis": {
                "status": analysis.get("status"),
                "insights": list(analysis.get("insights", [])),
            },
            "ux_ui": {
                "status": ux_ui.get("status"),
                "guidance": list(ux_ui.get("guidance", [])),
            },
        }


class ArchitectContextBuilder:
    def build(self, *, role_key: str, state: dict[str, Any], step_name: str) -> dict[str, Any]:
        coordination = dict(state.get("coordination") or {})
        requirements = dict(state.get("requirements") or {})
        ux_ui = dict(state.get("ux_ui") or {})
        analysis = dict(state.get("analysis") or {})
        research = dict(state.get("research") or {})
        design = dict(state.get("design") or {})

        return {
            "user_input": state.get("input"),
            "current_step": step_name,
            "coordination": {
                "repo_mode": coordination.get("repo_mode"),
                "ui_heavy": coordination.get("ui_heavy"),
                "parallel_development": coordination.get("parallel_development"),
            },
            "requirements": {
                "ready": requirements.get("ready"),
                "summary": requirements.get("summary"),
                "acceptance_criteria": list(requirements.get("acceptance_criteria", [])),
                "constraints": list(requirements.get("constraints", [])),
                "functional_requirements": list(requirements.get("functional_requirements", [])),
                "assumptions": list(requirements.get("assumptions", [])),
                "open_questions": list(requirements.get("open_questions", [])),
            },
            "ux_ui": {
                "status": ux_ui.get("status"),
                "guidance": list(ux_ui.get("guidance", [])),
            },
            "repository_analysis": {
                "status": analysis.get("status"),
                "insights": list(analysis.get("insights", [])),
            },
            "research": {
                "status": research.get("status"),
                "brief": list(research.get("brief", [])),
                "verified_facts": list(research.get("verified_facts", [])),
                "sources": list(research.get("sources", [])),
                "confidence": research.get("confidence"),
                "unknowns": list(research.get("unknowns", [])),
            },
            "existing_design": {
                "approved_for_build": design.get("approved_for_build"),
                "architecture": list(design.get("architecture", [])),
                "non_functional_requirements": list(
                    design.get("non_functional_requirements", [])
                ),
                "work_items": list(design.get("work_items", [])),
            },
        }


class ReviewerContextBuilder:
    def build(self, *, role_key: str, state: dict[str, Any], step_name: str) -> dict[str, Any]:
        requirements = dict(state.get("requirements") or {})
        design = dict(state.get("design") or {})
        development = dict(state.get("development") or {})
        research = dict(state.get("research") or {})

        return {
            "user_input": state.get("input"),
            "current_step": step_name,
            "requirements": {
                "summary": requirements.get("summary"),
                "acceptance_criteria": list(requirements.get("acceptance_criteria", [])),
                "constraints": list(requirements.get("constraints", [])),
            },
            "design": {
                "architecture": list(design.get("architecture", [])),
                "non_functional_requirements": list(
                    design.get("non_functional_requirements", [])
                ),
                "work_items": list(design.get("work_items", [])),
            },
            "development": {
                "status": development.get("status"),
                "revision": development.get("revision"),
                "strategy": development.get("strategy"),
                "worker_results": list(development.get("worker_results", [])),
                "changes": list(development.get("changes", [])),
            },
            "research": {
                "brief": list(research.get("brief", [])),
                "verified_facts": list(research.get("verified_facts", [])),
            },
        }


class TesterContextBuilder:
    def build(self, *, role_key: str, state: dict[str, Any], step_name: str) -> dict[str, Any]:
        requirements = dict(state.get("requirements") or {})
        design = dict(state.get("design") or {})
        development = dict(state.get("development") or {})
        review = dict(state.get("review") or {})

        return {
            "user_input": state.get("input"),
            "current_step": step_name,
            "requirements": {
                "summary": requirements.get("summary"),
                "acceptance_criteria": list(requirements.get("acceptance_criteria", [])),
                "constraints": list(requirements.get("constraints", [])),
            },
            "design": {
                "non_functional_requirements": list(
                    design.get("non_functional_requirements", [])
                ),
                "work_items": list(design.get("work_items", [])),
            },
            "development": {
                "status": development.get("status"),
                "revision": development.get("revision"),
                "strategy": development.get("strategy"),
                "changes": list(development.get("changes", [])),
            },
            "review": {
                "decision": review.get("decision"),
                "feedback": review.get("feedback"),
                "blocking_findings": list(review.get("blocking_findings", [])),
            },
        }


class DoDReviewerContextBuilder:
    def build(self, *, role_key: str, state: dict[str, Any], step_name: str) -> dict[str, Any]:
        requirements = dict(state.get("requirements") or {})
        design = dict(state.get("design") or {})
        development = dict(state.get("development") or {})
        review = dict(state.get("review") or {})
        test_results = dict(state.get("test_results") or {})

        return {
            "user_input": state.get("input"),
            "current_step": step_name,
            "requirements": {
                "summary": requirements.get("summary"),
                "acceptance_criteria": list(requirements.get("acceptance_criteria", [])),
                "constraints": list(requirements.get("constraints", [])),
            },
            "design": {
                "architecture": list(design.get("architecture", [])),
                "non_functional_requirements": list(
                    design.get("non_functional_requirements", [])
                ),
            },
            "development": {
                "status": development.get("status"),
                "revision": development.get("revision"),
                "changes": list(development.get("changes", [])),
            },
            "review": {
                "decision": review.get("decision"),
                "feedback": review.get("feedback"),
            },
            "test_results": {
                "decision": test_results.get("decision"),
                "passed": test_results.get("passed"),
                "errors": list(test_results.get("errors", [])),
            },
        }


class DeveloperContextBuilder:
    def build(self, *, role_key: str, state: dict[str, Any], step_name: str) -> dict[str, Any]:
        requirements = dict(state.get("requirements") or {})
        design = dict(state.get("design") or {})
        coordination = dict(state.get("coordination") or {})
        development = dict(state.get("development") or {})
        review = dict(state.get("review") or {})
        test_results = dict(state.get("test_results") or {})
        current_item = dict((state.get("meta") or {}).get("current_parallel_item") or {})

        return {
            "user_input": state.get("input"),
            "current_step": step_name,
            "requirements": {
                "summary": requirements.get("summary"),
                "acceptance_criteria": list(requirements.get("acceptance_criteria", [])),
                "constraints": list(requirements.get("constraints", [])),
            },
            "design": {
                "approved_for_build": design.get("approved_for_build"),
                "architecture": list(design.get("architecture", [])),
                "non_functional_requirements": list(
                    design.get("non_functional_requirements", [])
                ),
                "work_items": list(design.get("work_items", [])),
            },
            "coordination": {
                "parallel_development": coordination.get("parallel_development"),
                "work_items": list(coordination.get("work_items", [])),
                "integration_owner": coordination.get("integration_owner"),
            },
            "development": {
                "status": development.get("status"),
                "revision": development.get("revision"),
                "strategy": development.get("strategy"),
                "worker_results": list(development.get("worker_results", [])),
                "changes": list(development.get("changes", [])),
            },
            "review": {
                "decision": review.get("decision"),
                "feedback": review.get("feedback"),
                "blocking_findings": list(review.get("blocking_findings", [])),
            },
            "test_results": {
                "decision": test_results.get("decision"),
                "passed": test_results.get("passed"),
                "errors": list(test_results.get("errors", [])),
            },
            "parallel_item": current_item,
        }


class ScoutContextBuilder:
    def build(self, *, role_key: str, state: dict[str, Any], step_name: str) -> dict[str, Any]:
        request = dict(state.get("support_request") or {})
        coordination = dict(state.get("coordination") or {})
        repository = dict(state.get("repository") or {})
        requirements = dict(state.get("requirements") or {})
        design = dict(state.get("design") or {})
        development = dict(state.get("development") or {})
        analysis = dict(state.get("analysis") or {})

        requester = str(request.get("requested_by") or "")
        context: dict[str, Any] = {
            "question": request.get("question"),
            "reason": request.get("reason"),
            "requested_by": request.get("requested_by"),
            "resume_step": request.get("resume_step"),
            "request_id": request.get("id"),
            "user_input": state.get("input"),
            "coordination": {
                "repo_mode": coordination.get("repo_mode"),
                "ui_heavy": coordination.get("ui_heavy"),
            },
            "repository": {
                "path": repository.get("path"),
                "facts": list(repository.get("facts", [])),
            },
            "requirements": {
                "summary": requirements.get("summary"),
                "acceptance_criteria": list(requirements.get("acceptance_criteria", [])),
                "constraints": list(requirements.get("constraints", [])),
            },
            "repository_analysis": {
                "status": analysis.get("status"),
                "insights": list(analysis.get("insights", [])),
            },
        }

        if requester == "architect":
            context["requester_context"] = {
                "design_status": "in_progress" if not design else "available",
                "non_functional_requirements": list(
                    design.get("non_functional_requirements", [])
                ),
                "work_items": list(design.get("work_items", [])),
            }
        elif requester == "developer":
            context["requester_context"] = {
                "architecture": list(design.get("architecture", [])),
                "work_items": list(design.get("work_items", [])),
                "current_revision": development.get("revision"),
                "current_changes": list(development.get("changes", [])),
            }
        else:
            context["requester_context"] = {}

        return context
