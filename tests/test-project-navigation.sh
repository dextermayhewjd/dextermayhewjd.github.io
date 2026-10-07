#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
output_dir="$(mktemp -d)"
trap 'rm -rf "$output_dir"' EXIT

hugo --gc --minify --destination "$output_dir" --quiet

test -f "$output_dir/courses/index.html"
test -f "$output_dir/projects/index.html"
test -f "$output_dir/projects/learn-claude-code/index.html"
test -f "$output_dir/projects/learn-claude-code/s01/index.html"
test -f "$output_dir/projects/learn-claude-code/s17/index.html"
test -f "$output_dir/courses/mit-1806/index.html"
test -f "$output_dir/courses/mit-1806/01-systems/index.html"

course_page="$output_dir/courses/mit-1806/01-systems/index.html"
grep -q 'project-nav' "$course_page"
grep -q 'class="project-nav__link project-nav__link--active"' "$course_page"
grep -q 'MIT 18.06 线性代数' "$course_page"

claude_page="$output_dir/projects/learn-claude-code/s09/index.html"
grep -q 'S09' "$claude_page"
grep -q 'S01' "$claude_page"
grep -q 'S17' "$claude_page"

# 主目录应与新版 17 章一致，深入专题继续保留在子导航。
python3 - "$output_dir" <<'PY'
from pathlib import Path
from html.parser import HTMLParser
import sys
import json
import zipfile
import re

root = Path(sys.argv[1]) / 'projects/learn-claude-code'
base = '/projects/learn-claude-code/'

