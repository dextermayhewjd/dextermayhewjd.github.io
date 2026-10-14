"""Guard the promised source-to-tutorial coverage, not just chapter titles."""
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MATERIAL = ROOT / 'python-async-concurrency'
CONTENT = ROOT / 'content/projects/python-async-concurrency'


class PythonAsyncCoverage(unittest.TestCase):
    def test_every_inventory_position_has_a_valid_teaching_destination(self):
        path = MATERIAL / 'teaching-coverage.json'
        self.assertTrue(path.exists(), 'The tutorial needs a complete source-to-lesson map')
        coverage = json.loads(path.read_text())
        inventory = json.loads((MATERIAL / 'inventory.json').read_text())
        expected = {row['id']: row for row in inventory['occurrences']}
        actual = {row['id']: row for row in coverage['occurrences']}
        self.assertEqual(len(actual), len(coverage['occurrences']))
        self.assertEqual(set(actual), set(expected))
        self.assertEqual(coverage['source_revision'], inventory['source']['head'])
        for key, row in actual.items():
            with self.subTest(occurrence=key):
                self.assertEqual(row['file'], expected[key]['file'])
                self.assertEqual(row['line'], expected[key]['line'])
                self.assertEqual(row['kind'], expected[key]['kind'])
                page = CONTENT / row['lesson'] / 'index.md'
                self.assertTrue(page.exists(), str(page))
                self.assertIn('id="' + row['anchor'] + '"', page.read_text())
                if row['kind'] == 'instance_candidate':
                    self.assertIn(row['status'], ('inferred', 'candidate'))
                else:
                    self.assertEqual(row['status'], 'explained')

    def test_every_direct_api_has_an_explicit_topic(self):
        path = MATERIAL / 'teaching-topics.json'
        self.assertTrue(path.exists(), 'Every direct API needs an explicit topic')
        topics = json.loads(path.read_text())['topics']
        inventory = json.loads((MATERIAL / 'inventory.json').read_text())
        expected = {r['name'] for r in inventory['occurrences'] if r['kind'] in ('api_call', 'api_reference')}
        explained = {name for t in topics for name in t.get('apis', [])}
        self.assertFalse(expected - explained, sorted(expected - explained))
        for topic in topics:
            page = CONTENT / topic['lesson'] / 'index.md'
            self.assertIn('id="' + topic['anchor'] + '"', page.read_text())

    def test_generated_coverage_is_reproducible(self):
        tool = MATERIAL / 'tools/build_teaching_coverage.py'
        self.assertTrue(tool.exists(), 'Coverage must be regenerable when source changes')
        result = subprocess.run([sys.executable, str(tool), '--check'],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_supplementary_lessons_are_in_the_route(self):
        manifest = json.loads((MATERIAL / 'project-manifest.json').read_text())
        self.assertEqual([lesson['number'] for lesson in manifest['lessons']], list(range(1, 24)))
        for lesson in manifest['lessons']:
            page = (CONTENT / lesson['slug'] / 'index.md').read_text()
            if lesson.get('source_repository') == 'areal':
                self.assertIn('id="source-usage-locations"', page)
            else:
                self.assertIn('{{< python-async-coverage', page)
            if lesson['number'] >= 17:
                self.assertTrue(lesson['example'])
                self.assertGreaterEqual(lesson['source_count'], 1)


if __name__ == '__main__':
    unittest.main()
