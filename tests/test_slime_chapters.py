"""Check the published chapter navigation against the retained photo material."""

import ast
import hashlib
import json
import re
import subprocess
import tempfile
import textwrap
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]


def without_navigation(text):
    return re.sub(r'<div class="reading-navigation"[^>]*>\s*.*?\n</div>\n*', '', text, flags=re.S)


def source_fences(text, language=None):
    pattern = r'```python\n(.*?)\n```' if language == 'python' else r'```([^\n]*)\n(.*?)\n```'
    return re.findall(pattern, without_navigation(text), re.S)


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links = []
        self.images = []
        self.headings = []
        self.iframes = []
        self.details = []
        self.navigations = []
        self.sequence = []
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
            self.sequence.append(('image', attrs.get('src')))
        if attrs.get('data-reading-navigation'):
            self.navigations.append(attrs)
            self.sequence.append(('navigation', attrs['data-reading-navigation']))
        if tag == 'iframe':
            self.iframes.append(attrs)
        if tag == 'details':
            self.details.append(attrs)
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

    def test_framework_walkthrough_publishes_authored_body_and_resources(self):
        url = '/projects/slime/framework-walkthrough/'
        self.assertEqual(self.navigation.get('00 · 全景 Walkthrough'), url)
        reading = self.page('/projects/slime/code-reading/')
        self.assertTrue(any(link['href'] == url for link in reading.links))

        page = self.page(url)
        source = ROOT / 'slime_photo/code-reading/chapters/00-overview'
        self.assertTrue(page.images, 'The framework map must be visible in the walkthrough')
        map_urls = [item['src'] for item in page.images
                    if unquote(urlsplit(item['src']).path).endswith('/framework-map.svg')]
        self.assertEqual(len(map_urls), 1)
        rendered_map = self.output / unquote(urlsplit(map_urls[0]).path).lstrip('/')
        self.assertEqual(rendered_map.read_bytes(), (source / 'framework-map.svg').read_bytes())
        self.assertFalse(any(link['href'].startswith('../') for link in page.links))
        self.assertTrue(any(link['href'] == '/projects/slime/code-reading/' for link in page.links))
        self.assertTrue(any('/task-walkthrough/' in link['href'] for link in page.links))

        for filename in ('walkthrough.md', 'SOURCE-CHECK.md'):
            downloads = [link['href'] for link in page.links
                         if 'download' in link
                         and unquote(urlsplit(link['href']).path).endswith('/' + filename)]
            self.assertTrue(downloads, filename + ' has no local download')
            target = self.output / unquote(urlsplit(downloads[0]).path).lstrip('/')
            self.assertEqual(target.read_bytes(), (source / filename).read_bytes())

        # Both the new learning narrative and the retained reference headings
        # come from the authored document, rather than a second copied page.
        authored_headings = re.findall(r'^## (.+)$', (source / 'walkthrough.md').read_text(), re.M)
        rendered_headings = {heading.rstrip('#').rstrip() for heading in page.headings}
        self.assertTrue(set(authored_headings).issubset(rendered_headings))

    def test_trajectory_management_note_has_local_page_and_downloads(self):
        chapter = '/projects/slime/4-slime-core-components-and-orchestration/4-1-agent-rollout-adapters-and-harnesses/'
        note_url = chapter + 'trajectory-management/'
        self.assertEqual(self.navigation.get('专题：轨迹管理'), note_url)
        for source_url in (chapter, '/projects/slime/code-reading/'):
            page = self.page(source_url)
            self.assertTrue(any(link['href'] == note_url for link in page.links), source_url)

        note = self.page(note_url)
        for heading in ('单元 1：新请求怎样接回历史', '单元 2：历史中的 assistant 被改写怎么办', '单元 3：消息树怎样变成可训练片段'):
            self.assertTrue(any(text.rstrip('#').rstrip() == heading for text in note.headings), heading)
        source = ROOT / 'slime_photo/4.Slime Core Components and Orchestration/4.1.Agent Rollout Adapters and Harnesses/Trajectory Management'
        for filename in ('README.md', 'SOURCE-CHECK.md'):
            urls = [link['href'] for link in note.links
                    if unquote(urlsplit(link['href']).path).endswith('/' + filename)
                    and not urlsplit(link['href']).netloc]
            self.assertTrue(urls, filename + ' has no local download')
            target = self.output / unquote(urlsplit(urls[0]).path).lstrip('/')
            self.assertEqual(target.read_bytes(), (source / filename).read_bytes())
        self.assertFalse(any(link['href'].startswith('../') for link in note.links))

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
        self.assertTrue(parent.images, 'Action 2 has no opening diagram')
        self.assertTrue(
            urlsplit(parent.images[0]['src']).path.endswith('/flow.svg'),
            'Action 2 must open with its local data-flow diagram',
        )
        child_links = [
            link['href'] for link in parent.links
            if link.get('href', '').startswith(parent_url)
            and link.get('href', '').endswith('/data-flow/')
        ]
        self.assertTrue(child_links, 'Data-flow page is missing')
        page = self.page(child_links[0])
        self.assertIn('纵向数据流', page.headings)
        for view in (parent, page):
            self.assertFalse(any(
                'project-nav__link' in link.get('class', '')
                and link.get('href') == child_links[0]
                for link in view.links
            ), 'Merged data-flow page must not duplicate Action 2 in the sidebar')
            self.assertTrue(any(
                'project-nav__link--active' in link.get('class', '')
                and link.get('href') == parent_url
                for link in view.links
            ), 'Both URLs should identify Action 2 as the active sidebar entry')
        self.assertTrue(
            page.images and urlsplit(page.images[0]['src']).path.endswith('/flow.svg'),
            'The compatible data-flow URL must also open with the local diagram',
        )
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

    def test_generate_tokens_entry_renders_adopted_third_version(self):
        url = self.navigation['3. Generate Tokens']
        page = self.page(url)
        source = ROOT / 'slime_photo/4.Slime Core Components and Orchestration/4.1.Agent Rollout Adapters and Harnesses/3.Generate Tokens'
        # Original materials remain available after the approved third version is adopted.
        original_hashes = {
            'README.md': 'a99991263d07d3cc4db561ead8ede0b7ef6cf1fd4543257900a7a7f93baa7465',
            'flow.svg': '2ea3c8260282f8389389a1852b68f74be9b55dd589504f6e6afbf9735d85d65c',
            '示例.json': '2ff92deeafe35a3dbdbddf0ec2e6636732331f023c4e632f057581ed82e5728b',
        }
        for name, digest in original_hashes.items():
            self.assertEqual(hashlib.sha256((source / name).read_bytes()).hexdigest(), digest, name)
        self.assertTrue(page.images[0]['src'].endswith('/flow.svg'))
        diagram = self.output / unquote(urlsplit(page.images[0]['src']).path).lstrip('/')
        self.assertEqual(diagram.read_bytes(), (source / 'flow.svg').read_bytes())
        for name in ['示例.json', '模型输入.txt']:
            urls = [link['href'] for link in page.links
                    if unquote(urlsplit(link.get('href', '')).path).endswith('/3.Generate Tokens/' + name)]
            self.assertTrue(urls, 'Missing original resource: ' + name)
            resource = self.output / unquote(urlsplit(urls[0]).path).lstrip('/')
            self.assertEqual(resource.read_bytes(), (source / name).read_bytes())
        self.assertTrue(any('把图接到真实调用' in title for title in page.headings))
        self.assertTrue(any('检查是否能独立解释' in title for title in page.headings))
        sources = [detail for detail in page.details
                   if 'reading-source' in detail.get('class', '').split() and detail.get('data-source-check')]
        self.assertEqual({detail.get('data-source-check') for detail in sources},
                         {f'c{i:02d}' for i in range(1, 10)})
        self.assertTrue(all('open' not in detail for detail in sources))
        approved = ROOT / 'slime_photo/code-reading/previews/action-3/v3/reading.md'
        self.assertEqual(
            source_fences( (source / 'reading.md').read_text()),
            source_fences( approved.read_text()),
        )
        checks = [link['href'] for link in page.links if link['href'].endswith('/SOURCE-CHECK.md')]
        self.assertTrue(checks, 'Adopted chapter must publish its source checklist')
        self.assertTrue((self.output / unquote(urlsplit(checks[0]).path).lstrip('/')).is_file())
        self.assertTrue(any('封装 TurnRecord' in heading for heading in page.headings))
        self.assertTrue(any(link.get('href') == self.navigation['3.5. 完成一次模型请求']
                            for link in page.links))
        for link in page.links:
            href = link.get('href', '')
            self.assertFalse(href.startswith('../'), 'Unresolved source-material link: ' + href)

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

    def test_action_contexts_publish_scoped_sources_in_closed_details(self):
        mapping = json.loads((ROOT / 'slime_photo/code-reading/action-contexts.json').read_text())
        chapter_root = self.navigation['4.1. Agent Rollout Adapters and Harnesses']
        slugs = {
            'action-2': '2-translate-forward', 'action-3': '3-generate-tokens',
            'action-3-5': '3-5', 'pre-4': 'pre-4', 'action-4': '4-launch-agent',
            'action-5': '5-manage-sandbox', 'action-6': '6-exec-commands',
            'action-7': '7-make-api-calls',
        }
        self.assertEqual({entry['id'] for entry in mapping['contexts']}, set(slugs))
        for entry in mapping['contexts']:
            with self.subTest(chapter=entry['id']):
                target = self.output / chapter_root.lstrip('/') / slugs[entry['id']] / 'index.html'
                html = target.read_text()
                blocks = re.findall(
                    rf'<section[^>]*data-action-context=(?:"{entry["id"]}"|{entry["id"]}(?=[\s>]))[^>]*>(.*?)</section>',
                    html, re.S,
                )
                self.assertEqual(len(blocks), 1)
                block = Page(blocks[0])
                self.assertEqual(len(block.details), 1)
                self.assertNotIn('open', block.details[0])
                # Local diagrams/introductions precede the context; reading code follows it.
                self.assertLess(html.index('<img'), html.index('data-action-context='))
                self.assertNotIn(mapping['revision'], re.sub(r'<[^>]+>', '', blocks[0]))
                for source in entry['files']:
                    file_url = f'{mapping["sourceURL"]}/blob/{mapping["revision"]}/{source["path"]}'
                    self.assertIn(file_url, [link['href'] for link in block.links])
                    for symbol in source['symbols']:
                        self.assertIn(f'{file_url}#L{symbol["line"]}', [link['href'] for link in block.links])
        overview = self.page(chapter_root)
        self.assertTrue(all(any(link['href'] == chapter_root + slug + '/' for link in overview.links)
                            for slug in slugs.values()))

    def test_action_context_symbols_match_the_bound_source_snapshot(self):
        mapping = json.loads((ROOT / 'slime_photo/code-reading/action-contexts.json').read_text())
        repository = Path(mapping['sourceRepository'])
        if not (repository / '.git').exists():
            self.skipTest('Bound local Slime repository is unavailable')
        available = subprocess.run(['git', '-C', str(repository), 'cat-file', '-e', mapping['revision']],
                                   capture_output=True)
        if available.returncode:
            self.skipTest('Bound Slime snapshot is unavailable')

        def collect_symbols(tree, prefix=''):
            symbols = {}
            for node in tree.body:
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    name = prefix + node.name
                    symbols[name] = node.lineno
                    symbols.update(collect_symbols(node, name + '.'))
            return symbols

        definitions = {}
        for entry in mapping['contexts']:
            for source in entry['files']:
                path = source['path']
                if path not in definitions:
                    text = subprocess.run(['git', '-C', str(repository), 'show', f'{mapping["revision"]}:{path}'],
                                          capture_output=True, text=True, check=True).stdout
                    definitions[path] = collect_symbols(ast.parse(text))
                for symbol in source['symbols']:
                    with self.subTest(path=path, symbol=symbol['name']):
                        self.assertEqual(definitions[path].get(symbol['name']), symbol['line'])

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

    def test_action3_comparison_is_draft_and_reuses_original_resources(self):
        self.assertFalse((self.output / 'previews/slime-action-3').exists())
        manifest_path = ROOT / 'slime_photo/code-reading/previews/action-3/comparison-manifest.json'
        manifest = json.loads(manifest_path.read_text())
        for relative, digest in manifest['preservedFiles'].items():
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest, relative)
        for relative, change in manifest.get('approvedPageChanges', {}).items():
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), change['after'], relative)
        with tempfile.TemporaryDirectory(prefix='slime-action3-preview-') as directory:
            output = Path(directory)
            subprocess.run(
                ['hugo', '-D', '--destination', directory, '--noBuildLock'],
                cwd=ROOT, check=True, capture_output=True, text=True,
            )
            comparison = Page((output / 'previews/slime-action-3/compare/index.html').read_text())
            self.assertEqual([frame['src'] for frame in comparison.iframes],
                             [manifest['originalPage'], manifest['candidatePage']])
            self.assertTrue(all('Action 3' in frame['title'] for frame in comparison.iframes))
            candidate = Page((output / 'previews/slime-action-3/index.html').read_text())
            self.assertTrue(candidate.images[0]['src'].endswith('/3.Generate%20Tokens/flow.svg'))
            sources = [detail for detail in candidate.details
                       if 'reading-source' in detail.get('class', '').split() and detail.get('data-source-check')]
            self.assertEqual({detail.get('data-source-check') for detail in sources},
                             {f'c{i:02d}' for i in range(1, 10)})
            self.assertTrue(all('open' not in detail for detail in sources))
            self.assertTrue(any('把图接到真实调用' in title for title in candidate.headings))
            self.assertTrue(any('检查是否能独立解释' in title for title in candidate.headings))
            resource_suffixes = ['flow.svg', '示例.json', '模型输入.txt', 'SOURCE-CHECK.md']
            urls = [image['src'] for image in candidate.images] + [link['href'] for link in candidate.links]
            for suffix in resource_suffixes:
                paths = [unquote(urlsplit(url).path) for url in urls
                         if unquote(urlsplit(url).path).endswith('/' + suffix)]
                self.assertTrue(paths, suffix)
                self.assertTrue(all((output / path.lstrip('/')).is_file() for path in paths), suffix)
            # Shared template parameters must preserve the existing Action 2 comparison.
            previous = Page((output / 'previews/slime-action-2/compare/index.html').read_text())
            self.assertTrue(all('Action 2' in frame['title'] for frame in previous.iframes))
            third_root = ROOT / 'slime_photo/code-reading/previews/action-3/v3'
            third_manifest = json.loads((third_root / 'comparison-manifest.json').read_text())
            for relative, digest in third_manifest['preservedV2'].items():
                self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest, relative)
            for relative, change in third_manifest.get('approvedPageChanges', {}).items():
                self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), change['after'], relative)
            # The new reading organization must retain the checked code and examples.
            fence = r'```([^\n]*)\n(.*?)\n```'
            self.assertEqual(
                source_fences((third_root / 'reading.md').read_text()),
                source_fences((third_root.parent / 'reading.md').read_text()),
            )
            for route in ['compare-v3', 'compare-original-v3']:
                view = Page((output / f'previews/slime-action-3/{route}/index.html').read_text())
                self.assertEqual(len(view.iframes), 2)
                for frame in view.iframes:
                    target = urlsplit(frame['src'])
                    html = (output / unquote(target.path).lstrip('/') / 'index.html').read_text()
                    self.assertTrue(target.fragment, 'Comparison should start at the entry data table')
                    self.assertIn(f'id="{unquote(target.fragment)}"', html)
                self.assertIn('/previews/slime-action-3/v3/', view.iframes[1]['src'])
            third = Page((output / 'previews/slime-action-3/v3/index.html').read_text())
            self.assertEqual(third.images[0]['src'], candidate.images[0]['src'])
            third_sources = [detail for detail in third.details
                             if 'reading-source' in detail.get('class', '').split() and detail.get('data-source-check')]
            self.assertEqual({detail.get('data-source-check') for detail in third_sources},
                             {f'c{i:02d}' for i in range(1, 10)})
            self.assertTrue(all('open' not in detail for detail in third_sources))

    def test_action35_comparison_preserves_original_and_publishes_reading_draft(self):
        self.assertFalse((self.output / 'previews/slime-action-3-5').exists())
        draft_root = ROOT / 'slime_photo/code-reading/previews/action-3-5'
        manifest = json.loads((draft_root / 'comparison-manifest.json').read_text())
        for relative, digest in manifest['preservedFiles'].items():
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest, relative)
        for relative, change in manifest.get('approvedPageChanges', {}).items():
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), change['after'], relative)
        adopted = self.page(manifest['officialPage'])
        self.assertTrue(adopted.images[0]['src'].endswith('/flow.svg'))
        self.assertTrue(any('把图接到真实调用' in title for title in adopted.headings))
        adopted_sources = [d for d in adopted.details if d.get('data-source-check')]
        self.assertEqual({d['data-source-check'] for d in adopted_sources},
                         {f'c{i:02d}' for i in range(1, 10)})
        self.assertTrue(all('open' not in d for d in adopted_sources))
        adopted_source = ROOT / 'slime_photo/4.Slime Core Components and Orchestration/4.1.Agent Rollout Adapters and Harnesses/3.5.完成一次模型请求'
        self.assertEqual(
            source_fences( (adopted_source / 'reading.md').read_text()),
            source_fences( (draft_root / 'reading.md').read_text()),
        )
        with tempfile.TemporaryDirectory(prefix='slime-action35-preview-') as directory:
            output = Path(directory)
            subprocess.run(['hugo', '-D', '--destination', directory, '--noBuildLock'],
                           cwd=ROOT, check=True, capture_output=True, text=True)
            comparison = Page((output / 'previews/slime-action-3-5/compare/index.html').read_text())
            self.assertEqual([frame['src'] for frame in comparison.iframes],
                             [manifest['originalMaterialPage'], manifest['candidatePage']])
            draft = Page((output / 'previews/slime-action-3-5/index.html').read_text())
            baseline = Page((output / 'previews/slime-action-3-5/baseline/index.html').read_text())
            self.assertEqual(draft.images[0]['src'], baseline.images[0]['src'])
            self.assertTrue(unquote(urlsplit(draft.images[0]['src']).path).endswith(
                '/3.5.完成一次模型请求/flow.svg'))
            self.assertTrue(any('把图接到真实调用' in title for title in draft.headings))
            self.assertTrue(any('检查是否能独立解释' in title for title in draft.headings))
            sources = [detail for detail in draft.details
                       if 'reading-source' in detail.get('class', '').split() and detail.get('data-source-check')]
            self.assertEqual({detail['data-source-check'] for detail in sources},
                             {f'c{i:02d}' for i in range(1, 10)})
            self.assertTrue(all('open' not in detail for detail in sources))
            for page in (draft, baseline):
                for link in page.links:
                    url = link.get('href', '')
                    self.assertFalse(url.startswith('../'), url)
                    path = unquote(urlsplit(url).path)
                    if path.startswith(('/projects/', '/slime-photo/')):
                        target = output / path.lstrip('/')
                        self.assertTrue(target.is_file() or (target / 'index.html').is_file(), url)

    def test_launch_agent_candidate_preserves_existing_reading_and_scopes_the_diagram(self):
        self.assertFalse((self.output / 'previews/slime-action-4').exists())
        draft_root = ROOT / 'slime_photo/code-reading/previews/action-4'
        manifest = json.loads((draft_root / 'comparison-manifest.json').read_text())
        for relative, digest in manifest['preservedFiles'].items():
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest, relative)
        for relative, change in manifest.get('approvedPageChanges', {}).items():
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), change['after'], relative)
        original_example = ROOT / 'slime_photo/4.Slime Core Components and Orchestration/4.1.Agent Rollout Adapters and Harnesses/4.Launch Agent/纵向数据流/示例.json'
        self.assertEqual((draft_root / '示例.json').read_bytes(), original_example.read_bytes())
        source = original_example.parent.parent
        official_url = self.navigation['4. Launch Agent']
        official = self.page(official_url)
        self.assertTrue(official.images[0]['src'].endswith('/4.Launch%20Agent/flow.svg'))
        compatible = self.page(official_url + 'harness-run/')
        self.assertEqual(official.images[0]['src'], compatible.images[0]['src'])
        for page in (official, compatible):
            self.assertFalse(any('project-nav__link' in link.get('class', '')
                                 and link['href'] == official_url + 'harness-run/' for link in page.links))
            self.assertTrue(any('project-nav__link--active' in link.get('class', '')
                                and link['href'] == official_url for link in page.links))
        self.assertEqual(source_fences( (source / 'reading.md').read_text()),
                         source_fences( (draft_root / 'reading.md').read_text()))
        diagram = ET.parse(draft_root / 'flow.svg').getroot()
        labels = ''.join(diagram.itertext())
        for name in ['BaseHarness.run', 'ensure_agent_user', 'HarnessContext', 'write_config', 'launch_and_wait', 'run_agent', 'exec_and_wait']:
            self.assertIn(name, labels)
        self.assertNotIn('.py:', labels, 'Source metadata belongs in folded references, not the local diagram')
        with tempfile.TemporaryDirectory(prefix='slime-action4-preview-') as directory:
            output = Path(directory)
            subprocess.run(['hugo', '-D', '--destination', directory, '--noBuildLock'],
                           cwd=ROOT, check=True, capture_output=True, text=True)
            comparison = Page((output / 'previews/slime-action-4/compare/index.html').read_text())
            self.assertEqual([frame['src'] for frame in comparison.iframes],
                             [manifest['baselinePage'], manifest['candidatePage']])
            draft = Page((output / 'previews/slime-action-4/index.html').read_text())
            self.assertEqual(draft.images[0]['src'], official.images[0]['src'])
            sources = [d for d in draft.details if d.get('data-source-check')]
            self.assertEqual({d['data-source-check'] for d in sources}, {f'c{i:02d}' for i in range(1, 10)})
            self.assertTrue(all('open' not in d for d in sources))
            self.assertTrue(any('检查是否能独立解释' in h for h in draft.headings))
            for link in draft.links:
                url = link['href']
                self.assertFalse(url.startswith('../'), url)
                path = unquote(urlsplit(url).path)
                if path.startswith(('/projects/', '/slime-photo/')):
                    target = output / path.lstrip('/')
                    self.assertTrue(target.is_file() or (target / 'index.html').is_file(), url)


    def test_sandbox_adoption_preserves_originals_and_provides_comparison(self):
        candidate_root = ROOT / 'slime_photo/code-reading/previews/action-5'
        manifest = json.loads((candidate_root / 'comparison-manifest.json').read_text())
        adopted_root = ROOT / 'slime_photo/4.Slime Core Components and Orchestration/4.1.Agent Rollout Adapters and Harnesses/5.Manage Sandbox'
        adoption = json.loads((adopted_root / 'adoption-manifest.json').read_text())
        self.assertFalse((self.output / 'previews/slime-action-5').exists())
        for relative, digest in manifest['preservedFiles'].items():
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest, relative)
        for relative, change in manifest['approvedPageChanges'].items():
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), change['after'], relative)
        baseline_source = ROOT / 'content/previews/slime-action-5/baseline/index.md'
        self.assertEqual(hashlib.sha256(baseline_source.read_text().split('---', 2)[2].encode()).hexdigest(),
                         adoption['baselineBodySha256'])
        self.assertEqual(hashlib.sha256((candidate_root / 'reading.md').read_bytes()).hexdigest(),
                         adoption['approvedSnapshotSha256'])
        official = self.page(manifest['originalPage'])
        self.assertTrue(official.images[0]['src'].endswith('/5.Manage%20Sandbox/flow.svg'))
        headings = [h.removesuffix('#') for h in official.headings]
        self.assertLess(headings.index('3．结果回来了，调用者留下什么'),
                        headings.index('4．失败时，先分清两个问题'))
        self.assertEqual(next(d for d in official.details if d.get('id') == 'sandbox-failure-details').get('open'), None)
        with tempfile.TemporaryDirectory(prefix='slime-action5-preview-') as directory:
            output = Path(directory)
            subprocess.run(['hugo', '-D', '--destination', directory, '--noBuildLock'],
                           cwd=ROOT, check=True, capture_output=True, text=True)
            comparison = Page((output / 'previews/slime-action-5/compare/index.html').read_text())
            self.assertEqual([f['src'] for f in comparison.iframes],
                             [manifest['baselinePage'], manifest['candidatePage']])
            candidate_html = (output / 'previews/slime-action-5/index.html').read_text()
            candidate = Page(candidate_html)
            self.assertEqual(candidate.images[0]['src'], official.images[0]['src'])
            sources = [d for d in candidate.details if d.get('data-source-check')]
            self.assertEqual({d['data-source-check'] for d in sources},
                             {f'c{i:02d}' for i in range(1, 10)})
            self.assertTrue(all('open' not in d for d in sources))
            for name in ['示例.json', 'SOURCE-CHECK.md']:
                links = [link['href'] for link in candidate.links
                         if unquote(urlsplit(link['href']).path).endswith('/' + name)]
                self.assertTrue(links, name)
                self.assertTrue((output / unquote(urlsplit(links[0]).path).lstrip('/')).is_file())
        evidence = json.loads((candidate_root / 'source-groups.json').read_text())
        snippets = source_fences((adopted_root / 'reading.md').read_text(), 'python')
        self.assertEqual(snippets, source_fences((candidate_root / 'reading.md').read_text(), 'python'))
        self.assertEqual(len(snippets), len(evidence['excerpts']))
        for snippet, excerpt in zip(snippets, evidence['excerpts']):
            self.assertEqual(hashlib.sha256(snippet.encode()).hexdigest(), excerpt['codeSha256'])
        repository = Path('/home/fredkeira/projects/slime')
        if (repository / '.git').exists():
            for snippet, excerpt in zip(snippets, evidence['excerpts']):
                source = subprocess.run(['git', '-C', str(repository), 'show',
                                         evidence['revision'] + ':' + excerpt['path']],
                                        check=True, capture_output=True, text=True).stdout.splitlines()
                expected = textwrap.dedent('\n'.join(source[excerpt['first'] - 1:excerpt['last']]))
                self.assertEqual(snippet, expected)


    def test_current_actions_have_one_navigation_before_the_first_diagram(self):
        mapping = json.loads((ROOT / 'slime_photo/code-reading/action-navigations.json').read_text())
        chapter_root = self.navigation['4.1. Agent Rollout Adapters and Harnesses']
        slugs = {'action-2':'2-translate-forward', 'action-3':'3-generate-tokens', 'action-3-5':'3-5',
                 'pre-4':'pre-4', 'action-4':'4-launch-agent', 'action-5':'5-manage-sandbox',
                 'action-6':'6-exec-commands', 'action-7':'7-make-api-calls'}
        self.assertEqual({entry['id'] for entry in mapping['entries']}, set(slugs))
        for entry in mapping['entries']:
            with self.subTest(chapter=entry['id']):
                page = self.page(chapter_root + slugs[entry['id']] + '/')
                self.assertEqual([n['data-reading-navigation'] for n in page.navigations], [entry['id']])
                self.assertLess(page.sequence.index(('navigation', entry['id'])),
                                next(i for i, event in enumerate(page.sequence) if event[0] == 'image'))
                for relative in entry['files']:
                    if not relative.endswith('.md'):
                        continue
                    text = (ROOT / relative).read_text()
                    blocks = re.findall(r'<div class="reading-navigation"[^>]*>.*?```python\n(.*?)\n```.*?</div>', text, re.S)
                    self.assertEqual(len(blocks), 1, relative)
                    self.assertEqual(hashlib.sha256(blocks[0].encode()).hexdigest(), entry['codeSha256'], relative)
        for relative, change in mapping['approvedFileChanges'].items():
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), change['after'], relative)

    def test_exec_commands_candidate_preserves_formal_pages_and_source_excerpts(self):
        root = ROOT / 'slime_photo/code-reading/previews/action-6'
        manifest = json.loads((root / 'comparison-manifest.json').read_text())
        self.assertFalse((self.output / 'previews/slime-action-6').exists())
        for relative, digest in manifest['preservedFiles'].items():
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest, relative)
        with tempfile.TemporaryDirectory(prefix='slime-action6-preview-') as directory:
            output = Path(directory)
            subprocess.run(['hugo', '-D', '--destination', directory, '--noBuildLock'],
                           cwd=ROOT, check=True, capture_output=True, text=True)
            comparison = Page((output / 'previews/slime-action-6/compare/index.html').read_text())
            self.assertEqual([f['src'] for f in comparison.iframes],
                             [manifest['baselinePage'], manifest['candidatePage']])
            candidate_html = (output / 'previews/slime-action-6/index.html').read_text()
            candidate = Page(candidate_html)
            self.assertLess(candidate_html.index('<pre'), candidate_html.index('<img'))
            self.assertTrue(candidate.images[0]['src'].endswith('/action-6/flow.svg'))
            self.assertFalse(any(image['src'].endswith('/call-position.svg') for image in candidate.images))
            sources = [d for d in candidate.details if d.get('data-source-check')]
            self.assertEqual({d['data-source-check'] for d in sources}, {f'c{i:02d}' for i in range(1, 8)})
            self.assertTrue(all('open' not in d for d in sources))
            boundary = next(d for d in candidate.details if d.get('id') == 'exec-command-boundaries')
            self.assertNotIn('open', boundary)
            for name in ['示例.json', 'SOURCE-CHECK.md']:
                links = [a['href'] for a in candidate.links if unquote(urlsplit(a['href']).path).endswith('/' + name)]
                self.assertTrue(links, name)
                self.assertTrue((output / unquote(urlsplit(links[0]).path).lstrip('/')).is_file())
            self.assertTrue(any(a['href'] == self.navigation['7. Make API Calls'] for a in candidate.links))
        snippets = source_fences((root / 'reading.md').read_text(), 'python')
        evidence = json.loads((root / 'source-groups.json').read_text())
        navigation = re.search(r'<div class="reading-navigation"[^>]*>.*?```python\n(.*?)\n```.*?</div>',
                               (root / 'reading.md').read_text(), re.S).group(1)
        self.assertEqual(hashlib.sha256(navigation.encode()).hexdigest(), evidence['readingSkeleton']['codeSha256'])
        self.assertTrue(evidence['readingSkeleton']['notExecutableSource'])
        self.assertEqual(len(snippets), len(evidence['excerpts']))
        for snippet, excerpt in zip(snippets, evidence['excerpts']):
            self.assertEqual(hashlib.sha256(snippet.encode()).hexdigest(), excerpt['codeSha256'])
        cases = json.loads((root / '示例.json').read_text())['cases']
        self.assertEqual(cases['success_without_output']['return_value'], [0, ''])
        self.assertEqual(cases['nonzero_exit_with_tail']['return_value'], [7, 'cli-error\n'])
        self.assertEqual(cases['explicit_full_output']['return_value'], [0, 'cli-complete\n'])
        self.assertEqual(cases['wait_budget_exhausted']['return_value'], [-1, ''])


if __name__ == '__main__':
    unittest.main()
