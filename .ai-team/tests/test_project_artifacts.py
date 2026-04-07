from __future__ import annotations

import json
from pathlib import Path

import yaml

from agents.registry import build_default_agent_registry
from flows import default_flow_path
from team_orchestrator.artifact_sync import ArtifactSynchronizer
from team_orchestrator.engine import Orchestrator
from team_orchestrator.flow_loader import load_flow
from team_orchestrator.memory_sync import MemorySynchronizer
from state.factory import create_initial_state
from framework.runtime.export_docs import export_all_docs
from framework.runtime.memory_store import query_memory


def _write_blank_artifacts(root: Path) -> None:
    artifact_payloads = {
        "requirements": {
            "status": "Pending.",
            "title": "",
            "user_need": "",
            "goal": "",
            "in_scope": [],
            "out_of_scope": [],
            "functional_requirements": [],
            "acceptance_criteria": [],
            "constraints": [],
            "assumptions": [],
            "open_questions": [],
            "definition_of_ready": "Not ready.",
        },
        "design": {
            "title": "",
            "design_goal": "",
            "architecture_approach": [],
            "affected_areas": [],
            "separation_of_concerns": [],
            "module_boundaries": [],
            "data_flow": [],
            "interfaces": [],
            "technology_and_environment_considerations": [],
            "technology_choices": [],
            "clean_code_constraints": [],
            "performance_considerations": [],
            "risks_and_tradeoffs": [],
            "non_goals": [],
        },
        "review": {
            "status": "Pending.",
            "title": "",
            "decision": "Not reviewed.",
            "findings": [],
            "residual_risks": [],
            "recommendation": "",
        },
        "dod": {
            "status": "Pending.",
            "title": "",
            "delivery_summary": [],
            "requirements_coverage": [],
            "what_was_built": [],
            "what_was_verified": [],
            "automated_regression_coverage": [],
            "acceptance_test_coverage": [],
            "known_gaps_or_risks": [],
            "decision": "Not evaluated.",
            "user_feedback_needed": [],
        },
    }
    for artifact_name, payload in artifact_payloads.items():
        path = root / "doc_templates" / artifact_name / "current.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_project_metadata(root: Path) -> None:
    path = root / ".ai-team" / "framework" / "init-metadata.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "name": "Example Product",
                "description": "Example project built from the skeleton.",
                "target_stack": "Python 3.12",
                "artifact_persistence": True,
                "memory_persistence": True,
                "docs_export_on_release": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_skeleton_repo_does_not_sync_project_artifacts_without_metadata(tmp_path: Path) -> None:
    _write_blank_artifacts(tmp_path)
    orchestrator = Orchestrator(
        load_flow(default_flow_path()),
        build_default_agent_registry(),
        artifact_synchronizer=ArtifactSynchronizer(tmp_path),
    )

    orchestrator.run(create_initial_state("Build a robust orchestrator."))

    requirements = yaml.safe_load((tmp_path / "doc_templates" / "requirements" / "current.yaml").read_text(encoding="utf-8"))
    dod = yaml.safe_load((tmp_path / "doc_templates" / "dod" / "current.yaml").read_text(encoding="utf-8"))
    assert requirements["title"] == ""
    assert dod["decision"] == "Not evaluated."
    assert query_memory(limit=10, active_only=False, include_superseded=True, root=tmp_path) == []


def test_bootstrapped_project_syncs_phase_artifacts(tmp_path: Path) -> None:
    _write_blank_artifacts(tmp_path)
    _write_project_metadata(tmp_path)
    orchestrator = Orchestrator(
        load_flow(default_flow_path()),
        build_default_agent_registry(),
        artifact_synchronizer=ArtifactSynchronizer(tmp_path),
    )

    orchestrator.run(create_initial_state("Build a robust orchestrator."))

    requirements = yaml.safe_load((tmp_path / "doc_templates" / "requirements" / "current.yaml").read_text(encoding="utf-8"))
    design = yaml.safe_load((tmp_path / "doc_templates" / "design" / "current.yaml").read_text(encoding="utf-8"))
    review = yaml.safe_load((tmp_path / "doc_templates" / "review" / "current.yaml").read_text(encoding="utf-8"))
    dod = yaml.safe_load((tmp_path / "doc_templates" / "dod" / "current.yaml").read_text(encoding="utf-8"))

    assert requirements["title"] == "Example Product"
    assert requirements["status"] == "Ready."
    assert design["title"] == "Example Product"
    assert "technology_choices" in design
    assert review["decision"] == "Approved for testing."
    assert dod["decision"] == "Accepted for user review."
    assert dod["delivery_summary"]


def test_bootstrapped_project_syncs_reusable_memory_records_only(tmp_path: Path) -> None:
    _write_blank_artifacts(tmp_path)
    _write_project_metadata(tmp_path)
    orchestrator = Orchestrator(
        load_flow(default_flow_path()),
        build_default_agent_registry(),
        artifact_synchronizer=ArtifactSynchronizer(tmp_path),
        memory_synchronizer=MemorySynchronizer(tmp_path),
    )

    orchestrator.run(
        create_initial_state(
            "Build a robust orchestrator.",
            overrides={"repository": {"path": "example-repo"}},
        )
    )

    entries = query_memory(limit=10, active_only=False, include_superseded=True, root=tmp_path)
    summaries = [entry["summary"] for entry in entries]
    assert any(summary.startswith("Architecture baseline accepted for: Build a robust orchestrator.") for summary in summaries)
    assert any(summary.startswith("Repository exploration captured for example-repo.") for summary in summaries)
    assert all(entry["kind"] in {"decision", "fact"} for entry in entries)


def test_release_doc_export_is_disabled_for_bare_skeleton_repo() -> None:
    tmp_root = Path.cwd() / ".tmp-pytest-workspace" / "bare-skeleton-export"
    tmp_root.mkdir(parents=True, exist_ok=True)

    original_repo_root = export_all_docs.__globals__["repo_root"]
    export_all_docs.__globals__["repo_root"] = lambda: tmp_root
    try:
        export_all_docs(release_only=False)
    except RuntimeError as exc:
        assert "bootstrapped project repos" in str(exc)
    else:
        raise AssertionError("Expected export_all_docs to be disabled for the bare skeleton repo.")
    finally:
        export_all_docs.__globals__["repo_root"] = original_repo_root
