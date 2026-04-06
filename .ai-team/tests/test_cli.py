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
