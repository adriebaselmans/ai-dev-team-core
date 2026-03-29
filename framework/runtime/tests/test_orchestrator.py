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
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import orchestrator
import state_manager


class OrchestratorCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self._sandbox_root = Path(tempfile.mkdtemp(prefix='runtime-orchestrator-', dir=Path(__file__).resolve().parents[3]))
        (self._sandbox_root / 'framework' / 'runtime').mkdir(parents=True, exist_ok=True)
        state_manager.STATE_PATH = self._sandbox_root / 'framework' / 'runtime' / 'state.json'
        state_manager.save_state(dict(state_manager.DEFAULT_STATE))

    def tearDown(self) -> None:
        shutil.rmtree(self._sandbox_root, ignore_errors=True)

    def test_start_sets_requirements_phase_and_prints_dispatch(self) -> None:
        args = argparse.Namespace(feature='framework rework', force=False)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = orchestrator.cmd_start(args)

        self.assertEqual(exit_code, 0)
        state = state_manager.load_state()
        self.assertEqual(state['phase'], 'requirements')
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload['dispatch']['phase'], 'requirements')

    def test_start_rolls_back_when_initial_dispatch_build_fails(self) -> None:
        args = argparse.Namespace(feature='framework rework', force=False)
        starting_state = dict(state_manager.DEFAULT_STATE)

        with (
            patch.object(orchestrator, 'build_phase_dispatch_envelope', side_effect=ValueError('broken dispatch')),
            patch.object(orchestrator, 'save_state') as save_state_mock,
        ):
            with self.assertRaisesRegex(ValueError, 'broken dispatch'):
                orchestrator.cmd_start(args)

        save_state_mock.assert_not_called()
        self.assertEqual(state_manager.load_state(), starting_state)


if __name__ == '__main__':
    unittest.main()
