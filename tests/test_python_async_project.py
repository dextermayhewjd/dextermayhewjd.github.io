"""Source fidelity, runnable lessons, and published navigation for the async project."""
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MATERIAL = ROOT / 'python-async-concurrency'
CONTENT = ROOT / 'content/projects/python-async-concurrency'


def documented_stdout(stdout, experiment):
    if experiment.get('normalize_elapsed_seconds'):
        # Elapsed wall time varies; preserve and compare the observable events.
        return re.sub(r'^\[\d+\.\d{3}s\] ', '', stdout, flags=re.MULTILINE)
    return stdout


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'a' and 'href' in attrs:
            self.hrefs.append(attrs['href'])


class SourceReading(HTMLParser):
    def __init__(self):
        super().__init__()
        self.details = []
        self.groups = 0
        self.unfolded_sources = []
        self.source_ids = set()
        self.in_pre = False
        self.visible_code = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'pre':
            self.in_pre = True
        if tag == 'details':
            self.details.append(attrs.get('id'))
            if attrs.get('id') == 'slime-source-reading':
                self.groups += 1
                if 'open' in attrs:
                    self.unfolded_sources.append('open group')
        if 'reading-source' in attrs.get('class', '').split() or attrs.get('id') == 'source-usage-locations':
            self.source_ids.add(attrs['id'])
            if 'slime-source-reading' not in self.details:
                self.unfolded_sources.append(attrs['id'])

    def handle_endtag(self, tag):
        if tag == 'pre':
            self.in_pre = False
        if tag == 'details':
            self.details.pop()

    def handle_data(self, data):
        if self.in_pre and not self.details:
            self.visible_code.append(data)


