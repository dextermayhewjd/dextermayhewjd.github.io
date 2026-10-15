"""Validate review coverage and execute the exact short examples shown on cards."""

import asyncio
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'python-async-reference/knowledge-map.json'


class AsyncKnowledgeMapTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(DATA.exists(), 'Question-oriented review data is missing')
        self.data = json.loads(DATA.read_text())

    def test_cards_match_review_scope_and_relations_are_labeled(self):
        plan = json.loads((ROOT / 'python-async-reference/curriculum.json').read_text())
        ready = {unit['number'] for unit in plan['lessons'] if unit['status'] == 'existing'}
        cards = self.data['nodes']
        ids = [card['id'] for card in cards]
        self.assertEqual(len(ids), len(set(ids)))
        covered = set(self.data['covered_units'])
        self.assertEqual(covered, set(range(1, 23)), 'The current review map covers units 01–22')
        self.assertLessEqual(covered, ready, 'Review cards must not introduce unwritten units')
        self.assertEqual({number for card in cards for number in card['units']}, covered)
        groups = {group['id'] for group in self.data['groups']}
        for card in cards:
            self.assertIn(card['group'], groups)
            for field in ('title', 'question', 'explanation', 'misconception'):
                self.assertTrue(card[field], (card['id'], field))
        for edge in self.data['relations']:
            self.assertIn(edge['from'], ids)
            self.assertIn(edge['to'], ids)
            self.assertIn(edge['type'], ('prerequisite', 'contrast', 'combine'))
            self.assertTrue(edge['text'])
        self.assertTrue(all(any(card['id'] in (e['from'], e['to']) for e in self.data['relations']) for card in cards))

    def test_every_exercise_runs_and_matches_its_answer(self):
        for card in self.data['nodes']:
            with self.subTest(card=card['id']):
                exercise = card['exercise']
                options = {option['id']: option['text'] for option in exercise['options']}
                self.assertEqual(len(options), len(exercise['options']))
                self.assertIn(exercise['answer'], options)
                namespace = {'__file__': str(Path(__file__).resolve())}
                script = 'import asyncio\nimport contextlib\nimport time\nasync def main():\n'
                script += textwrap.indent(exercise['code'], '    ')
                exec(compile(script, card['id'], 'exec'), namespace)
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    asyncio.run(asyncio.wait_for(namespace['main'](), 2))
                self.assertEqual(output.getvalue().strip(), exercise['expected_output'])
                self.assertEqual(options[exercise['answer']], exercise['expected_output'])

    @unittest.skipUnless(shutil.which('node'), 'Node.js is required for interactive state checks')
    def test_review_state(self):
        result = subprocess.run(['node', str(ROOT / 'tests/async_knowledge_state.test.cjs')],
                                text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
