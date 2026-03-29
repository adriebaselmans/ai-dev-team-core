from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import context_slicer


class ContextSlicerMemoryTests(unittest.TestCase):
    def test_build_context_slice_uses_named_memory_recipes(self) -> None:
        state = {
            'phase': 'development',
            'active_feature': 'memory subsystem',
        }
        config = {
            'slices': {
                'developer': {
                    'state': ['phase', 'active_feature'],
                    'memory': {
                        'latest_brief': {
                            'kind': 'phase-brief',
                            'scope': 'phase',
                            'limit': 1,
                            'single': True,
                        },
                        'project_decisions': {
                            'kind': 'decision',
                            'scope': 'project',
                            'limit': 2,
                        },
                    },
                }
            }
        }

        with (
            patch.object(context_slicer, 'load_context_slices', return_value=config),
            patch.object(
                context_slicer,
                'query_memory',
                side_effect=[
                    [{'summary': 'Latest phase brief'}],
                    [{'summary': 'Decision A'}, {'summary': 'Decision B'}],
                ],
            ) as query_memory_mock,
        ):
            result = context_slicer.build_context_slice('developer', state)

        self.assertEqual(result['state'], {'phase': 'development', 'active_feature': 'memory subsystem'})
        self.assertEqual(result['memory']['latest_brief'], {'summary': 'Latest phase brief'})
        self.assertEqual(
            result['memory']['project_decisions'],
            [{'summary': 'Decision A'}, {'summary': 'Decision B'}],
        )
        self.assertEqual(query_memory_mock.call_count, 2)
        first_call = query_memory_mock.call_args_list[0]
        self.assertEqual(first_call.kwargs, {'limit': 1, 'kind': 'phase-brief', 'scope': 'phase'})


if __name__ == '__main__':
    unittest.main()
