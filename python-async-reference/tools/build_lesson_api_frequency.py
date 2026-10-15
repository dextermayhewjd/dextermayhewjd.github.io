#!/usr/bin/env python3
"""Render the complete curriculum's APIs and syntax at their first introduction."""
import argparse
import ast
from html import escape
from itertools import groupby
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from api_usage_data import REPOS, LABELS, call_statistics, load_usage

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'lesson-api-frequency.md'
TOTAL_SHARE_PERCENT = 1
REPO_COUNT_THRESHOLD = 10


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def frequency_marks(counts, denominator):
    values = list(counts.values())
    combined = sum(values) if all(value is not None for value in values) else None
    return {
        'total_high': bool(denominator and combined is not None
                           and combined * 100 >= denominator * TOTAL_SHARE_PERCENT),
        'repo_high': {repo for repo, value in counts.items()
                      if value is not None and value >= REPO_COUNT_THRESHOLD},
    }


def highlighted(value, category, description):
    return (f'<span class="api-frequency-mark api-frequency-mark--{category}" '
            f'title="{escape(description, quote=True)}" '
            f'aria-label="{escape(description, quote=True)}">{escape(str(value))}</span>')


def sources():
    plan = read_json(ROOT / 'curriculum.json')
    registry, inventories = load_usage()
    return plan, registry, inventories


def cleanup_syntax_counts(source):
    """Count cleanup blocks and except* clauses in async function bodies only."""
    class Counter(ast.NodeVisitor):
        def __init__(self):
            self.in_async = False
            self.counts = {'try/finally': 0, 'except*': 0}

        def visit_body(self, node, in_async):
            previous = self.in_async
            self.in_async = in_async
            for statement in node.body:
                self.visit(statement)
            self.in_async = previous

        def visit_AsyncFunctionDef(self, node):
            self.visit_body(node, True)

        def visit_FunctionDef(self, node):
            self.visit_body(node, False)

        def visit_ClassDef(self, node):
            self.visit_body(node, False)

        def visit_Try(self, node):
            if self.in_async and node.finalbody:
                self.counts['try/finally'] += 1
            self.generic_visit(node)

        def visit_TryStar(self, node):
            if self.in_async:
                self.counts['except*'] += len(node.handlers)
                if node.finalbody:
                    self.counts['try/finally'] += 1
            self.generic_visit(node)

    counter = Counter()
    counter.visit(ast.parse(source))
    return counter.counts


def snapshot_cleanup_counts(repo, inventory):
    paths = {event['snapshot'] for event in inventory['occurrences']
             if event['scope'] == 'core' and event['kind'] in ('async_def', 'async_generator_def')}
    total = {'try/finally': 0, 'except*': 0}
    for path in sorted(paths):
        counts = cleanup_syntax_counts((ROOT / 'repositories' / repo / path).read_text(encoding='utf-8'))
        for name in total:
            total[name] += counts[name]
    return total


def build_rows():
    plan, registry, inventories = sources()
    rows = []
    syntax_kinds = {
        'async def': 'async_def', 'await': 'await', 'async with': 'async_with',
        'async for': 'async_for', '异步生成器中的 yield': 'async_yield',
    }
    cleanup = {repo: snapshot_cleanup_counts(repo, inventories[repo]) for repo in REPOS}

    def syntax_row(name):
        if name not in syntax_kinds:
            return dict(api=name, kind='语法位置', counts={repo: cleanup[repo][name] for repo in REPOS})
        counts = {repo: sum(event['scope'] == 'core' and event['kind'] == syntax_kinds[name]
                            for event in inventories[repo]['occurrences']) for repo in REPOS}
        return dict(api=name, kind='语法位置', counts=counts)

    for lesson in plan['lessons']:
        number = lesson['number']
        # Basic syntax precedes the API it makes readable in lessons 01, 02 and 04.
        items = [syntax_row(name) for name in lesson['syntax'] if name in syntax_kinds]
        for name in lesson['introduces']:
            decorator = name == 'contextlib.asynccontextmanager'
            counts = {}
            for repo in REPOS:
                data = registry[name]['counts'][repo]
                counts[repo] = data['core_references'] if decorator else data['core_direct_calls'] + data['core_inferred_calls']
            items.append(dict(api=name, kind='装饰器引用' if decorator else '调用位置', counts=counts))
        items.extend(syntax_row(name) for name in lesson['syntax'] if name not in syntax_kinds)
        for index, item in enumerate(items, 1):
            rows.append(dict(lesson=number, index=index, **item))
        if not items:
            name = '回访 ' + ' / '.join(lesson['revisits']) + '；处理失败与 return_exceptions'
            rows.append(dict(lesson=number, index=None, api=name, kind='无新增 API', counts=dict.fromkeys(REPOS)))
    return rows


