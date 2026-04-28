from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from team_orchestrator.project_context import artifacts_enabled, load_project_metadata, repo_root


ARTIFACT_RELATIVE_PATHS = {
    "requirements": Path("phase_artifacts/requirements/current.yaml"),
    "design": Path("phase_artifacts/design/current.yaml"),
    "review": Path("phase_artifacts/review/current.yaml"),
    "dod": Path("phase_artifacts/dod/current.yaml"),
}


class ArtifactSynchronizer:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or repo_root()

    def sync(self, state: dict[str, Any], *, role_key: str, step_name: str) -> list[Path]:
        if not artifacts_enabled(self.root):
            return []
        if role_key not in {"requirements-engineer", "architect", "reviewer", "dod-reviewer", "coordinator"}:
            return []
        if role_key == "coordinator" and step_name != "finalize":
            return []

        payloads = self._artifact_payloads(state)
        written: list[Path] = []
        for name, payload in payloads.items():
            path = self.root / ARTIFACT_RELATIVE_PATHS[name]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
            written.append(path)
        return written

    def _artifact_payloads(self, state: dict[str, Any]) -> dict[str, dict[str, Any]]:
        metadata = load_project_metadata(self.root) or {}
        title = str(metadata.get("name") or state.get("input") or "")
        target_stack = str(metadata.get("target_stack") or "").strip()
        return {
            "requirements": self._requirements_payload(state, title=title, target_stack=target_stack),
            "design": self._design_payload(state, title=title, target_stack=target_stack),
            "review": self._review_payload(state, title=title),
            "dod": self._dod_payload(state, title=title),
        }

    def _requirements_payload(self, state: dict[str, Any], *, title: str, target_stack: str) -> dict[str, Any]:
        requirements = state.get("requirements") or {}
        constraints = list(requirements.get("constraints", []))
        if target_stack:
            constraints = [f"Target stack: {target_stack}", *constraints]
        return {
            "status": "Ready." if requirements.get("ready") else "Pending.",
            "title": title,
            "user_need": str(state.get("input", "")),
            "goal": str(requirements.get("summary") or state.get("input") or ""),
            "in_scope": list(requirements.get("in_scope", [])),
            "out_of_scope": list(requirements.get("out_of_scope", [])),
            "functional_requirements": list(requirements.get("functional_requirements", [])),
            "acceptance_criteria": list(requirements.get("acceptance_criteria", [])),
            "constraints": constraints,
            "assumptions": list(requirements.get("assumptions", [])),
            "open_questions": list(requirements.get("open_questions", [])),
            "definition_of_ready": "Ready." if requirements.get("ready") else "Not ready.",
        }

    def _design_payload(self, state: dict[str, Any], *, title: str, target_stack: str) -> dict[str, Any]:
        design = state.get("design") or {}
        work_items = list(design.get("work_items", []))
        affected_areas = [str(item.get("description") or item.get("id")) for item in work_items if isinstance(item, dict)]
        environment = list(design.get("technology_and_environment_considerations", []))
        if target_stack:
            environment = [f"Target stack: {target_stack}", *environment]
        return {
            "title": title,
            "design_goal": str(state.get("input", "")),
            "architecture_approach": list(design.get("architecture", [])),
            "affected_areas": affected_areas,
            "separation_of_concerns": list(design.get("separation_of_concerns", [])),
            "module_boundaries": list(design.get("module_boundaries", [])),
            "data_flow": list(design.get("data_flow", [])),
            "interfaces": list(design.get("interfaces", [])),
            "technology_and_environment_considerations": environment,
            "clean_code_constraints": list(design.get("clean_code_constraints", [])),
            "performance_considerations": list(design.get("performance_considerations", [])),
            "risks_and_tradeoffs": list(design.get("risks_and_tradeoffs", [])),
            "non_goals": list(design.get("non_goals", [])),
            "technology_choices": list(design.get("technology_choices", [])),
        }

    def _review_payload(self, state: dict[str, Any], *, title: str) -> dict[str, Any]:
        review = state.get("review") or {}
        if not review:
            from team_orchestrator.artifact_templates import blank_artifact_payload
            blank = blank_artifact_payload("review")
            blank["title"] = title
            return blank
        return {
            "status": "Complete.",
            "title": title,
            "decision": "Approved for testing." if review.get("approved") else "Rework required.",
            "findings": list(review.get("blocking_findings", [])),
            "residual_risks": list(review.get("residual_risks", [])),
            "recommendation": str(review.get("feedback", "")),
        }

    def _dod_payload(self, state: dict[str, Any], *, title: str) -> dict[str, Any]:
        dod_review = state.get("dod_review") or {}
        test_results = state.get("test_results") or {}
        development = state.get("development") or {}
        coordination = state.get("coordination") or {}
        requirements = state.get("requirements") or {}
        if not dod_review:
            from team_orchestrator.artifact_templates import blank_artifact_payload
            blank = blank_artifact_payload("dod")
            blank["title"] = title
            return blank
        verified = []
        if test_results:
            verified.append(
                "Automated validation passed." if test_results.get("passed") else "Automated validation failed."
            )
            verified.extend(str(error) for error in test_results.get("errors", []))
        return {
            "status": "Complete.",
            "title": title,
            "delivery_summary": [str(coordination.get("final_summary", ""))] if coordination.get("final_summary") else [],
            "requirements_coverage": list(requirements.get("acceptance_criteria", [])),
            "what_was_built": list(development.get("changes", [])),
            "what_was_verified": verified,
            "automated_regression_coverage": (
                ["Automated validation executed by tester."] if test_results.get("automated") else []
            ),
            "acceptance_test_coverage": [str(dod_review.get("feedback", ""))] if dod_review.get("feedback") else [],
            "known_gaps_or_risks": list(dod_review.get("blocking_findings", [])),
            "decision": "Accepted for user review." if dod_review.get("approved") else "Not accepted.",
            "user_feedback_needed": [] if dod_review.get("approved") else list(dod_review.get("blocking_findings", [])),
        }
