"""Check lesson ownership, per-API counts, and table grouping against the snapshot."""
import importlib.util
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'python-async-reference/tools/build_lesson_api_frequency.py'


class FrequencyTable(HTMLParser):
    """Read the published cells, including their row spans and category labels."""
    def __init__(self, content):
        super().__init__()
        self.groups = {}
        self.headers = []
        self.rows = None
        self.row = None
        self.cell = None
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tbody' and 'data-lesson' in attrs:
            self.rows = []
            self.groups[int(attrs['data-lesson'])] = self.rows
        elif tag == 'tr':
            self.row = []
        elif tag in ('td', 'th'):
            self.cell = {'attrs': attrs, 'text': [], 'classes': set(attrs.get('class', '').split())}
        elif self.cell is not None:
            self.cell['classes'].update(attrs.get('class', '').split())

    def handle_data(self, data):
        if self.cell is not None:
            self.cell['text'].append(data)

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            self.cell['text'] = ' '.join(' '.join(self.cell['text']).split())
            self.row.append(self.cell)
            self.cell = None
        elif tag == 'tr' and self.row is not None:
            if self.rows is not None:
                self.rows.append(self.row)
            else:
                self.headers.extend(self.row)
            self.row = None
        elif tag == 'tbody':
            self.rows = None


class LessonAPIFrequencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SCRIPT.exists():
            raise AssertionError('Per-lesson API frequency generator is missing')
        spec = importlib.util.spec_from_file_location('lesson_api_frequency', SCRIPT)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def rendered_table(self):
        table = FrequencyTable(self.module.render())
        self.assertEqual(set(table.groups), set(range(1, 42)))
        return table

    def api_cells(self):
        result = {}
        for rows in self.rendered_table().groups.values():
            for row in rows:
                cells = {cell['attrs'].get('class'): cell for cell in row
                         if cell['attrs'].get('class') not in {
                             'api-frequency-lesson', 'api-frequency-course-total',
                             'api-frequency-course-share'}}
                result[cells['api-frequency-api']['text']] = cells
        return result

    def test_each_new_api_appears_once_with_reset_local_number(self):
        rows = self.module.build_rows()
        api_rows = [row for row in rows if row['kind'] in ('调用位置', '装饰器引用')]
        scope = json.loads((ROOT / 'python-async-reference/current-api-plan.json').read_text())
        expected = {name for group in scope['api_groups'] for name in group['apis']}
        self.assertEqual(len(api_rows), 97)
        self.assertEqual({row['api'] for row in api_rows}, expected)
        self.assertEqual({row['lesson'] for row in rows}, set(range(1, 42)))
        for number in range(1, 42):
            own = [row['index'] for row in rows if row['lesson'] == number and row['index'] is not None]
            self.assertEqual(own, list(range(1, len(own) + 1)))
        for number in (10, 11):
            self.assertFalse(any(row['lesson'] == number for row in api_rows))

    def test_syntax_is_numbered_at_its_first_introduction(self):
        rows = self.module.build_rows()
        by_lesson = lambda number: [row for row in rows if row['lesson'] == number]
        self.assertEqual([row['api'] for row in by_lesson(1)], ['async def', 'asyncio.run'])
        self.assertEqual([row['api'] for row in by_lesson(2)], ['await', 'asyncio.sleep'])
        self.assertEqual(by_lesson(4)[0]['index'], 1)
        self.assertEqual(by_lesson(9)[-1]['api'], 'try/finally')
        self.assertEqual(by_lesson(11)[0]['api'], 'except*')
        lookup = {row['api']: row for row in rows}
        self.assertEqual(lookup['async def']['counts'], {'verl': 316, 'areal': 546, 'slime': 105, 'miles': 570})
        self.assertEqual(lookup['await']['counts'], {'verl': 566, 'areal': 798, 'slime': 192, 'miles': 723})
        self.assertEqual(lookup['except*']['counts'], dict.fromkeys(('verl', 'areal', 'slime', 'miles'), 0))
        self.assertEqual([row['api'] for row in by_lesson(22)], ['async for', '异步生成器中的 yield'])
        self.assertEqual(lookup['async for']['counts'], {'verl': 18, 'areal': 10, 'slime': 1, 'miles': 9})
        self.assertEqual(lookup['异步生成器中的 yield']['counts'], {'verl': 26, 'areal': 42, 'slime': 0, 'miles': 11})
        self.assertEqual(sum(row['index'] is not None for row in rows), 104)

    def test_methods_and_references_are_not_conflated(self):
        rows = {row['api']: row for row in self.module.build_rows()}
        self.assertEqual(rows['asyncio.TaskGroup']['counts'], {'verl': 0, 'areal': 1, 'slime': 0, 'miles': 0})
        self.assertEqual(rows['asyncio.TaskGroup.create_task']['counts'], {'verl': 0, 'areal': 1, 'slime': 0, 'miles': 0})
        self.assertEqual(rows['contextlib.asynccontextmanager']['kind'], '装饰器引用')
        self.assertEqual(rows['contextlib.asynccontextmanager']['counts'], {'verl': 2, 'areal': 12, 'slime': 0, 'miles': 6})
        self.assertEqual(rows['async with']['counts'], {'verl': 37, 'areal': 188, 'slime': 13, 'miles': 44})
        self.assertEqual(rows['asyncio.Semaphore.acquire']['counts'], dict.fromkeys(('verl', 'areal', 'slime', 'miles'), 0))
        self.assertEqual(rows['asyncio.gather']['counts'], {'verl': 57, 'areal': 100, 'slime': 13, 'miles': 61})

    def test_generated_table_only_labels_first_row_of_each_lesson(self):
        markdown = self.module.render()
        table = self.rendered_table()
        self.assertEqual(sum(len(rows) for rows in table.groups.values()), 105)
        for rows in table.groups.values():
            lesson_cells = [cell for row in rows for cell in row
                            if 'api-frequency-lesson' in cell['classes']]
            self.assertEqual(len(lesson_cells), 1)
            self.assertEqual(int(lesson_cells[0]['attrs']['rowspan']), len(rows))
            self.assertEqual(lesson_cells[0]['attrs']['scope'], 'rowgroup')
        self.assertIn('asyncio.TaskGroup.create_task', self.api_cells())
        self.assertNotIn('配套语法另看', markdown)
        self.assertNotIn('课内序号', markdown)
        self.assertIn('href="/projects/python-async-concurrency/22-async-iteration/"', markdown)
        self.assertIn('href="/projects/python-async-concurrency/learning-route/#curriculum-stage-processes"', markdown)
        result = subprocess.run([sys.executable, str(SCRIPT), '--check'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_progress_ranges_preserve_unwritten_gaps(self):
        self.assertEqual(self.module.format_lesson_ranges(list(range(1, 23)) + list(range(26, 33))),
                         '01–22、26–32')
        self.assertEqual(self.module.format_lesson_ranges([23, 24, 25, *range(33, 42)]),
                         '23–25、33–41')
        self.assertEqual(self.module.format_lesson_ranges([1, 3, 4]), '01、03–04')

    def test_completed_future_unit_links_to_its_first_part(self):
        rendered = self.module.render()
        self.assertIn('01–22、25–38 已整理', rendered)
        self.assertNotIn('35 单元已整理', rendered)
        table = self.rendered_table()
        label = next(cell for cell in table.groups[35][0] if 'api-frequency-lesson' in cell['classes'])
        self.assertNotIn('部分完成', label['text'])
        self.assertIn('href="/projects/python-async-concurrency/35-future-results/"', rendered)

    def test_completed_loop_unit_links_to_its_first_part(self):
        rendered = self.module.render()
        self.assertNotIn('36 单元已整理', rendered)
        self.assertIn('href="/projects/python-async-concurrency/36-manual-event-loop/"', rendered)
        table = self.rendered_table()
        label = next(cell for cell in table.groups[36][0] if 'api-frequency-lesson' in cell['classes'])
        self.assertNotIn('部分完成', label['text'])

    def test_lesson_usage_combines_all_knowledge_points_in_the_lesson(self):
        self.assertTrue(hasattr(self.module, 'lesson_usage'))
        rows = self.module.build_rows()

        def usage(number):
            return self.module.lesson_usage([row for row in rows if row['lesson'] == number])

        self.assertEqual(usage(1), {'verl': 324, 'areal': 549, 'slime': 106, 'miles': 578})
        self.assertEqual(usage(14),
                         {'verl': 11, 'areal': 125, 'slime': 6, 'miles': 69})
        self.assertEqual(usage(22),
                         {'verl': 44, 'areal': 52, 'slime': 1, 'miles': 20})
        self.assertEqual(sum(usage(21).values()), 20)
        self.assertEqual(usage(10), dict.fromkeys(self.module.REPOS))
        self.assertEqual(sum(value for number in range(1, 42) for value in usage(number).values()
                             if value is not None), 5929)

    def test_api_call_coverage_stays_separate_from_combined_lesson_usage(self):
        plan, registry, inventories = self.module.sources()
        rows = self.module.build_rows()
        selected = {api for lesson in plan['lessons'] for api in lesson['introduces']}
        stats = self.module.call_statistics(registry, inventories, selected)
        for repo in self.module.REPOS:
            total = sum(row['counts'][repo] for row in rows if row['kind'] == '调用位置')
            self.assertEqual(total, len(stats[repo]['covered']))

    def test_one_course_share_spans_all_its_api_rows_using_all_knowledge_occurrences(self):
        table = self.rendered_table()
        headers = [cell['text'] for cell in table.headers]
        self.assertIn('单项 API / 语法', headers)
        self.assertEqual(headers.count('本课占比'), 1)
        self.assertNotIn('本课合计', headers)
        for rows in table.groups.values():
            self.assertEqual(len(rows[0]), 10)
            for row in rows[1:]:
                self.assertEqual(len(row), 8)
            self.assertEqual(int(rows[0][-1]['attrs']['rowspan']), len(rows))
            self.assertTrue(all('本课' not in cell['text'] for row in rows for cell in row
                                if 'api-frequency-api' in cell['classes']))

        def values(number):
            return table.groups[number][0][-1]['text']

        self.assertEqual(values(14), '3.08%')
        self.assertEqual(values(22), '1.71%')
        self.assertEqual(values(21), '0.29%')
        self.assertEqual(values(10), '复用前课')
        self.assertEqual(values(15), '0.00%')
        self.assertEqual(values(1), '22.75%')
        self.assertEqual(values(2), '34.77%')
        # Usage outside the selected lessons stays in the denominator.
        displayed_total = sum(float(values(number).rstrip('%')) for number in table.groups
                              if values(number).endswith('%'))
        self.assertAlmostEqual(displayed_total, 86.64, delta=0.1)

    def test_four_repository_coverage_is_weighted_by_call_positions(self):
        markdown = self.module.render()
        self.assertIn('1609/1899', markdown)
        self.assertIn('84.7%', markdown)
        self.assertIn('1528/1899', markdown)
        rows = {row['api']: row for row in self.module.build_rows()}
        self.assertEqual(rows['contextlib.AsyncExitStack.pop_all']['counts'],
                         {'verl': 0, 'areal': 0, 'slime': 0, 'miles': 2})

    def test_each_statistical_row_shows_total_and_its_category_share(self):
        rows = self.api_cells()
        for name, expected in (
            ('asyncio.gather', ['231', '12.16%']),
            ('asyncio.TaskGroup', ['1', '0.05%']),
            ('async def', ['1537', '35.74%']),
            ('contextlib.asynccontextmanager', ['20', '3.11%']),
            ('try/finally', ['85', '1.98%']),
            ('except*', ['0', '0.00%']),
        ):
            self.assertEqual([rows[name][key]['text'] for key in
                              ('api-frequency-total', 'api-frequency-share')], expected)

    def test_cleanup_counts_follow_async_scope_and_count_except_star_clauses(self):
        self.assertTrue(hasattr(self.module, 'cleanup_syntax_counts'))
        source = '''
try:
    pass
finally:
    pass
async def main():
    def sync_inner():
        try:
            pass
        finally:
            pass
    try:
        await work()
    except* ValueError:
        pass
    except* TypeError:
        pass
    finally:
        pass
'''
        self.assertEqual(self.module.cleanup_syntax_counts(source), {'try/finally': 1, 'except*': 2})

    def test_frequency_marks_use_pooled_share_and_individual_repo_counts(self):
        self.assertTrue(hasattr(self.module, 'frequency_marks'))
        below = self.module.frequency_marks({'verl': 9, 'areal': 9}, 1899)
        self.assertFalse(below['total_high'])
        self.assertEqual(below['repo_high'], set())
        above = self.module.frequency_marks({'verl': 9, 'areal': 10}, 1899)
        self.assertTrue(above['total_high'])
        self.assertEqual(above['repo_high'], {'areal'})
        # A concentration in one repository can be highlighted on its own.
        concentrated = self.module.frequency_marks({'verl': 10, 'areal': 0}, 1899)
        self.assertFalse(concentrated['total_high'])
        self.assertEqual(concentrated['repo_high'], {'verl'})
        empty = self.module.frequency_marks({'verl': None, 'areal': None}, None)
        self.assertFalse(empty['total_high'])
        self.assertEqual(empty['repo_high'], set())

    def test_frequency_annotations_keep_the_measurement_type_visible(self):
        markdown = self.module.render()
        rows = self.api_cells()
        classes = lambda name: set().union(*(cell['classes'] for cell in rows[name].values()))
        self.assertIn('api-frequency-mark--total', classes('asyncio.gather'))
        self.assertIn('api-frequency-mark--repo', classes('asyncio.Event'))
        self.assertNotIn('api-frequency-mark--total', classes('asyncio.Event'))
        self.assertFalse(any(name.startswith('api-frequency-mark--') for name in classes('except*')))
        self.assertIn('同类占比 ≥ 1%', markdown)
        self.assertIn('单库次数 ≥ 10', markdown)
        self.assertIn('低频不等于不重要', markdown)

    def test_slime_threshold_excludes_four_and_includes_five(self):
        below = self.module.frequency_marks(dict.fromkeys(self.module.REPOS, 4), 1899)
        self.assertEqual(below['repo_high'], set())
        above = self.module.frequency_marks(dict.fromkeys(self.module.REPOS, 5), 1899)
        self.assertEqual(above['repo_high'], {'slime'})
        unchanged = self.module.frequency_marks(dict.fromkeys(self.module.REPOS, 10), 1899)
        self.assertEqual(unchanged['repo_high'], set(self.module.REPOS))
        self.assertIn('Slime 次数 ≥ 5', self.module.render())

    def test_every_slime_api_and_syntax_count_at_least_five_is_red(self):
        expected = {row['api']: row for row in self.module.build_rows()}
        found = set()
        for rows in self.rendered_table().groups.values():
            for cells in rows:
                name_cell = next(c for c in cells if 'api-frequency-api' in c['classes'])
                name = name_cell['text']
                repo_cells = [c for c in cells if 'api-frequency-repo' in c['classes']]
                slime = repo_cells[self.module.REPOS.index('slime')]
                count = expected[name]['counts']['slime']
                marked = 'api-frequency-mark--slime' in slime['classes']
                self.assertEqual(marked, count is not None and count >= 5, name)
                self.assertEqual(name_cell['attrs'].get('data-slime-high') == 'true', marked, name)
                self.assertNotIn('api-frequency-mark--repo', slime['classes'], name)
                for index, cell in enumerate(repo_cells):
                    if index != self.module.REPOS.index('slime'):
                        self.assertNotIn('api-frequency-mark--slime', cell['classes'], name)
                if marked:
                    found.add(name)
        self.assertIn('async with', found)
        self.assertIn('asyncio.run_coroutine_threadsafe', found)
        self.assertIn('asyncio.wait', found)
        self.assertIn('contextvars.ContextVar.get', found)
        self.assertNotIn('contextvars.ContextVar', found)
        self.assertIn('红色标注', self.module.render())


if __name__ == '__main__':
    unittest.main()
