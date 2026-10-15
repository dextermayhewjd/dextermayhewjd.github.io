"""Miles uses the existing static scanner and the same API normalization rules."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'python-async-reference'
COUNTS = REFERENCE / 'repositories/miles/api-counts.json'


class MilesAsyncStatistics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not COUNTS.exists():
            raise AssertionError('Miles API counts have not been generated')
        cls.data = json.loads(COUNTS.read_text())
        cls.apis = {api['name']: api for api in cls.data['apis']}
        cls.inventory = json.loads((REFERENCE / 'repositories/miles/inventory.json').read_text())

    def test_snapshot_is_clean_and_matches_the_counts(self):
        self.assertEqual(self.data['source_head'], self.inventory['source']['head'])
        self.assertEqual(self.inventory['source']['status_porcelain_v1'], '')
        self.assertEqual(self.inventory['summary']['parse_error_count'], 0)

    def test_core_calls_and_references_remain_separate(self):
        for name, expected in [('asyncio.gather', 61), ('asyncio.create_task', 28),
                               ('asyncio.wait_for', 26), ('asyncio.TaskGroup', 0),
                               ('asyncio.Condition', 1), ('asyncio.Queue', 0)]:
            count = self.apis[name]['counts']
            self.assertEqual(count['core_direct_calls'] + count['core_inferred_calls'], expected, name)
        context = self.apis['contextlib.asynccontextmanager']['counts']
        self.assertEqual(context['core_direct_calls'], 0)
        self.assertGreater(context['core_references'], 0)

    def test_all_reported_occurrences_are_traceable(self):
        known = {event['id'] for event in self.inventory['occurrences']}
        for api in self.data['apis']:
            self.assertEqual(len(api['occurrences']), len(set(api['occurrences'])))
            self.assertTrue(set(api['occurrences']) <= known)
        self.assertTrue(set(self.data['unmapped_occurrences']) <= known)

    def test_regeneration_matches_saved_counts(self):
        result = subprocess.run([sys.executable, str(REFERENCE / 'tools/build_repository_api_counts.py'),
                                 '--repo', 'miles', '--check'], text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
