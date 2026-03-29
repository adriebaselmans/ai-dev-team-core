from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import artifacts
import task_builder
from execution import DispatchEnvelope, MockExecutionBackend, ModelSelection
from spec_loader import load_team_spec
from skill_loader import load_role_skill_contracts, load_skill_contract


class TaskBuilderInputDerivationTests(unittest.TestCase):
    def test_available_inputs_reflect_artifacts_role_writes_and_real_repo_inputs(self) -> None:
        team_spec = load_team_spec()
        contracts = load_role_skill_contracts(team_spec['roles']['developer'])
        state = {
            'phase': 'development',
            'owner': 'developer',
            'active_feature': 'framework rework',
            'next_action': 'dispatch developer',
        }

        inputs = task_builder._available_inputs_for_role('developer', 'development', team_spec, contracts, state)

        self.assertTrue(set(artifacts.ARTIFACT_FILES.values()).issubset(inputs))
        self.assertTrue(set(team_spec['roles']['developer']['writes']).issubset(inputs))
        self.assertIn('framework/clean-code.md', inputs)
        self.assertIn('relevant code in src/', inputs)
        self.assertNotIn('made up input', inputs)

    def test_build_phase_dispatch_envelope_names_missing_input_and_skill(self) -> None:
        team_spec = load_team_spec()
        fake_contracts = [
            {
                'skill': 'implementation-clean-code',
                'skill_path': '.github/skills/implementation-clean-code',
                'required_inputs': ['missing input'],
                'owned_artifacts': [],
            }
        ]
        state = {
            'phase': 'development',
            'owner': 'developer',
            'active_feature': 'framework rework',
            'next_action': 'dispatch developer',
        }

        with patch.object(task_builder, 'load_role_skill_contracts', return_value=fake_contracts):
            with self.assertRaisesRegex(
                ValueError,
                "Skill 'implementation-clean-code' from '.github/skills/implementation-clean-code' is missing required input 'missing input'",
            ):
                task_builder.build_phase_dispatch_envelope('development', team_spec, state)

    def test_missing_skill_contract_raises_clear_error(self) -> None:
        team_spec = copy.deepcopy(load_team_spec())
        team_spec['roles']['developer']['primary_skill'] = '.github/skills/does-not-exist'
        state = {
            'phase': 'development',
            'owner': 'developer',
            'active_feature': 'framework rework',
            'next_action': 'dispatch developer',
        }

        with self.assertRaisesRegex(FileNotFoundError, "Missing skill contract for '.github/skills/does-not-exist'"):
            task_builder.build_phase_dispatch_envelope('development', team_spec, state)

    def test_skill_contract_lookup_uses_declared_path_without_aliasing(self) -> None:
        contract = load_skill_contract('.github/skills/implementation-clean-code')

        self.assertEqual(contract['skill_path'], '.github/skills/implementation-clean-code')
        self.assertEqual(contract['skill'], 'implementation-clean-code')


class MockPlaceholderGuardTests(unittest.TestCase):
    def test_model_selection_marks_placeholder_configs(self) -> None:
        selection = task_builder.model_selection_for_role('developer')

        self.assertTrue(selection.placeholder)

    def test_mock_backend_requires_placeholder_flag(self) -> None:
        envelope = DispatchEnvelope(
            role='developer',
            phase='development',
            objective='Implement the change.',
            context_slice={'development': 'context'},
            owned_outputs=['framework/runtime/'],
            skill_contracts=[],
            model_selection=ModelSelection(provider='openai', model='mock-model', mode='one-shot'),
            correlation_id='corr-1',
        )

        with self.assertRaisesRegex(RuntimeError, 'MockExecutionBackend requires placeholder: true'):
            MockExecutionBackend().dispatch(envelope)


if __name__ == '__main__':
    unittest.main()
