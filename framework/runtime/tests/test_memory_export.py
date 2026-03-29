from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import memory_export


class MemoryExportTests(unittest.TestCase):
    def test_render_project_log_snapshot_uses_structured_phase_briefs(self) -> None:
        with patch.object(
            memory_export,
            'query_memory',
            return_value=[
                {
                    'timestamp_utc': '2026-03-29T10:00:00.000000Z',
                    'phase': 'requirements',
                    'scope': 'phase',
                    'subject': 'memory subsystem',
                    'summary': 'Compact brief for requirements',
                    'payload': {
                        'why_it_changed': 'Requirements completed.',
                        'resulting_state': 'Ready for architecture.',
                    },
                }
            ],
        ) as query_memory_mock:
            markdown = memory_export.render_project_log_snapshot(limit=5)

        self.assertIn('# Project Log Snapshot', markdown)
        self.assertIn('Compact brief for requirements', markdown)
        self.assertIn('Why it changed: Requirements completed.', markdown)
        query_memory_mock.assert_called_once_with(
            kind='phase-brief',
            limit=5,
            include_superseded=True,
            active_only=False,
        )

    def test_render_known_context_snapshot_groups_facts_and_decisions(self) -> None:
        with patch.object(
            memory_export,
            'query_memory',
            side_effect=[
                [{'summary': 'The runtime is local-first', 'phase': 'development', 'payload': {'context': 'No hosted backend'}}],
                [{'summary': 'Keep records in git', 'phase': 'architecture', 'payload': {'decision': 'JSON files only'}}],
            ],
        ):
            markdown = memory_export.render_known_context_snapshot(fact_limit=3, decision_limit=2)

        self.assertIn('## Active Facts', markdown)
        self.assertIn('The runtime is local-first', markdown)
        self.assertIn('## Active Decisions', markdown)
        self.assertIn('Keep records in git', markdown)


if __name__ == '__main__':
    unittest.main()
