from __future__ import annotations

import argparse
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import orchestrator


class OrchestratorWrapperTests(unittest.TestCase):
    def setUp(self) -> None:
        self._sandbox_root = Path(tempfile.mkdtemp(prefix="runtime-wrapper-", dir=Path(__file__).resolve().parents[3]))
        self.state_path = self._sandbox_root / "state.json"

    def tearDown(self) -> None:
        shutil.rmtree(self._sandbox_root, ignore_errors=True)

    def test_run_executes_new_orchestrator_and_persists_state(self) -> None:
        args = argparse.Namespace(
            input="Build a robust orchestrator.",
            flow=str(Path(__file__).resolve().parents[3] / "flows" / "software_delivery.yaml"),
            repo_path=".",
            parallel=False,
            work_item=None,
            max_iterations=5,
            max_steps=40,
            state_path=self.state_path,
            json=True,
        )
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            exit_code = orchestrator.cmd_run(args)

        self.assertEqual(exit_code, 0)
        self.assertTrue(self.state_path.exists())
        payload = json.loads(buffer.getvalue())
        self.assertTrue(payload["meta"]["completed"])
        self.assertEqual(payload["meta"]["role_models"]["developer"]["model"], "gpt-5.4")

    def test_status_reads_persisted_state_summary(self) -> None:
        self.state_path.write_text(
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
        args = argparse.Namespace(state_path=self.state_path, json=False)
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            exit_code = orchestrator.cmd_status(args)

        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["current_step"], "done")
        self.assertTrue(payload["completed"])


if __name__ == "__main__":
    unittest.main()
