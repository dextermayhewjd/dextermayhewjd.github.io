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


class PythonAsyncMaterial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((MATERIAL / 'project-manifest.json').read_text())

    def test_examples_run_with_documented_output(self):
        examples = 0
        for lesson in self.manifest['lessons']:
            if not lesson['example']:
                continue
            with self.subTest(lesson=lesson['slug']):
                path = CONTENT / lesson['slug'] / 'example.py'
                result = subprocess.run(
                    [sys.executable, '-W', 'error', str(path)],
                    capture_output=True, text=True, timeout=20,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, '')
                self.assertIn(result.stdout, lesson.get('valid_stdout', [lesson['expected_stdout']]))
                # The displayed experiment must be the file the reader downloads.
                page = (path.parent / 'index.md').read_text()
                self.assertIn('```python\n' + path.read_text().rstrip() + '\n```', page)
                examples += 1
        self.assertEqual(examples, 20)

    def test_additional_experiments_with_registered_outputs(self):
        for lesson in self.manifest['lessons']:
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
                    self.assertIn(result.stdout, experiment.get('valid_stdout', [experiment['expected_stdout']]))
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
        self.assertNotIn('create_task', page)
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
        for lesson in self.manifest['lessons']:
            path = CONTENT / lesson['slug'] / 'learning-pack.json'
            pack = json.loads(path.read_text())
            self.assertEqual(pack['revision'], summary['source_head'])
            for reference in pack['references'].values():
                with self.subTest(lesson=lesson['slug'], source=reference['path']):
                    raw = (MATERIAL / 'source_snapshot' / (reference['path'] + '.txt')).read_bytes()
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
        cls.project = cls.output / 'projects/python-async-concurrency'

    def test_project_placement_and_order(self):
        self.assertFalse((self.output / 'courses/python-async-concurrency').exists())
        projects = (self.output / 'projects/index.html').read_text()
        self.assertIn('/projects/python-async-concurrency/', projects)
        homepage = (self.project / 'index.html').read_text()
        positions = [homepage.index('href="' + lesson['slug'] + '/"') for lesson in self.manifest['lessons']]
        self.assertEqual(positions, sorted(positions))
        for lesson in self.manifest['lessons']:
            text = (self.project / lesson['slug'] / 'index.html').read_text()
            self.assertIn('project-nav', text)
            self.assertIn('/projects/python-async-concurrency/', text)
            self.assertIn('source-source-1', text)
            self.assertNotRegex(text, r'\{\{(?:SOURCE|EXAMPLE|OUTPUT)\}\}')

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