class PythonAsyncMaterial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((MATERIAL / 'project-manifest.json').read_text())
        cls.lessons = cls.manifest['lessons'] + cls.manifest.get('curriculum_lessons', [])

    def test_async_queue_hands_off_items_before_processing_finishes(self):
        path = CONTENT / '07-queues/example.py'
        result = subprocess.run(
            [sys.executable, '-W', 'error', str(path)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], 'get request')
        self.assertLess(lines.index('put request 11'), lines.index('get 10'))
        self.assertLess(lines.index('get 10'), lines.index('put done 11'))
        self.assertLess(lines.index('put done 11'), lines.index('processed 10'))
        self.assertLess(lines.index('producer finished'), lines.index('consumer finished'))
        self.assertEqual(lines[-1], 'received [10, 11]')
        queued = []
        for line in lines:
            if line.startswith('put done '):
                queued.append(int(line.split()[-1]))
                self.assertLessEqual(len(queued), 1)
            elif line.startswith('get ') and line != 'get request':
                self.assertEqual(queued.pop(0), int(line.split()[-1]))
        self.assertEqual(queued, [])

    def test_semaphore_limits_the_region_and_releases_after_exit(self):
        bundle = CONTENT / '06-semaphore'
        result = subprocess.run(
            [sys.executable, '-W', 'error', str(bundle / 'example.py')],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], 'tasks scheduled 5')
        active, peak = set(), 0
        entered, cleaned = set(), set()
        for line in lines:
            if line.startswith('entered '):
                task = int(line.split()[1])
                active.add(task)
                entered.add(task)
                peak = max(peak, len(active))
                self.assertLessEqual(len(active), 2)
            elif line.startswith('cleanup '):
                task = int(line.split()[1])
                self.assertIn(task, active)
                active.remove(task)
                cleaned.add(task)
        self.assertEqual(peak, 2)
        self.assertEqual(entered, set(range(10, 15)))
        self.assertEqual(cleaned, entered)
        self.assertEqual(active, set())
        self.assertEqual(lines[-1], 'results [10, 11, 12, 13, 14]')

        for filename, report in (
            ('failure.py', 'error generation 10 failed'),
            ('cancellation.py', 'cancelled 10'),
        ):
            with self.subTest(exit_path=filename):
                result = subprocess.run(
                    [sys.executable, '-W', 'error', str(bundle / filename)],
                    capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, '')
                lines = result.stdout.splitlines()
                self.assertNotIn('finished 10', lines)
                self.assertLess(lines.index('cleanup 10'), lines.index(report))
                self.assertLess(lines.index(report), lines.index('entered 11'))
                self.assertEqual(lines[-1], 'result 11')

    def test_taskgroup_failure_reports_only_after_remaining_cleanup(self):
        for slug, ending in (
            ('11-taskgroup-failures', ['group failed']),
            ('11-exception-groups', ['caught ExceptionGroup', 'error generation 11 failed']),
        ):
            with self.subTest(lesson=slug):
                path = CONTENT / slug / 'example.py'
                self.assertTrue(path.exists(), 'TaskGroup failure needs its own focused experiment')
                result = subprocess.run(
                    [sys.executable, '-W', 'error', str(path)],
                    capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, '')
                self.assertEqual(result.stdout.splitlines(), [
                    'start 10', 'start 11', 'cleanup 11', 'cleanup 10', *ending,
                ])

    def test_gather_failure_modes_account_for_remaining_work(self):
        cases = {
            'example.py': ('gather error generation 11 failed', 'remaining result 10'),
            'collect_exceptions.py': ("results [10, ValueError('generation 11 failed')]", 'error ValueError generation 11 failed'),
            'cancel_remaining.py': ('gather error generation 11 failed', 'remaining cancelled'),
        }
        for filename, (reported, terminal) in cases.items():
            with self.subTest(example=filename):
                path = CONTENT / '15-gather-failures' / filename
                self.assertTrue(path.exists(), 'S15 needs runnable failure and cleanup comparisons')
                result = subprocess.run(
                    [sys.executable, '-W', 'error', str(path)],
                    capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, '')
                lines = result.stdout.splitlines()
                self.assertIn(reported, lines)
                self.assertEqual(lines[-1], terminal)
                self.assertLess(lines.index('cleanup 11'), lines.index(reported))
                self.assertLess(lines.index('cleanup 10'), lines.index(terminal))
                if filename == 'example.py':
                    self.assertLess(lines.index(reported), lines.index('finished 10'))
                    self.assertIn('remaining done False', lines)
                elif filename == 'collect_exceptions.py':
                    self.assertLess(lines.index('finished 10'), lines.index(reported))
                else:
                    self.assertNotIn('finished 10', lines)

    def test_task_results_observes_pending_success_and_failure(self):
        path = CONTENT / '07-task-results' / 'example.py'
        self.assertTrue(path.exists(), 'Planned unit 07 needs its own runnable example')
        result = subprocess.run(
            [sys.executable, '-W', 'error', str(path)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        self.assertEqual(result.stdout.splitlines(), [
            'pending done False',
            'pending result InvalidStateError',
            'pending exception InvalidStateError',
            'success done True',
            'success result 10',
            'success exception None',
            'failed done True',
            'failed exception generation 11 failed',
            'failed result ValueError: generation 11 failed',
        ])

    def test_as_completed_consumes_results_and_handles_expected_failure(self):
        examples = {
            'example.py': ['result 11', 'result 10'],
            'failure.py': ['error generation 11 failed', 'result 10'],
        }
        for filename, expected in examples.items():
            with self.subTest(example=filename):
                path = CONTENT / '08-as-completed' / filename
                self.assertTrue(path.exists(), 'Unit 08 needs its own runnable experiments')
                result = subprocess.run(
                    [sys.executable, '-W', 'error', str(path)],
                    capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, '')
                self.assertEqual(result.stdout.splitlines(), expected)

    def test_task_cancellation_waits_for_cleanup_before_reporting_completion(self):
        path = CONTENT / '09-task-cancellation' / 'example.py'
        self.assertTrue(path.exists(), 'Unit 09 needs a focused cancellation experiment')
        result = subprocess.run(
            [sys.executable, '-W', 'error', str(path)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        self.assertEqual(result.stdout.splitlines(), [
            'generate 10 started',
            'cancel requested True',
            'done immediately False',
            'cleanup 10',
            'cancelled',
            'done after await True',
        ])

    def test_wait_for_examples_report_timeout_after_cleanup(self):
        cases = {
            'example.py': ['cleanup 10', 'timeout'],
            'slow_cleanup.py': ['cleanup start 10', 'cleanup finished 10', 'timeout'],
            'timeout_message.py': ['cleanup 10', 'timeout: 任务 10 未在等待时限内完成'],
        }
        for filename, expected in cases.items():
            with self.subTest(example=filename):
                path = CONTENT / '10-wait-for' / filename
                self.assertTrue(path.exists(), 'Unit 10 needs its documented experiments')
                result = subprocess.run(
                    [sys.executable, '-W', 'error', str(path)],
                    capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, '')
                self.assertEqual(result.stdout.splitlines(), expected)

    def test_time_budget_examples_measure_cleanup_and_finish_budgeted_wait(self):
        folder = CONTENT / '11-time-budget'
        for filename in ('example.py', 'budget.py'):
            self.assertTrue((folder / filename).exists(), 'Unit 11 needs runnable timing examples')
        result = subprocess.run(
            [sys.executable, '-W', 'error', str(folder / 'example.py')],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        match = re.fullmatch(
            r'cleanup start 10\ncleanup finished 10\n\[(\d+\.\d{3})s\] timeout\n',
            result.stdout,
        )
        self.assertIsNotNone(match, result.stdout)
        # Validate the measured output without assuming scheduler precision.
        self.assertGreaterEqual(float(match.group(1)), 0)
        budget = subprocess.run(
            [sys.executable, '-W', 'error', str(folder / 'budget.py')],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(budget.returncode, 0, budget.stderr)
        self.assertEqual(budget.stderr, '')
        self.assertEqual(budget.stdout, 'budget expired\n')

    def test_timeout_shares_budget_and_reports_after_cleanup(self):
        folder = CONTENT / '12-timeout-scope'
        cases = {
            'example.py': [
                'start 10', 'finished 10', 'cleanup 10',
                'start 20', 'cleanup 20', 'shared budget expired',
                'outside timeout block',
            ],
            'individual.py': [
                'start 10', 'finished 10', 'cleanup 10',
                'start 20', 'finished 20', 'cleanup 20',
                'both finished', 'outside timeout block',
            ],
        }
        for filename, expected in cases.items():
            with self.subTest(example=filename):
                path = folder / filename
                self.assertTrue(path.exists(), 'Unit 12 needs its budget comparison')
                result = subprocess.run(
                    [sys.executable, '-W', 'error', str(path)],
                    capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, '')
                self.assertEqual(result.stdout.splitlines(), expected)

    def test_taskgroup_joins_tasks_before_leaving_scope(self):
        path = CONTENT / '04-taskgroup' / 'example.py'
        self.assertTrue(path.exists(), 'TaskGroup needs its own runnable lesson')
        result = subprocess.run(
            [sys.executable, '-W', 'error', str(path)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        lines = re.sub(r'^\[\d+\.\d{3}s\] ', '', result.stdout,
                       flags=re.MULTILINE).splitlines()
        self.assertCountEqual(lines, [
            'main: inside group',
            'generate 10: sleep 2s', 'generate 11: sleep 1s',
            'generate 10: resumed', 'generate 11: resumed',
            'main: group finished',
        ])
        self.assertEqual(lines[-1], 'main: group finished')
        for item in (10, 11):
            self.assertLess(lines.index(f'generate {item}: sleep {2 if item == 10 else 1}s'),
                            lines.index(f'generate {item}: resumed'))

    def test_taskgroup_lesson_follows_create_task(self):
        lessons = self.manifest['lessons']
        self.assertEqual([lesson['slug'] for lesson in lessons[:6]], [
            '01-async-def', '02-await', '03-tasks', '04-taskgroup', '05-gather', '04-results',
        ])
        self.assertEqual([lesson['number'] for lesson in lessons], list(range(1, 24)))

    def test_gather_keeps_input_order_when_tasks_finish_in_reverse_order(self):
        path = CONTENT / '05-gather' / 'example.py'
        self.assertTrue(path.exists(), 'Gather needs its own runnable lesson')
        result = subprocess.run(
            [sys.executable, '-W', 'error', str(path)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        lines = documented_stdout(result.stdout, {'normalize_elapsed_seconds': True}).splitlines()
        self.assertLess(lines.index('generate 11: resumed'), lines.index('generate 10: resumed'))
        self.assertEqual(lines[-1], 'results [10, 11]')

    def test_examples_run_with_documented_output(self):
        examples = 0
        for lesson in self.lessons:
            if not lesson['example']:
                continue
            with self.subTest(lesson=lesson['slug']):
                path = CONTENT / lesson['slug'] / 'example.py'
                result = subprocess.run(
                    [sys.executable, '-W', 'error', str(path)],
                    cwd=path.parent if lesson.get('working_directory') == 'bundle' else None,
                    capture_output=True, text=True, timeout=20,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, '')
                self.assertIn(documented_stdout(result.stdout, lesson),
                              lesson.get('valid_stdout', [lesson['expected_stdout']]))
                # The displayed experiment must be the file the reader downloads.
                page = (path.parent / 'index.md').read_text()
                self.assertIn('```python\n' + path.read_text().rstrip() + '\n```', page)
                examples += 1
        self.assertEqual(examples, 36)

    def test_additional_experiments_with_registered_outputs(self):
        for lesson in self.lessons:
            for experiment in lesson.get('additional_examples', []):
                if 'expected_stdout' not in experiment:
                    continue
                with self.subTest(lesson=lesson['slug'], example=experiment['file']):
                    path = CONTENT / lesson['slug'] / experiment['file']
                    result = subprocess.run(
                        [sys.executable, '-W', 'error', str(path)],
                        capture_output=True, text=True, timeout=20,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stderr, '')
                    self.assertIn(documented_stdout(result.stdout, experiment),
                                  experiment.get('valid_stdout', [experiment['expected_stdout']]))
                    self.assertIn('(' + experiment['file'] + ')', (path.parent / 'index.md').read_text())

    def test_await_comparison_uses_only_direct_await(self):
        path = CONTENT / '02-await' / 'comparison.py'
        result = subprocess.run(
            [sys.executable, '-W', 'error', str(path)],
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        self.assertEqual(result.stdout.splitlines(), [
            'A: with assignment', 'start 10', 'end 10', 'start 11', 'end 11',
            'B: without assignment', 'start 10', 'end 10', 'start 11', 'end 11',
        ])
        page = (path.parent / 'index.md').read_text()
        self.assertIn('(comparison.py)', page)
        # Navigation may name the next lesson without teaching its API here.
        lesson_body = page.rsplit('\n---\n', 1)[0]
        self.assertNotIn('create_task', lesson_body)
        for script in path.parent.glob('*.py'):
            self.assertNotIn('create_task', script.read_text())
        for label in ('A: with assignment', 'B: without assignment'):
            self.assertIn(label, page)

    def test_task_comparison_shows_yielding_and_blocking(self):
        path = CONTENT / '03-tasks' / 'comparison.py'
        self.assertTrue(path.exists(), 'Task lesson needs a runnable comparison')
        result = subprocess.run(
            [sys.executable, '-W', 'error', str(path)],
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        self.assertEqual(result.stdout.splitlines(), [
            'A: no other task', 'start 10', 'end 10', 'start 11', 'end 11',
            'B: another task is ready', 'start 10', 'start 11', 'end 10', 'end 11',
            'C: blocking sleep', 'start 10', 'end 10', 'start 11', 'end 11',
        ])
        page = (path.parent / 'index.md').read_text()
        self.assertIn('(comparison.py)', page)
        for label in ('A: no other task', 'B: another task is ready', 'C: blocking sleep'):
            self.assertIn(label, page)

    def test_wait_lesson_avoids_notification_primitives(self):
        folder = CONTENT / '04-results'
        page = (folder / 'index.md').read_text()
        for artifact in (folder / 'index.md', folder / 'example.py', folder / 'as_completed.py'):
            text = artifact.read_text()
            for unfamiliar in ('asyncio.Event', 'release.wait', 'release.set'):
                self.assertNotIn(unfamiliar, text)
        script = folder / 'as_completed.py'
        result = subprocess.run(
            [sys.executable, '-W', 'error', str(script)],
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        self.assertEqual(result.stdout, 'result 11\nresult 10\n')
        self.assertIn('```python\n' + script.read_text().rstrip() + '\n```', page)

    def test_source_packs_match_snapshots(self):
        summary = json.loads((MATERIAL / 'summary.json').read_text())
        total = 0
        for lesson in self.lessons:
            path = CONTENT / lesson['slug'] / 'learning-pack.json'
            if lesson.get('source_count') == 0:
                self.assertFalse(path.exists(), 'A syntax-only unit should not fabricate a source pack')
                continue
            pack = json.loads(path.read_text())
            self.assertEqual(pack['revision'], lesson.get('source_revision', summary['source_head']))
            snapshot_root = ROOT / lesson.get('source_snapshot_root', 'python-async-concurrency/source_snapshot')
            for reference in pack['references'].values():
                with self.subTest(lesson=lesson['slug'], source=reference['path']):
                    raw = (snapshot_root / (reference['path'] + '.txt')).read_bytes()
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), reference['blobSha256'])
                    lines = raw.decode().splitlines()
                    self.assertEqual(reference['text'], '\n'.join(lines[reference['line']-1:reference['endLine']]))
                    self.assertTrue(reference['available'])
                    total += 1
        self.assertGreaterEqual(total, 25)


class PythonAsyncPublished(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        hugo = os.environ.get('HUGO_BINARY') or shutil.which('hugo')
        if not hugo:
            raise unittest.SkipTest('Hugo Extended 0.166.0 is required')
        cls.temp = tempfile.TemporaryDirectory(prefix='python-async-project-test-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.output = Path(cls.temp.name)
        subprocess.run([
            hugo, '--quiet', '--destination', str(cls.output),
            '--cacheDir', str(cls.output / 'cache'),
        ], cwd=ROOT, check=True)
        cls.manifest = json.loads((MATERIAL / 'project-manifest.json').read_text())
        cls.lessons = cls.manifest['lessons'] + cls.manifest.get('curriculum_lessons', [])
        cls.project = cls.output / 'projects/python-async-concurrency'

    def test_async_lock_is_current_unit_19_after_queue(self):
        html = (self.project / '19-async-lock/index.html').read_text()
        self.assertIn('19 · asyncio.Lock：保护跨 await 的共享状态', html)
        self.assertIn('href="../07-queues/"', html)
        previous = (self.project / '07-queues/index.html').read_text()
        self.assertIn('href="../19-async-lock/"', previous)
        links = Links()
        links.feed(html)
        self.assertTrue({'async-lock', 'lock-swimlanes', 'lock-acquire-release',
                         'lock-exit', 'lock-takeaways'} <= links.ids)
        parser = SourceReading()
        parser.feed(html)
        self.assertIn((CONTENT / '19-async-lock/example.py').read_text().strip(),
                      ''.join(parser.visible_code))
        plan = json.loads((ROOT / 'python-async-reference/curriculum.json').read_text())
        self.assertEqual(plan['lessons'][18]['status'], 'existing')
        self.assertEqual(plan['lessons'][18]['source_lessons'], ['19-async-lock'])

    def test_async_event_is_current_unit_20_after_lock(self):
        html = (self.project / '20-async-event/index.html').read_text()
        self.assertIn('20 · asyncio.Event：让任务等待一个通知', html)
        self.assertIn('href="../19-async-lock/"', html)
        previous = (self.project / '19-async-lock/index.html').read_text()
        self.assertIn('href="../20-async-event/"', previous)
        links = Links()
        links.feed(html)
        self.assertTrue({'event-notification', 'event-output', 'event-set-clear',
                         'event-broadcast', 'event-cancellation', 'event-takeaways'} <= links.ids)
        self.assertIn('class="async-event-lanes"', html)
        parser = SourceReading()
        parser.feed(html)
        self.assertIn((CONTENT / '20-async-event/example.py').read_text().strip(),
                      ''.join(parser.visible_code))
        plan = json.loads((ROOT / 'python-async-reference/curriculum.json').read_text())
        self.assertEqual(plan['lessons'][19]['status'], 'existing')
        self.assertEqual(plan['lessons'][19]['source_lessons'], ['20-async-event'])

    def test_async_queue_is_current_unit_18_after_semaphore(self):
        html = (self.project / '07-queues/index.html').read_text()
        self.assertIn('18 · asyncio.Queue：让生产者与消费者交接数据', html)
        self.assertIn('href="../06-semaphore/"', html)
        previous = (self.project / '06-semaphore/index.html').read_text()
        self.assertIn('href="../07-queues/"', previous)
        links = Links()
        links.feed(html)
        self.assertTrue({'async-queue', 'queue-transfer', 'queue-capacity', 'queue-stop', 'thread-queue'} <= links.ids)
        parser = SourceReading()
        parser.feed(html)
        self.assertIn((CONTENT / '07-queues/example.py').read_text().strip(),
                      ''.join(parser.visible_code))
        plan = json.loads((ROOT / 'python-async-reference/curriculum.json').read_text())
        self.assertEqual(plan['lessons'][17]['status'], 'existing')

    def test_semaphore_is_current_unit_17_after_shield(self):
        html = (self.project / '06-semaphore/index.html').read_text()
        self.assertIn('17 · asyncio.Semaphore：限制同时进入的工作', html)
        self.assertIn('href="../13-shield/"', html)
        previous = (self.project / '13-shield/index.html').read_text()
        self.assertIn('href="../06-semaphore/"', previous)
        links = Links()
        links.feed(html)
        self.assertTrue({'semaphore-permits', 'semaphore-acquire-release', 'semaphore-cleanup'} <= links.ids)
        self.assertTrue({'failure.py', 'cancellation.py'} <= set(links.hrefs))
        parser = SourceReading()
        parser.feed(html)
        self.assertIn((CONTENT / '06-semaphore/example.py').read_text().strip(),
                      ''.join(parser.visible_code))
        plan = json.loads((ROOT / 'python-async-reference/curriculum.json').read_text())
        self.assertEqual(plan['lessons'][16]['status'], 'existing')

    def test_with_syntax_has_its_own_unit_before_taskgroup(self):
        syntax = (self.project / '04-with-async-with/index.html').read_text()
        self.assertIn('04 · with / async with', syntax)
        self.assertIn('message.txt', syntax)
        self.assertIn('with open(', syntax)
        self.assertNotIn('with manager', syntax)
        self.assertIn('href="../04-taskgroup/"', syntax)
        previous = (self.project / '03-tasks/index.html').read_text()
        self.assertIn('href="../04-with-async-with/"', previous)
        taskgroup = (self.project / '04-taskgroup/index.html').read_text()
        self.assertIn('05 · TaskGroup', taskgroup)
        self.assertIn('href="../04-with-async-with/#async-with-basics"', taskgroup)
        for slug in ('12-timeout-scope', '13-shield'):
            html = (self.project / slug / 'index.html').read_text()
            self.assertIn('href="../04-with-async-with/#async-with-basics"', html)

    def test_planned_task_results_is_reached_after_wait(self):
        page = self.project / '07-task-results/index.html'
        self.assertTrue(page.exists(), 'Planned unit 07 must be published separately')
        new_page = page.read_text()
        self.assertIn('读取 Task 的状态与结果', new_page)
        previous = (self.project / '04-results/index.html').read_text()
        self.assertIn('href="../07-task-results/"', previous)
        route = (self.project / 'learning-route/index.html').read_text()
        self.assertIn('/projects/python-async-concurrency/07-task-results/', route)
        old_page = (self.project / '05-cancellation/index.html').read_text()
        self.assertIn('取消与超时', old_page)
        parser = SourceReading()
        parser.feed(new_page)
        self.assertIn((CONTENT / '07-task-results/example.py').read_text().strip(),
                      ''.join(parser.visible_code))

    def test_as_completed_is_reached_after_taskgroup_failures(self):
        page = self.project / '08-as-completed/index.html'
        self.assertTrue(page.exists(), 'Unit 08 must have a separate published page')
        html = page.read_text()
        previous = (self.project / '11-exception-groups/index.html').read_text()
        self.assertIn('href="../08-as-completed/"', previous)
        route = (self.project / 'learning-route/index.html').read_text()
        self.assertIn('/projects/python-async-concurrency/08-as-completed/', route)
        self.assertTrue((self.project / '06-semaphore/index.html').exists())
        links = Links()
        links.feed(html)
        self.assertIn('as-completed-results', links.ids)
        self.assertIn('failure.py', links.hrefs)
        parser = SourceReading()
        parser.feed(html)
        self.assertIn((CONTENT / '08-as-completed/example.py').read_text().strip(),
                      ''.join(parser.visible_code))

    def test_task_cancellation_is_reached_after_task_results(self):
        page = self.project / '09-task-cancellation/index.html'
        self.assertTrue(page.exists(), 'Unit 09 must have a separate published page')
        html = page.read_text()
        previous = (self.project / '07-task-results/index.html').read_text()
        self.assertIn('href="../09-task-cancellation/"', previous)
        route = (self.project / 'learning-route/index.html').read_text()
        self.assertIn('/projects/python-async-concurrency/09-task-cancellation/', route)
        self.assertTrue((self.project / '05-cancellation/index.html').exists())
        links = Links()
        links.feed(html)
        self.assertIn('task-cancellation', links.ids)
        self.assertIn('cancelled-task-results', links.ids)
        parser = SourceReading()
        parser.feed(html)
        self.assertIn((CONTENT / '09-task-cancellation/example.py').read_text().strip(),
                      ''.join(parser.visible_code))

    def test_wait_for_is_reached_after_as_completed(self):
        page = self.project / '10-wait-for/index.html'
        self.assertTrue(page.exists(), 'Unit 10 must have a separate published page')
        previous = (self.project / '08-as-completed/index.html').read_text()
        self.assertIn('href="../10-wait-for/"', previous)
        route = (self.project / 'learning-route/index.html').read_text()
        self.assertIn('/projects/python-async-concurrency/10-wait-for/', route)
        html = page.read_text()
        links = Links()
        links.feed(html)
        self.assertTrue({'wait-for', 'timeout-error', 'timeout-cleanup'} <= links.ids)
        self.assertTrue({'slow_cleanup.py', 'timeout_message.py'} <= set(links.hrefs))
        parser = SourceReading()
        parser.feed(html)
        self.assertIn((CONTENT / '10-wait-for/example.py').read_text().strip(),
                      ''.join(parser.visible_code))

    def test_time_budget_is_reached_after_wait_for(self):
        page = self.project / '11-time-budget/index.html'
        self.assertTrue(page.exists(), 'Unit 11 must have a separate published page')
        previous = (self.project / '10-wait-for/index.html').read_text()
        self.assertIn('href="../11-time-budget/"', previous)
        route = (self.project / 'learning-route/index.html').read_text()
        self.assertIn('/projects/python-async-concurrency/11-time-budget/', route)
        html = page.read_text()
        links = Links()
        links.feed(html)
        self.assertTrue({'elapsed-time', 'remaining-budget', 'timing-is-observation'} <= links.ids)
        self.assertIn('budget.py', links.hrefs)
        parser = SourceReading()
        parser.feed(html)
        self.assertIn((CONTENT / '11-time-budget/example.py').read_text().strip(),
                      ''.join(parser.visible_code))

    def test_timeout_scope_is_reached_after_time_budget(self):
        page = self.project / '12-timeout-scope/index.html'
        self.assertTrue(page.exists(), 'Unit 12 must have a separate published page')
        previous = (self.project / '11-time-budget/index.html').read_text()
        self.assertIn('href="../12-timeout-scope/"', previous)
        route = (self.project / 'learning-route/index.html').read_text()
        self.assertIn('/projects/python-async-concurrency/12-timeout-scope/', route)
        html = page.read_text()
        links = Links()
        links.feed(html)
        self.assertTrue({'shared-timeout', 'timeout-exit', 'individual-budgets'} <= links.ids)
        self.assertIn('individual.py', links.hrefs)
        parser = SourceReading()
        parser.feed(html)
        self.assertIn((CONTENT / '12-timeout-scope/example.py').read_text().strip(),
                      ''.join(parser.visible_code))

    def test_shield_is_reached_after_timeout_scope(self):
        page = self.project / '13-shield/index.html'
        self.assertTrue(page.exists(), 'Unit 13 must have a separate published page')
        previous = (self.project / '12-timeout-scope/index.html').read_text()
        self.assertIn('href="../13-shield/"', previous)
        route = (self.project / 'learning-route/index.html').read_text()
        self.assertIn('/projects/python-async-concurrency/13-shield/', route)
        html = page.read_text()
        links = Links()
        links.feed(html)
        self.assertTrue({'shield-cancellation', 'shield-ownership', 'shield-limits'} <= links.ids)
        self.assertTrue({'unshielded.py', 'failure.py'} <= set(links.hrefs))
        parser = SourceReading()
        parser.feed(html)
        self.assertIn((CONTENT / '13-shield/example.py').read_text().strip(),
                      ''.join(parser.visible_code))

    def test_gather_failures_is_reached_after_cancellation(self):
        page = self.project / '15-gather-failures/index.html'
        self.assertTrue(page.exists(), 'S15 must have a separate published page')
        html = page.read_text()
        self.assertIn('10.1 · asyncio.gather：收集报错，任务仍可继续', html)
        previous = (self.project / '09-task-cancellation/index.html').read_text()
        self.assertIn('href="../15-gather-failures/"', previous)
        route = (self.project / 'learning-route/index.html').read_text()
        self.assertIn('/projects/python-async-concurrency/15-gather-failures/', route)
        links = Links()
        links.feed(html)
        self.assertTrue({'gather-failure', 'gather-return-exceptions', 'gather-cleanup'} <= links.ids)
        self.assertTrue({'collect_exceptions.py', 'cancel_remaining.py'} <= set(links.hrefs))
        parser = SourceReading()
        parser.feed(html)
        self.assertIn((CONTENT / '15-gather-failures/example.py').read_text().strip(),
                      ''.join(parser.visible_code))

    def test_gather_exceptions_is_a_separate_sublesson_after_failure(self):
        first = (self.project / '15-gather-failures/index.html').read_text()
        self.assertIn('href="../15-gather-exceptions/"', first)
        page = self.project / '15-gather-exceptions/index.html'
        self.assertTrue(page.exists(), 'S15.2 needs a separate reading page')
        html = page.read_text()
        self.assertIn('10.2 · return_exceptions=True：收齐结果与异常', html)
        self.assertIn('href="../15-gather-failures/"', html)
        route = (self.project / 'learning-route/index.html').read_text()
        self.assertIn('/projects/python-async-concurrency/15-gather-exceptions/', route)
        nav = html.split('<nav class="project-nav__desktop"', 1)[1].split('</nav>', 1)[0]
        self.assertLess(nav.index('/15-gather-failures/'), nav.index('/15-gather-exceptions/'))
        parser = SourceReading()
        parser.feed(html)
        self.assertIn((CONTENT / '15-gather-exceptions/example.py').read_text().strip(),
                      ''.join(parser.visible_code))

    def test_project_placement_and_order(self):
        self.assertFalse((self.output / 'courses/python-async-concurrency').exists())
        projects = (self.output / 'projects/index.html').read_text()
        self.assertIn('/projects/python-async-concurrency/', projects)
        homepage = (self.project / 'index.html').read_text()
        catalog = homepage.split('<details id="legacy-course-catalog">', 1)[1].split('</details>', 1)[0]
        positions = [catalog.index('href="' + lesson['slug'] + '/"') for lesson in self.manifest['lessons']]
        self.assertEqual(positions, sorted(positions))
        for lesson in self.lessons:
            text = (self.project / lesson['slug'] / 'index.html').read_text()
            self.assertIn('project-nav', text)
            self.assertIn('/projects/python-async-concurrency/', text)
            if lesson.get('source_count', 0):
                self.assertIn('source-source-1', text)
            else:
                self.assertNotIn('source-source-1', text)
            self.assertNotRegex(text, r'\{\{(?:SOURCE|EXAMPLE|OUTPUT)\}\}')

    def test_lesson_sources_share_one_closed_optional_group(self):
        for lesson in self.lessons:
            with self.subTest(lesson=lesson['slug']):
                parser = SourceReading()
                parser.feed((self.project / lesson['slug'] / 'index.html').read_text())
                if lesson.get('source_count') == 0:
                    self.assertEqual(parser.groups, 0)
                    self.assertEqual(parser.source_ids, set())
                    continue
                self.assertEqual(parser.groups, 1)
                self.assertEqual(parser.unfolded_sources, [])
                pack = json.loads((CONTENT / lesson['slug'] / 'learning-pack.json').read_text())
                self.assertEqual(parser.source_ids, {'source-usage-locations'} | {
                    'source-' + ref for ref in pack['references']
                })

    def test_wait_download_is_readable_without_opening_optional_material(self):
        parser = SourceReading()
        parser.feed((self.project / '04-results/index.html').read_text())
        example = (CONTENT / '04-results/example.py').read_text().strip()
        self.assertIn(example, ''.join(parser.visible_code))

    def test_wait_source_locations_render_as_navigable_rows(self):
        parser = Links()
        parser.feed((self.project / '04-results/index.html').read_text())
        coverage = json.loads((MATERIAL / 'teaching-coverage.json').read_text())
        rows = [row for row in coverage['occurrences'] if row['lesson'] == '04-results']
        self.assertTrue(rows)
        for row in rows:
            with self.subTest(source=row['id']):
                self.assertIn('source-' + row['id'], parser.ids)
                self.assertIn('/python-async-concurrency/' + row['snapshot'], parser.hrefs)

    def test_inventory_tables_and_downloads(self):
        summary = json.loads((MATERIAL / 'summary.json').read_text())
        for category, count in summary['by_category'].items():
            text = (self.project / 'usage-index' / category / 'index.html').read_text()
            occurrences = re.findall(r'<td>\s*(occ-\d{6})\s*</td>', text)
            self.assertEqual(len(occurrences), count['total_static_occurrences'], category)
        for filename in ('inventory.json', 'inventory.tsv', 'summary.json', 'SOURCE-LICENSE'):
            self.assertEqual(
                (self.output / 'python-async-concurrency' / filename).read_bytes(),
                (MATERIAL / filename).read_bytes(),
            )
        # Existing static assets remain available after adding a second mount.
        self.assertTrue((self.output / 'images').is_dir())

    def test_local_links_resolve(self):
        parsed_destinations = {}
        for page in self.project.rglob('index.html'):
            parser = Links()
            parser.feed(page.read_text())
            for href in parser.hrefs:
                url = urlsplit(href)
                if url.scheme or url.netloc:
                    continue
                target = (self.output / unquote(url.path).lstrip('/')) if url.path.startswith('/') else page.parent / unquote(url.path)
                if target.is_dir():
                    target = target / 'index.html'
                with self.subTest(page=str(page.relative_to(self.project)), href=href):
                    self.assertTrue(target.exists(), str(target))
                    if url.fragment and target.suffix == '.html':
                        if target not in parsed_destinations:
                            destination = Links()
                            destination.feed(target.read_text())
                            parsed_destinations[target] = destination.ids
                        self.assertIn(unquote(url.fragment), parsed_destinations[target])


if __name__ == '__main__':
    unittest.main()