def lesson_usage(rows):
    """Count all first-introduced knowledge points together for course weighting."""
    members = [row for row in rows if row['kind'] != '无新增 API']
    if not members:
        return dict.fromkeys(REPOS)
    return {repo: sum(row['counts'][repo] for row in members) for repo in REPOS}


def format_counts(counts, denominator):
    marks = frequency_marks(counts, denominator)
    values = [
        '—' if counts[repo] is None else
        highlighted(counts[repo], 'repo', f'{LABELS[repo]}：{counts[repo]} 次，单库次数 ≥ {REPO_COUNT_THRESHOLD}')
        if repo in marks['repo_high'] else str(counts[repo])
        for repo in REPOS
    ]
    combined = sum(counts.values()) if all(value is not None for value in counts.values()) else None
    combined_label = '—' if combined is None else str(combined)
    share = '复用前课' if combined is None else f'{combined / denominator:.2%}' if denominator else '—'
    if marks['total_high']:
        combined_label = highlighted(combined_label, 'total', f'四库合计 {combined}，同类占比 ≥ {TOTAL_SHARE_PERCENT}%')
        share = highlighted(share, 'total', f'同类占比 {share}，达到 {TOTAL_SHARE_PERCENT}% 标注线')
    return values, combined_label, share


def format_lesson_ranges(numbers):
    ranges = []
    for _, items in groupby(enumerate(sorted(numbers)), lambda item: item[1] - item[0]):
        group = [number for _, number in items]
        ranges.append(f'{group[0]:02d}' if len(group) == 1 else f'{group[0]:02d}–{group[-1]:02d}')
    return '、'.join(ranges)


