"""Check the published chapter navigation against the retained photo material."""

import hashlib
import json
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
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
        if tag in ('h1', 'h2'):
            self.current_heading = ''

    def handle_data(self, text):
        if self.current_link is not None:
            self.current_link['text'] += text
        if self.current_heading is not None:
            self.current_heading += text

    def handle_endtag(self, tag):
        if tag == 'a':
            self.current_link = None
        if tag in ('h1', 'h2') and self.current_heading is not None:
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
            '6. Exec Commands',
            '7. Make API Calls',
        }
        for title in expected:
            with self.subTest(action=title):
                self.assertTrue(title in self.navigation, 'Missing action: ' + title)
                page = self.page(self.navigation[title])
                if title == '2. Translate & Forward':
                    self.assertFalse(any(heading.startswith('阅读材料') for heading in page.headings))
                    self.assertTrue(any(
                        link.get('href', '').startswith(self.navigation[title])
                        and link.get('href', '').endswith('/data-flow/')
                        for link in page.links
                    ), 'Translate & Forward has no local data-flow child page')
                    continue
                self.assertTrue(any(
                    '/blob/main/slime_photo/' in link.get('href', '')
                    and unquote(link['href']).endswith('/README.md')
                    for link in page.links
                ), 'Action has no README reading entry')
        for old in ['agent', 'agent-launch', '01-agent-task']:
            self.assertFalse((self.output / 'projects/slime' / old).exists(), old)

    def test_translate_data_flow_renders_source_and_example_on_site(self):
        parent_url = self.navigation['2. Translate & Forward']
        parent = self.page(parent_url)
        child_links = [
            link['href'] for link in parent.links
            if link.get('href', '').startswith(parent_url)
            and link.get('href', '').endswith('/data-flow/')
        ]
        self.assertTrue(child_links, 'Data-flow page is missing')
        page = self.page(child_links[0])
        self.assertIn('纵向数据流', page.headings)
        source = ROOT / 'slime_photo/4.Slime Core Components and Orchestration/4.1.Agent Rollout Adapters and Harnesses/2.Translate & Forward/纵向数据流'
        self.assertTrue(page.images, 'Data-flow diagram is missing')
        diagrams = [image for image in page.images if urlsplit(image['src']).path.endswith('/flow.svg')]
        self.assertTrue(diagrams, 'Detailed data-flow diagram is missing')
        diagram = self.output / unquote(urlsplit(diagrams[0]['src']).path).lstrip('/')
        self.assertEqual(diagram.read_bytes(), (source / 'flow.svg').read_bytes())
        examples = [
            link['href'] for link in page.links
            if urlsplit(link.get('href', '')).path.endswith('.json')
        ]
        self.assertTrue(examples, 'Complete example link is missing')
        example = self.output / unquote(urlsplit(examples[0]).path).lstrip('/')
        self.assertEqual(json.loads(example.read_text()), json.loads((source / '示例.json').read_text()))
        self.assertTrue(any(link.get('href') == parent_url for link in page.links))
        next_url = self.navigation['3. Generate Tokens']
        self.assertTrue(any(link.get('href') == next_url for link in page.links), 'Next action link is broken')
        self.assertTrue(any('消息路' in heading for heading in page.headings))
        self.assertTrue(any('工具路' in heading for heading in page.headings))

    def test_project_entry_starts_with_agent_task_lifecycle(self):
        self.assertIn('先看一个 Agent 样本的任务生命周期', [heading.removesuffix('#') for heading in self.home.headings])
        self.assertTrue(any(
            urlsplit(image['src']).path == '/images/slime-lifecycle/overview.svg'
            for image in self.home.images
        ), 'Project entry has no lifecycle overview')
        self.assertTrue(any(
            link.get('href', '').endswith('/4-launch-agent/')
            for link in self.home.links
        ), 'Overview has no launch reading entry')

    def test_each_action_has_a_position_map_and_overview_link(self):
        actions = {
            '2. Translate & Forward': '2',
            '3. Generate Tokens': '3',
            '3.5. 完成一次模型请求': '3-5',
            '4. Launch Agent': '4',
            '5. Manage Sandbox': '5',
            '6. Exec Commands': '6',
            '7. Make API Calls': '7',
        }
        for title, action in actions.items():
            with self.subTest(action=title):
                self.assertTrue(title in self.navigation, 'Missing action: ' + title)
                page = self.page(self.navigation[title])
                path = '/images/slime-lifecycle/action-' + action + '.svg'
                self.assertTrue(any(urlsplit(image['src']).path == path for image in page.images))
                self.assertTrue(any(
                    link.get('href') == '/projects/slime/#agent-lifecycle'
                    for link in page.links
                ), 'Action cannot return to the lifecycle overview')
                diagram = ET.parse(self.output / path.lstrip('/')).getroot()
                stages = diagram.findall('.//*[@data-stage]')
                self.assertTrue(any(stage.get('data-focus') == 'true' for stage in stages))

    def test_sandbox_position_spans_preparation_running_and_cleanup(self):
        path = self.output / 'images/slime-lifecycle/action-5.svg'
        self.assertTrue(path.exists(), 'Sandbox position map is missing')
        diagram = ET.parse(path).getroot()
        focused = {
            stage.get('data-stage') for stage in diagram.findall('.//*[@data-stage]')
            if stage.get('data-focus') == 'true'
        }
        self.assertTrue({'prepare', 'run', 'finish'}.issubset(focused))

    def test_execution_and_api_call_guides_render_their_source_on_site(self):
        execution = self.page(self.navigation['6. Exec Commands'])
        self.assertIn('4 哪一步真正启动进程', [heading.removesuffix('#') for heading in execution.headings])
        calls = self.page(self.navigation['7. Make API Calls'])
        self.assertIn('3 HTTP 路由怎样进入共享流程', [heading.removesuffix('#') for heading in calls.headings])
        self.assertTrue(any(
            link.get('href') == self.navigation['2. Translate & Forward']
            for link in calls.links
        ), 'API call guide cannot continue to input translation')

    def test_material_position_maps_match_their_action(self):
        material = ROOT / 'slime_photo/4.Slime Core Components and Orchestration/4.1.Agent Rollout Adapters and Harnesses'
        actions = {
            '2.Translate & Forward': '2',
            '3.Generate Tokens': '3',
            '3.5.完成一次模型请求': '3-5',
            '4.Launch Agent': '4',
            '5.Manage Sandbox': '5',
            '6.Exec Commands': '6',
            '7.Make API Calls': '7',
        }
        for directory, action in actions.items():
            for page in (material / directory).rglob('README.md'):
                with self.subTest(page=str(page.relative_to(material))):
                    self.assertIn('static/images/slime-lifecycle/action-' + action + '.svg', page.read_text())


if __name__ == '__main__':
    unittest.main()
