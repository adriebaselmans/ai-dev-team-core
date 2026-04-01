from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import memory_store


class MemoryStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._sandbox_root = Path(tempfile.mkdtemp(prefix='runtime-memory-', dir=Path(__file__).resolve().parents[3]))

    def tearDown(self) -> None:
        shutil.rmtree(self._sandbox_root, ignore_errors=True)

    def test_query_memory_prefers_active_records_and_preserves_superseded_chain(self) -> None:
        root = self._sandbox_root / 'case-memory'
        with patch.object(memory_store, 'repo_root', return_value=root):
            first_path = memory_store.append_memory_record(
                kind='phase-brief',
                phase='requirements',
                scope='phase',
                subject='feature-a',
                source='memory-update',
                confidence='high',
                summary='First brief',
                payload={'why_it_changed': 'initial'},
                tags=['compact'],
            )
            first_record = json.loads(first_path.read_text(encoding='utf-8'))
            memory_store.append_memory_record(
                kind='phase-brief',
                phase='requirements',
                scope='phase',
                subject='feature-a',
                source='memory-update',
                confidence='high',
                summary='Replacement brief',
                payload={'why_it_changed': 'replacement'},
                tags=['compact'],
                supersedes=first_record['entry_id'],
            )
            memory_store.append_memory_record(
                kind='decision',
                phase='architecture',
                scope='project',
                subject='feature-a',
                source='architect',
                confidence='high',
                summary='Architecture decision',
                payload={'decision': 'Use local memory'},
                tags=['memory'],
            )

            active_entries = memory_store.query_memory(kind='phase-brief', scope='phase', tags={'compact'})
            all_entries = memory_store.query_memory(
                kind='phase-brief',
                scope='phase',
                tags={'compact'},
                active_only=False,
                include_superseded=True,
            )
            decision_entries = memory_store.query_memory(kind='decision', scope='project')
            latest = memory_store.latest_brief()

        self.assertEqual([entry['summary'] for entry in active_entries], ['Replacement brief'])
        self.assertEqual([entry['summary'] for entry in all_entries], ['Replacement brief', 'First brief'])
        self.assertEqual([entry['summary'] for entry in decision_entries], ['Architecture decision'])
        self.assertIsNotNone(latest)
        self.assertEqual(latest['summary'], 'Replacement brief')

    def test_query_memory_reads_legacy_logs_during_records_migration(self) -> None:
        root = self._sandbox_root / 'case-legacy-memory'
        legacy_root = root / 'framework' / 'memory' / 'logs'
        legacy_root.mkdir(parents=True, exist_ok=True)
        legacy_record = {
            'entry_id': 'legacy-1',
            'timestamp_utc': '2026-03-29T09:00:00.000000Z',
            'version': 2,
            'kind': 'decision',
            'phase': 'architecture',
            'scope': 'project',
            'source': 'architect',
            'confidence': 'high',
            'status': 'active',
            'tags': ['memory'],
            'summary': 'Keep local structured memory',
            'artifact_refs': [],
            'payload': {'decision': 'Use local records only'},
        }
        (legacy_root / 'legacy-1.json').write_text(json.dumps(legacy_record), encoding='utf-8')

        with patch.object(memory_store, 'repo_root', return_value=root):
            entries = memory_store.query_memory(kind='decision', scope='project')

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['entry_id'], 'legacy-1')
        self.assertEqual(entries[0]['summary'], 'Keep local structured memory')

    def test_query_memory_orders_mixed_timestamp_formats_by_actual_time(self) -> None:
        root = self._sandbox_root / 'case-mixed-ordering'
        legacy_root = root / 'framework' / 'memory' / 'logs'
        legacy_root.mkdir(parents=True, exist_ok=True)
        legacy_record = {
            'entry_id': 'legacy-newer',
            'timestamp_utc': '2026-03-29T09:00:00Z',
            'version': 1,
            'kind': 'phase-brief',
            'phase': 'requirements',
            'scope': 'phase',
            'subject': 'feature-a',
            'source': 'memory-update',
            'confidence': 'high',
            'status': 'active',
            'tags': ['compact'],
            'summary': 'Legacy brief',
            'artifact_refs': [],
            'payload': {},
        }
        (legacy_root / 'legacy-newer.json').write_text(json.dumps(legacy_record), encoding='utf-8')

        with patch.object(memory_store, 'repo_root', return_value=root):
            records_root = memory_store.records_root()
            structured_record = {
                'entry_id': 'new-older',
                'timestamp_utc': '2026-03-29T08:59:59.999999Z',
                'version': memory_store.MEMORY_SCHEMA_VERSION,
                'kind': 'phase-brief',
                'phase': 'requirements',
                'scope': 'phase',
                'subject': 'feature-a',
                'source': 'memory-update',
                'confidence': 'high',
                'status': 'active',
                'tags': ['compact'],
                'summary': 'Structured brief',
                'artifact_refs': [],
                'payload': {},
            }
            (records_root / 'new-older.json').write_text(json.dumps(structured_record), encoding='utf-8')

            latest = memory_store.latest_brief(phase='requirements', subject='feature-a', scope='phase')

        self.assertIsNotNone(latest)
        self.assertEqual(latest['entry_id'], 'legacy-newer')

    def test_append_memory_record_requires_known_supersedes_target(self) -> None:
        root = self._sandbox_root / 'case-supersedes'
        with patch.object(memory_store, 'repo_root', return_value=root):
            with self.assertRaisesRegex(ValueError, "supersedes unknown entry 'missing-entry'"):
                memory_store.append_memory_record(
                    kind='fact',
                    phase='development',
                    summary='Structured memory exists',
                    supersedes='missing-entry',
                )

    def test_append_memory_record_rejects_unsupported_kind(self) -> None:
        root = self._sandbox_root / 'case-invalid-kind'
        with patch.object(memory_store, 'repo_root', return_value=root):
            with self.assertRaisesRegex(ValueError, "Unsupported memory record kind 'note'"):
                memory_store.append_memory_record(
                    kind='note',
                    phase='development',
                    summary='Invalid kind',
                )


if __name__ == '__main__':
    unittest.main()
