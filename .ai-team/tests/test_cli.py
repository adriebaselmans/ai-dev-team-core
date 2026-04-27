from __future__ import annotations

import json
from pathlib import Path

from team_orchestrator.cli import main


def test_cli_run_persists_state_and_supports_summary_output(tmp_path: Path, capsys) -> None:
    state_path = tmp_path / "runtime-state.json"

    exit_code = main(
        [
            "run",
            "--input",
            "Build a robust orchestrator.",
            "--state-path",
            str(state_path),
        ]
    )

    assert exit_code == 0
    assert state_path.exists()
    payload = json.loads(capsys.readouterr().out)
    assert payload["completed"] is True
    assert payload["flow_name"] == "software-delivery-orchestration"


def test_cli_status_reads_persisted_state(tmp_path: Path, capsys) -> None:
    state_path = tmp_path / "runtime-state.json"
    state_path.write_text(
        json.dumps(
            {
                "input": "Build a robust orchestrator.",
                "meta": {
                    "current_step": "done",
                    "completed": True,
                    "terminated": True,
                    "termination_reason": "completed",
                    "last_role": "coordinator",
                    "flow_name": "software-delivery-orchestration",
                },
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(["status", "--state-path", str(state_path)])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["current_step"] == "done"
    assert payload["completed"] is True


def test_cli_supports_legacy_short_form_run_invocation(tmp_path: Path, capsys) -> None:
    state_path = tmp_path / "runtime-state.json"
    exit_code = main(
        [
            "--input",
            "Build a robust orchestrator.",
            "--state-path",
            str(state_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["completed"] is True


def test_cli_context_status_reports_adapter_state(capsys) -> None:
    exit_code = main(["context", "status"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["policy"] == ".ai-team/context/policy.yaml"
    assert payload["default_output_mode"] == "compact"
    assert "rtk" in payload["adapter_status"]
    assert "fallback" in payload["adapter_status"]["rtk"]


def test_cli_context_doctor_passes_for_pristine_skeleton(capsys) -> None:
    exit_code = main(["context", "doctor"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is True
    assert payload["errors"] == []


def test_cli_version_reports_consistent_metadata(capsys) -> None:
    exit_code = main(["version"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["version"] == "1.0.5"


def test_cli_export_docs_fails_safely_for_bare_skeleton(capsys) -> None:
    exit_code = main(["export-docs"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "only enabled for bootstrapped project repos" in captured.err


def test_cli_export_memory_renders_snapshot(capsys) -> None:
    exit_code = main(["export-memory", "--view", "known-context", "--limit", "5"])

    assert exit_code == 0
    assert "# Known Context Snapshot" in capsys.readouterr().out


def test_cli_repository_tool_builds_request(capsys) -> None:
    exit_code = main(["repository-tool", "--target-path", ".", "--objective", "Map the skeleton."])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["tool"] == "repository-exploration"
    assert payload["target_path"] == "."
    assert payload["wiki_category"] == "repositories"