class Navigation(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None
        self.links = {}
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and 'project-nav__link' in attrs.get('class', ''):
            self.href = attrs['href']
            self.links[self.href] = ''
    def handle_data(self, text):
        if self.href is not None:
            self.links[self.href] += text
    def handle_endtag(self, tag):
        if tag == 'a':
            self.href = None

topics = {10: 'Task System', 11: 'Background Tasks', 12: 'Cron Scheduler',
          13: 'Agent Teams', 14: 'MCP Tools', 15: 'Integrated Harness',
          16: 'Workflow Runtime', 17: 'Goal Loop'}
nav = Navigation()
nav.feed((root / 's10/index.html').read_text())
for number in range(1, 18):
    chapter = f's{number:02d}'
    assert (root / chapter / 'index.html').exists(), chapter
    label = nav.links[base + chapter + '/']
    if number in topics:
        assert topics[number] in label, label
for number in (18, 19, 20):
    assert base + f's{number}/' not in nav.links

for suffix in ('s13/01-team-messaging/', 's13/02-team-protocols/',
               's13/03-task-claiming/', 's13/04-worktree-isolation/',
               's15/system-prompt/', 's15/error-recovery/'):
    page = (root / suffix / 'index.html').read_text()
    assert suffix in page
    current = Navigation()
    current.feed(page)
    assert base + suffix in current.links
    assert 'project-nav__branch open' in page
    assert 'project-nav__link--active' in page

prompt = (root / 's15/system-prompt/index.html').read_text()
assert 'Skills 目录与正文分层进入上下文' in prompt
assert len(re.findall(r'<figure class=(?:"architecture-diagram"|architecture-diagram)(?:\s|>)', prompt)) == 2
assert 'S15.1 System Prompt：模型需要哪些指令与背景' in prompt
assert 'System Prompt 的内容组成' in prompt
for old, new in {18: 's13/04-worktree-isolation/', 19: 's14/', 20: 's15/'}.items():
    assert base + new in (root / f's{old}/index.html').read_text()

# 回顾图复用上一章结构：蓝色保留、橙色旧模块将改造、灰色虚线提示合并。
class Architecture(HTMLParser):
    def __init__(self):
        super().__init__()
        self.figures = []
        self.current = None
        self.in_svg = False
        self.ids = set()
        self.diagram_links = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if tag == 'figure' and attrs.get('class') == 'architecture-diagram':
            self.current = {'nodes': [], 'paths': [], 'text': '', 'legends': 0}
            self.figures.append(self.current)
        if self.current is not None:
            if tag == 'svg':
                self.in_svg = True
            if tag == 'a' and self.in_svg and attrs.get('class') == 'diagram-chapter-link':
                self.diagram_links.append(attrs['href'])
            if tag == 'div' and attrs.get('class') == 'architecture-diagram__legend':
                self.current['legends'] += 1
            if tag == 'rect' and 'data-group' not in attrs and float(attrs.get('width', 0)) > 20:
                self.current['nodes'].append(attrs)
            if tag == 'path':
                self.current['paths'].append(attrs.get('d'))
    def handle_data(self, text):
        if self.current is not None and self.in_svg:
            self.current['text'] += text
    def handle_endtag(self, tag):
        if tag == 'svg':
            self.in_svg = False
        if tag == 'figure':
            self.current = None

diagrams = {}
for number in range(1, 7):
    parser = Architecture()
    parser.feed((root / f's{number:02d}/index.html').read_text())
    diagrams[number] = parser.figures
    assert len(parser.figures) == (1 if number == 1 else 3)
    assert all(f['legends'] == 1 for f in parser.figures), number
assert all('--diagram-base-fill' in n['fill'] for n in diagrams[1][0]['nodes'])
modified_stages = {2: {'execute'}, 3: set(), 4: {'permission-site'},
                   5: {'tools', 'handler'}, 6: {'tools', 'handler', 'system'}}
removed_stages = {6: {'reminder', 'todo-handler', 'todo-manager'}}
for number in range(2, 7):
    previous = diagrams[number - 1][0 if number == 2 else 1]
    baseline = diagrams[number][0]
    geometry = lambda nodes: [tuple(n.get(k) for k in
        ('data-stage', 'x', 'y', 'width', 'height')) for n in nodes]
    assert geometry(previous['nodes']) == geometry(baseline['nodes']), number
    assert previous['paths'] == baseline['paths'], number
    for node in baseline['nodes']:
        modified = node.get('data-stage') in modified_stages[number]
        removed = node.get('data-stage') in removed_stages.get(number, set())
        palette = 'removed' if removed else 'modified' if modified else 'base'
        assert f'--diagram-{palette}-fill' in node['fill'], (number, node)
        assert f'--diagram-{palette}-stroke' in node['stroke'], (number, node)
        if removed:
            assert node.get('data-view') == 'removed'
            assert node.get('stroke-dasharray') == '5 3'
        elif modified:
            assert node.get('data-view') == 'modified'
        else:
            assert 'data-view' not in node
    assert not any(word in baseline['text'] for word in
                   ('紫色', '新增', '本轮展开')), number
    assert any('--diagram-memory-fill' in n['fill'] for n in
               diagrams[number][1]['nodes']), number
for number in (3, 4, 5, 6):
    file_tools = [n for n in diagrams[number][1]['nodes']
                  if n.get('data-stage') == 'added-file-tools']
    assert len(file_tools) == 1, number
    assert '--diagram-base-fill' in file_tools[0]['fill'], number
    assert ('文件工具实现' if number < 6 else '工具实现') in diagrams[number][1]['text'], number
    if number == 6:
        assert file_tools[0]['x'] == '468' and file_tools[0]['y'] == '183'
        assert file_tools[0]['width'] == '112'
assert '名称 / 描述 / schema' in diagrams[3][1]['text']
assert '执行 Bash' in diagrams[2][0]['text']
assert '分发并执行' in diagrams[2][1]['text']
s02_page = (root / 's02/index.html').read_text()
assert '橙色：本轮将改造（仍是旧实现）' in s02_page
assert '橙色：修改／职责迁移' in s02_page
retired = [n for n in diagrams[6][1]['nodes'] if n.get('data-change') == 'removed']
assert not retired  # The current view keeps only a short S05 reference, not old internals.
assert all(name not in diagrams[6][1]['text'] for name in
           ('TodoManager', '计数与条件提醒'))
assert 'TODO → S05' in diagrams[6][1]['text']
assert '历史索引，本例未含' in diagrams[6][1]['text']
assert {'task', 'child-history', 'child-loop', 'child-return', 'child-context'} <= {
    node.get('data-stage') for node in diagrams[6][1]['nodes']}
assert '父循环同步等待' in diagrams[6][1]['text']
s06_page = (root / 's06/index.html').read_text()
assert '30 轮仍未结束' in s06_page
assert '额外调用模型' in s06_page
assert 'safe_path' not in s06_page
catalog = Architecture()
catalog.feed(s06_page)
expected_links = {
    base + 's02/#file-tool-implementation',
    base + 's05/#todo-tool-implementation',
}
assert set(catalog.diagram_links) == expected_links
for href in catalog.diagram_links:
    url, anchor = href.split('#')
    target = Architecture()
    target.feed((root / url.removeprefix(base) / 'index.html').read_text())
    assert anchor in target.ids, href
assert '工具实现' in diagrams[6][1]['text']
assert 'Shell 工具' not in diagrams[6][1]['text']
assert 'data-group="tool-implementations"' not in s06_page
for page in root.rglob('index.html'):
    parser = Architecture()
    parser.feed(page.read_text())
    assert all(f['legends'] == 1 for f in parser.figures), page
dependency = (root / 's10/index.html').read_text()
assert '绿色：已完成 completed' in dependency
assert '蓝色：进行中 in_progress' in dependency

# Skills is learned independently first, then connected back to the previous loop.
skill_overview = Architecture()
skill_overview.feed((root / 's07/index.html').read_text())
assert len(skill_overview.figures) == 1
assert 'skills-map' in skill_overview.ids
assert not {'handler', 'history', 'decision'} & {
    n.get('data-stage') for n in skill_overview.figures[0]['nodes']}
integration = Architecture()
integration.feed((root / 's07/09-agent-loop/index.html').read_text())
assert len(integration.figures) == 2
assert geometry(integration.figures[0]['nodes']) == geometry(diagrams[6][1]['nodes'])
assert integration.figures[0]['paths'] == diagrams[6][1]['paths']
assert '可见技能目录' in integration.figures[1]['text']
assert '交付正文' in integration.figures[1]['text']
assert 'Shell 工具' not in integration.figures[1]['text']

# S09 continues the S08 author overview; only its detail presentation is folded.
s08_view = Architecture()
s08_view.feed((root / 's08/index.html').read_text())
s09_view = Architecture()
s09_page = (root / 's09/index.html').read_text()
s09_view.feed(s09_page)
assert len(s09_view.figures) == 3, 'S09 needs previous/current/core views'
assert geometry(s09_view.figures[0]['nodes']) == geometry(s08_view.figures[1]['nodes'])
assert s09_view.figures[0]['paths'] == s08_view.figures[1]['paths']
for node in s09_view.figures[0]['nodes']:
    stage = node.get('data-stage')
    palette = 'modified' if stage in {'system', 'end'} else 'storage' if stage in {'summary', 'reactive'} else 'base'
    assert f'--diagram-{palette}-fill' in node['fill'], stage
assert {'memory-recall', 'memory-extract', 'memory-save', 'memory-consolidate', 'memory-store'} <= {
    n.get('data-stage') for n in s09_view.figures[1]['nodes']}
assert '每个用户回合一次' in s09_view.figures[1]['text']
s09_text = re.sub(r'<[^>]+>', '', s09_page)
assert 'def load_memories' in s09_text and 'def should_store_memory' in s09_text
assert 'data-diagram-explorer' in s09_page
for slug in ('03-invocation', '04-context', '07-subagents'):
    local_view = Architecture()
    local_view.feed((root / 's07' / slug / 'index.html').read_text())
    assert len(local_view.figures) == 1, slug

# Task System extends the same default author diagram, with memory details folded.
s10_view = Architecture()
s10_page = (root / 's10/index.html').read_text()
s10_view.feed(s10_page)
assert len(s10_view.figures) == 4, 'S10 needs previous/current/core views plus a dependency example'
assert geometry(s10_view.figures[0]['nodes']) == geometry(s09_view.figures[1]['nodes'])
assert s10_view.figures[0]['paths'] == s09_view.figures[1]['paths']
for node in s10_view.figures[0]['nodes']:
    stage = node.get('data-stage')
    palette = 'modified' if stage in {'system', 'tools', 'handler'} else 'storage' if stage in {
        'memory-extract', 'memory-save', 'memory-consolidate'} else 'base'
    assert f'--diagram-{palette}-fill' in node['fill'], stage
stages = {node.get('data-stage'): node for node in s10_view.figures[1]['nodes']}
assert {'task-tools', 'task-store', 'task-files', 'memory-recall', 'memory-persist', 'memory-store'} <= stages.keys()
assert not {'memory-extract', 'memory-save', 'memory-consolidate'} & stages.keys()
assert 'data-diagram-explorer' in s10_page and 's10-task-core' in s10_view.ids
assert '已有 Memory 入口、退出与存储接口' in s10_view.figures[0]['text']
assert '独立 S10 脚本实际保留 S04' in re.sub(r'<[^>]+>', '', s10_page)

s11_view = Architecture()
s11_page = (root / 's11/index.html').read_text()
s11_view.feed(s11_page)
assert len(s11_view.figures) == 3, 'S11 needs previous/current/core views'
assert geometry(s11_view.figures[0]['nodes']) == geometry(s10_view.figures[1]['nodes'])
assert s11_view.figures[0]['paths'] == s10_view.figures[1]['paths']
for node in s11_view.figures[0]['nodes']:
    stage = node.get('data-stage')
    palette = 'modified' if stage in {'prepare', 'tools', 'handler', 'system'} else 'storage' if stage in {
        'task-tools', 'task-store', 'task-files'} else 'base'
    assert f'--diagram-{palette}-fill' in node['fill'], stage
stages = {node.get('data-stage') for node in s11_view.figures[1]['nodes']}
assert {'background-start', 'background-worker', 'background-ready', 'background-collect'} <= stages
assert not {'task-tools', 'task-store', 'task-files'} & stages
assert '已有任务工具、记忆与原循环' in s11_view.figures[0]['text']
assert 's11-background-core' in s11_view.ids and 'run_in_background' in s11_page

s12_view = Architecture()
s12_page = (root / 's12/index.html').read_text()
s12_view.feed(s12_page)
assert len(s12_view.figures) == 3, 'S12 needs previous/current/core views'
assert geometry(s12_view.figures[0]['nodes']) == geometry(s11_view.figures[1]['nodes'])
assert s12_view.figures[0]['paths'] == s11_view.figures[1]['paths']
for node in s12_view.figures[0]['nodes']:
    stage = node.get('data-stage')
    palette = 'modified' if stage in {'model', 'decision', 'tools', 'system', 'handler', 'pre-event'} else 'storage' if stage in {
        'background-start', 'background-worker', 'background-ready'} else 'base'
    assert f'--diagram-{palette}-fill' in node['fill'], stage
assert {'cron-create', 'cron-poll', 'cron-queue', 'cron-idle', 'cron-deliver', 'cron-ack'} <= {
    node.get('data-stage') for node in s12_view.figures[1]['nodes']}
assert '已有后台命令与通知接口' in s12_view.figures[0]['text']
assert 's12-cron-core' in s12_view.ids and 'pending_delivery' in s12_page
for page in (root / 's07').rglob('index.html'):
    parsed = Architecture()
    parsed.feed(page.read_text())
    for href in parsed.diagram_links:
        url, _, fragment = href.partition('#')
        target_file = root / url.removeprefix(base) / 'index.html'
        assert target_file.exists(), (page, href)
        if fragment:
            target = Architecture()
            target.feed(target_file.read_text())
            assert fragment in target.ids, (page, href)

lab_root = Path('examples/s07-skills-lab')
lab_manifest = json.loads((lab_root / 'manifest.json').read_text())
appendix_text = (root / 's07/10-appendix/index.html').read_text()
appendix = Architecture()
appendix.feed(appendix_text)
assert appendix_text.count('class=skill-lab-file') == len(lab_manifest['files'])
for entry in lab_manifest['files']:
    assert entry['id'] in appendix.ids, entry['path']
    assert entry['chapters'] and entry['note'], entry['path']
    for chapter in entry['chapters']:
        assert (root / 's07' / chapter / 'index.html').exists(), chapter
archive_path = Path(sys.argv[1]) / 'downloads/s07-skills-lab.zip'
with zipfile.ZipFile(archive_path) as archive:
    expected = {'s07-skills-lab/' + entry['path'] for entry in lab_manifest['files']}
    assert set(archive.namelist()) == expected
    for entry in lab_manifest['files']:
        assert archive.read('s07-skills-lab/' + entry['path']) == (lab_root / entry['path']).read_bytes(), entry['path']
PY

for chapter in 01-structure 02-discovery 03-invocation 04-context 05-rendering 06-permissions 07-subagents 08-evaluation 09-agent-loop 10-appendix; do
  chapter_url="/projects/learn-claude-code/s07/$chapter/"
  chapter_page="$output_dir${chapter_url}index.html"
  test -f "$chapter_page"
  # 当前子章节应高亮，并在项目导航中展开 S07。
  grep -q "class=\"project-nav__link project-nav__link--active\" href=$chapter_url aria-current=page" "$chapter_page"
  grep -q 'class=project-nav__branch open' "$chapter_page"
  # 进入任一子章节后，仍能导航到九节主线和完整附录。
  for sibling in 01-structure 02-discovery 03-invocation 04-context 05-rendering 06-permissions 07-subagents 08-evaluation 09-agent-loop 10-appendix; do
    grep -q "href=/projects/learn-claude-code/s07/$sibling/" "$chapter_page"
  done
done

post_page="$output_dir/posts/hello-world/index.html"
if grep -q 'project-nav' "$post_page"; then
  echo "普通文章错误地显示了方向导航" >&2
  exit 1
fi

echo "project navigation checks passed"
