"""Check the published chapter navigation against the retained photo material."""

import hashlib
import json
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links = []
        self.images = []
        self.headings = []
        self.current_link = None
        self.current_heading = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a':
            self.current_link = dict(attrs, text='')
            self.links.append(self.current_link)
        if tag == 'img':
            self.images.append(attrs)
        if tag == 'h1':
            self.current_heading = ''

    def handle_data(self, text):
        if self.current_link is not None:
            self.current_link['text'] += text
        if self.current_heading is not None:
            self.current_heading += text

    def handle_endtag(self, tag):
        if tag == 'a':
            self.current_link = None
        if tag == 'h1' and self.current_heading is not None:
            self.headings.append(self.current_heading.strip())
            self.current_heading = None


class SlimeChapters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='slime-chapters-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.output = Path(cls.temp.name)
        subprocess.run(
            ['hugo', '--gc', '--minify', '--destination', str(cls.output)],
            cwd=ROOT, check=True, capture_output=True, text=True,
        )
        cls.index = json.loads((ROOT / 'slime_photo/index.json').read_text())
        cls.home = Page((cls.output / 'projects/slime/index.html').read_text())
        cls.navigation = {}
        for link in cls.home.links:
            if 'project-nav__link' in link.get('class', ''):
                cls.navigation[link['text'].strip()] = link['href']

    def page(self, url):
        return Page((self.output / unquote(urlsplit(url).path).lstrip('/') / 'index.html').read_text())

    def test_every_photo_chapter_is_reachable_in_original_order(self):
        expected_top = []
        for section in self.index['sections']:
            title = section['number'] + '. ' + section['title']
            with self.subTest(chapter=title):
                self.assertTrue(title in self.navigation, 'Missing chapter: ' + title)
                page = self.page(self.navigation[title])
                self.assertIn(title, page.headings)
            if '.' not in section['number']:
                expected_top.append(title)
        actual_top = [title for title in self.navigation if title in expected_top]
        self.assertEqual(actual_top, expected_top)

    def test_diagrams_and_chapter_links_resolve_to_retained_material(self):
        for section in self.index['sections']:
            title = section['number'] + '. ' + section['title']
            with self.subTest(chapter=title):
                self.assertTrue(title in self.navigation, 'Missing chapter: ' + title)
                url = self.navigation[title]
                page = self.page(url)
                for image in section['svg']:
                    self.assertTrue(page.images, 'Chapter diagram is missing')
                    candidates = []
                    for rendered in page.images:
                        src = urlsplit(rendered['src']).path
                        if not src.startswith('/'):
                            src = urlsplit(url).path + src
                        candidates.append(self.output / unquote(src).lstrip('/'))
                    self.assertTrue(any(
                        file.is_file() and hashlib.sha256(file.read_bytes()).hexdigest() == image['sha256']
                        for file in candidates
                    ), 'Diagram is missing or differs from the original SVG')
                for link in page.links:
                    path = unquote(urlsplit(link.get('href', '')).path)
                    if path.startswith('/projects/slime/'):
                        target = self.output / path.lstrip('/')
                        self.assertTrue(target.is_file() or (target / 'index.html').is_file(), path)
                    if path.startswith('/dextermayhewjd/dextermayhewjd.github.io/blob/main/slime_photo/'):
                        material = path.split('/blob/main/', 1)[1]
                        self.assertTrue((ROOT / material).is_file(), material)

    def test_action_reading_entries_replace_the_old_course(self):
        expected = {
            '2. Translate & Forward',
            '3. Generate Tokens',
            '3.5. 完成一次模型请求',
            '4. Launch Agent',
            '5. Manage Sandbox',
        }
        for title in expected:
            with self.subTest(action=title):
                self.assertTrue(title in self.navigation, 'Missing action: ' + title)
                page = self.page(self.navigation[title])
                self.assertTrue(any(
                    '/blob/main/slime_photo/' in link.get('href', '')
                    and unquote(link['href']).endswith('/README.md')
                    for link in page.links
                ), 'Action has no README reading entry')
        for old in ['agent', 'agent-launch', '01-agent-task']:
            self.assertFalse((self.output / 'projects/slime' / old).exists(), old)


if __name__ == '__main__':
    unittest.main()
