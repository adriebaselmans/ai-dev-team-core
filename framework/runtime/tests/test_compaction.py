from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import compaction


class CompactionMemoryTests(unittest.TestCase):
    def test_compact_phase_records_phase_brief_and_supersedes_previous_brief(self) -> None:
        with (
            patch.object(compaction, 'artifact_summary', return_value={'title': 'Example'}),
            patch.object(compaction, 'latest_brief', return_value={'entry_id': 'brief-1'}) as latest_brief_mock,
            patch.object(compaction, 'append_memory_record', return_value=Path('framework/memory/records/example.json')) as append_record_mock,
        ):
            result = compaction.compact_phase('requirements', 'requirements', 'feature-a')

        self.assertEqual(result, Path('framework/memory/records/example.json'))
        latest_brief_mock.assert_called_once_with(phase='requirements', subject='feature-a', scope='phase')
        append_record_mock.assert_called_once()
        _, kwargs = append_record_mock.call_args
        self.assertEqual(kwargs['kind'], 'phase-brief')
        self.assertEqual(kwargs['phase'], 'requirements')
        self.assertEqual(kwargs['scope'], 'phase')
        self.assertEqual(kwargs['subject'], 'feature-a')
        self.assertEqual(kwargs['source'], 'compaction')
        self.assertEqual(kwargs['confidence'], 'high')
        self.assertEqual(kwargs['tags'], ['compact', 'requirements'])
        self.assertEqual(kwargs['supersedes'], 'brief-1')

    def test_compact_phase_without_artifact_still_records_memory(self) -> None:
        with (
            patch.object(compaction, 'latest_brief', return_value=None) as latest_brief_mock,
            patch.object(compaction, 'append_memory_record', return_value=Path('framework/memory/records/example.json')) as append_record_mock,
        ):
            result = compaction.compact_phase('done', None, 'feature-a')

        self.assertEqual(result, Path('framework/memory/records/example.json'))
        latest_brief_mock.assert_called_once_with(phase='done', subject='feature-a', scope='phase')
        append_record_mock.assert_called_once()
        _, kwargs = append_record_mock.call_args
        self.assertEqual(kwargs['kind'], 'phase-brief')
        self.assertEqual(kwargs['phase'], 'done')
        self.assertEqual(kwargs['scope'], 'phase')
        self.assertEqual(kwargs['subject'], 'feature-a')
        self.assertEqual(kwargs['source'], 'compaction')
        self.assertEqual(kwargs['confidence'], 'high')
        self.assertEqual(kwargs['tags'], ['compact'])
        self.assertIsNone(kwargs['supersedes'])


if __name__ == '__main__':
    unittest.main()