def render():
    plan, registry, inventories = sources()
    lessons = {lesson['number']: lesson for lesson in plan['lessons']}
    stages = {number: stage['id'] for stage in plan['stages']
              for number in range(stage['first'], stage['last'] + 1)}
    api_count = len({api for lesson in lessons.values() for api in lesson['introduces']})
    syntax_count = len({syntax for lesson in lessons.values() for syntax in lesson['syntax']})
    ready = [number for number, lesson in lessons.items() if lesson['status'] == 'existing']
    planned = [number for number, lesson in lessons.items() if lesson['status'] == 'planned']
    progress = f'**{format_lesson_ranges(ready)} 已整理；{format_lesson_ranges(planned)} 待编写。**' if planned else '**全部课程均已整理。**'
    rows = build_rows()
    selected = {api for lesson in lessons.values() for api in lesson['introduces']}
    stats = call_statistics(registry, inventories, selected)
    total = sum(len(item['core']) for item in stats.values())
    covered = sum(len(item['covered']) for item in stats.values())
    syntax_total = sum(sum(row['counts'].values()) for row in rows if row['kind'] == '语法位置')
    reference_total = sum(event['scope'] == 'core' and event['kind'] == 'api_reference'
                          for inventory in inventories.values() for event in inventory['occurrences'])
    denominators = {'调用位置': total, '语法位置': syntax_total, '装饰器引用': reference_total}
    # Include identified usage outside the chosen curriculum in the denominator.
    knowledge_total = total + syntax_total + reference_total
    first_lesson_total = sum(lesson_usage([row for row in rows if row['lesson'] == 1]).values())
    baseline = read_json(ROOT / 'api-plan-82.json')
    before = call_statistics(registry, inventories, {name for group in baseline['api_groups'] for name in group['apis']})
    before_count = sum(len(item['covered']) for item in before.values())
    lines = [
        f'**按完整课程规划的 {len(lessons)} 个编号单元排列，包含全部 {api_count} 项 API / 方法 / 装饰器和 {syntax_count} 项语法。** 每项只放在首次正式引入的课程中，同一课只在第一行显示课号。第 10 课回访 gather；第 11 课回访 TaskGroup，并首次正式引入 `except*`，不重复计入已有 API。',
        '',
        progress + ' 后续课程先列出规划中的接口及使用次数，列入本表不表示教程已经写完；“待编写”课号链接到对应模块的课程规划。',
        '',
        '数字来自四个仓库固定快照的**核心包静态位置**，排除测试和示例；不是程序运行时的执行频率。每个 API 单独一行，构造与方法分开。单项明细保留调用、语法、引用的统计口径；课程占比统一按知识点出现次数计算。',
        '',
        f'**四库按调用量加权：{covered}/{total}（{covered / total:.1%}）**；扩充前 82 项为 {before_count}/{total}（{before_count / total:.1%}）。分子是所选接口对应的去重调用位置数，分母是四库全部已识别相关调用位置数，不平均四个仓库的百分比。新增子课仍待编写，具体安排见[完整课程规划](/projects/python-async-concurrency/learning-route/)。',
        '',
        f'每个统计项都给出“四库合计”和“占同类总量”：**调用位置除以 {total}**，**语法位置除以本表七项语法的合计 {syntax_total}**，**装饰器引用除以已识别 API 引用的合计 {reference_total}**。分母随“统计口径”而定，三类百分比不相加；调用占比保持原口径。第 10 课只是复用前课，标为“复用前课”，不重复计数。窄屏可左右滑动查看合计和百分比。',
        '',
        f'**怎样看整节课：** 最右侧“本课占比”把同课各项的四库使用次数相加，再除以四库整体统计总量，跨本课所有明细行显示一次。当前统一分母为 **{total} 个 API 调用位置 + {syntax_total} 个语法位置 + {reference_total} 个 API 引用位置 = {knowledge_total}**；其中调用和引用包含尚未选入课程的接口，语法沿用本表七类统计范围。例如第 1 课把 `async def` 和 `asyncio.run` 一起计算：**{first_lesson_total} / {knowledge_total} = {first_lesson_total / knowledge_total:.2%}**。原有单项占比保持不变，不平均四个仓库的百分比。',
        '',
        '“本课占比”与单项“占同类总量”的分母不同：前者看本课组合占整体统计范围的比例，后者保留各类明细的原口径。同一行代码涉及多个知识点时分别计数；因此它不是去重代码行覆盖率，也不是运行时执行频率。课程尚未包含所有已识别接口，各课占比不需要加到 100%。复习旧 API 不再次计数，纯复习课标为“复用前课”。',
        '',
        '颜色图例：' + highlighted(f'同类占比 ≥ {TOTAL_SHARE_PERCENT}%', 'total', '蓝色标注：四库合计占同类总量至少 1%')
        + ' 标蓝色合计与占比；' + highlighted(f'单库次数 ≥ {REPO_COUNT_THRESHOLD}', 'repo', '橙色标注：单个仓库的次数至少 10')
        + ' 标橙色单库数字。右侧“本课占比”达到 1% 时同样标蓝，但使用课程份额的分母；该列用底色和分隔线区分。',
        '',
        '**学习提示：** 课程占比帮助判断哪些知识点整体更常出现，适合增加练习和源码对照；低频不等于不重要，取消、清理、异常与必要前置仍按课程顺序学习。',
        '',
        '<div class="api-frequency-table-wrap" tabindex="0" role="region" aria-label="课程 API 频率表，窄屏可左右滚动">',
        '<table class="api-frequency-table">',
        '<colgroup><col class="frequency-col-lesson"><col class="frequency-col-api"><col class="frequency-col-kind">'
        + '<col class="frequency-col-repo">' * len(REPOS)
        + '<col class="frequency-col-value"><col class="frequency-col-value">'
        + '<col class="frequency-col-course"></colgroup>',
        '<thead><tr><th rowspan="2" scope="col">课号</th>'
        '<th colspan="8" scope="colgroup">单项 API / 语法</th>'
        '<th rowspan="2" scope="col" class="api-frequency-course-heading">本课占比</th></tr>',
        '<tr><th scope="col">本课新增 API / 语法</th><th scope="col">统计口径</th>'
        + ''.join(f'<th scope="col">{LABELS[repo]}</th>' for repo in REPOS)
        + '<th scope="col">四库合计</th><th scope="col">占同类总量</th></tr></thead>',
    ]
    for number, grouped_rows in groupby(rows, key=lambda row: row['lesson']):
        lesson_rows = list(grouped_rows)
        lesson = lessons[number]
        if lesson['status'] == 'existing':
            target = f'/projects/python-async-concurrency/{lesson["source_lessons"][0]}/'
            title = f'{number:02d}'
        else:
            target = f'/projects/python-async-concurrency/learning-route/#curriculum-stage-{stages[number]}'
            title = f'{number:02d}'
        lesson_label = escape(title)
        if lesson['status'] == 'planned':
            lesson_label += '<span class="api-frequency-status">待编写</span>'
        lines.append(f'<tbody data-lesson="{number}">')
        for index, row in enumerate(lesson_rows):
            cells = ['<tr>']
            if index == 0:
                cells.append(f'<th class="api-frequency-lesson" scope="rowgroup" rowspan="{len(lesson_rows)}">'
                             f'<a href="{escape(target, quote=True)}">{lesson_label}</a></th>')
            name = escape(row['api'])
            if row['kind'] != '无新增 API':
                name = f'<code>{name}</code>'
            cells.append(f'<td class="api-frequency-api">{name}</td>')
            cells.append(f'<td class="api-frequency-kind">{row["kind"]}</td>')
            values, combined, share = format_counts(row['counts'], denominators.get(row['kind']))
            cells.extend(f'<td class="api-frequency-repo">{value}</td>' for value in values)
            cells.append(f'<td class="api-frequency-total">{combined}</td>')
            cells.append(f'<td class="api-frequency-share">{share}</td>')
            if index == 0:
                _, _, course_share = format_counts(lesson_usage(lesson_rows), knowledge_total)
                cells.append(f'<td class="api-frequency-course-share" rowspan="{len(lesson_rows)}">'
                             + course_share + '</td>')
            cells.append('</tr>')
            lines.append(''.join(cells))
        lines.append('</tbody>')
    lines.extend(['</table>', '</div>'])

    example_decorators = sum(event['scope'] == 'examples'
                             and event['kind'] == 'api_reference'
                             and event['canonical_name'] == 'contextlib.asynccontextmanager'
                             for event in inventories['slime']['occurrences'])
    lines += [
        '',
        '1. `0` 表示本次静态统计未识别到该类位置；`—` 表示尚未统计或不适用，不能理解为零次使用。未知接收者的方法不强行归到 asyncio。',
        '2. `Semaphore`、`Lock` 通过 `async with` 隐式获取和释放的行为，不算显式 `acquire/release` 调用。',
        '3. 第 21 课常用 `@asynccontextmanager`，所以单独统计装饰器引用；其显式调用在四库均为 0。'
        f'Slime 核心包为 0，但示例目录另有 {example_decorators} 处。',
        '4. `async def` 不含单独归类的异步生成器定义。`try/finally`、`except*` 从同一固定版本的核心包源码快照补查：只计协程和异步生成器函数体内的 finally 代码块、except* 子句，排除其中嵌套普通函数与类体的同步代码。零命中也显示 0.00%；异常类型另按课程内容学习。',
        '5. Miles 的核心包范围为 `miles/`；`miles_plugins/`、入口脚本、测试和示例另存于扫描清单。类成员的接收者类型未能确定时，方法只进入候选清单；例如源码中的某些 Event/Condition 操作不能据表内的 0 判断为不存在。参见 [Miles 的异步并发用法](/projects/python-async-concurrency/miles-async-usage/)。',
        '6. `AsyncExitStack.pop_all` 继承自退出栈基类，文档入口位于 `ExitStack.pop_all`；本表从原始清单补回这项映射，不修改原三库报告或调用总数。',
        '',
        '固定源码版本：' + '；'.join(f'{repo} `{inventories[repo]["source"]["head"][:12]}`' for repo in REPOS) + '。',
        '',
        '本表由 `curriculum.json`、原三库 `report.json`、各库 `inventory.json` 及 Miles 的 `api-counts.json` 生成；Miles 沿用相同的 API 归一化规则，课程归属继续以 `curriculum.json` 为准。',
        '',
    ]
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    content = render()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding='utf-8') != content:
            raise SystemExit('Stale lesson-api-frequency.md; run build_lesson_api_frequency.py')
        rows = build_rows()
        print(f'Lesson frequency verified: {len({row["lesson"] for row in rows})} units, '
              f'{sum(row["kind"] in ("调用位置", "装饰器引用") for row in rows)} APIs and '
              f'{sum(row["kind"].startswith("语法位置") for row in rows)} syntax items at first introduction.')
    else:
        OUTPUT.write_text(content, encoding='utf-8')
        print(f'Wrote {OUTPUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
