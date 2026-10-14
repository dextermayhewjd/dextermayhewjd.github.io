#!/usr/bin/env python3
"""Join cached official documentation with versioned repository inventories."""
import argparse
from collections import Counter, defaultdict
import csv
import io
import json
from pathlib import Path
import shlex
from urllib.parse import quote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
REPOSITORIES = ('slime', 'areal', 'verl')
COUNT_FIELDS = ('direct_calls', 'inferred_calls', 'references',
                'core_direct_calls', 'core_inferred_calls', 'core_references')
SELECTIVE = {
    'inspect': {'isawaitable', 'iscoroutine', 'iscoroutinefunction', 'isasyncgen',
                'isasyncgenfunction', 'getcoroutinestate', 'getcoroutinelocals',
                'getasyncgenstate', 'getasyncgenlocals', 'CO_COROUTINE',
                'CO_ITERABLE_COROUTINE', 'CO_ASYNC_GENERATOR', 'markcoroutinefunction'},
    'contextlib': {'asynccontextmanager', 'AsyncExitStack', 'AbstractAsyncContextManager',
                   'aclosing', 'nullcontext'},
    'types': {'coroutine', 'CoroutineType', 'AsyncGeneratorType'},
    'typing': {'Awaitable', 'Coroutine', 'AsyncIterable', 'AsyncIterator', 'AsyncGenerator',
               'AsyncContextManager'},
    'collections.abc': {'Awaitable', 'Coroutine', 'AsyncIterable', 'AsyncIterator', 'AsyncGenerator'},
    'functions': {'aiter', 'anext'},
    'exceptions': {'StopAsyncIteration', 'StopIteration', 'GeneratorExit', 'TimeoutError',
                   'ExceptionGroup', 'BaseExceptionGroup'},
    'time': {'sleep', 'monotonic', 'monotonic_ns', 'perf_counter', 'perf_counter_ns'},
    'unittest': {'IsolatedAsyncioTestCase'},
    'unittest.mock': {'AsyncMock'},
    'os': {'fork', 'forkpty', '_exit', 'kill', 'killpg', 'wait', 'waitpid', 'waitid',
           'wait3', 'wait4', 'register_at_fork', 'getpid', 'getppid', 'setsid', 'getsid',
           'setpgid', 'getpgid', 'getpgrp', 'setpgrp', 'pipe', 'pipe2', 'pidfd_open',
           'sched_yield', 'system', 'popen'},
    'fcntl': {'flock', 'lockf', 'LOCK_SH', 'LOCK_EX', 'LOCK_UN', 'LOCK_NB'},
    'datamodel': {'object.__await__', 'object.__aiter__', 'object.__anext__',
                  'object.__aenter__', 'object.__aexit__', 'coroutine.send',
                  'coroutine.throw', 'coroutine.close'},
}
INHERITANCE = {
    'concurrent.futures.ThreadPoolExecutor': 'concurrent.futures.Executor',
    'concurrent.futures.ProcessPoolExecutor': 'concurrent.futures.Executor',
    'asyncio.BoundedSemaphore': 'asyncio.Semaphore',
    'asyncio.PriorityQueue': 'asyncio.Queue',
    'asyncio.LifoQueue': 'asyncio.Queue',
    'asyncio.Task': 'asyncio.Future',
    'threading.Timer': 'threading.Thread',
    'queue.PriorityQueue': 'queue.Queue',
    'queue.LifoQueue': 'queue.Queue',
    'asyncio.TimerHandle': 'asyncio.Handle',
}


def normalize_api(name):
    if not name:
        return None
    if name.startswith(('loop.', 'asyncio.loop.')):
        return 'asyncio.AbstractEventLoop.' + name.split('loop.', 1)[1]
    if name.startswith('multiprocessing.context.BaseContext.'):
        name = 'multiprocessing.' + name.removeprefix('multiprocessing.context.BaseContext.')
    if name == 'multiprocessing.Pool' or name.startswith('multiprocessing.Pool.'):
        return name.replace('multiprocessing.Pool', 'multiprocessing.pool.Pool', 1)
    for prefix in ('asyncio.tasks.', 'asyncio.futures.', 'asyncio.queues.',
                   'asyncio.locks.', 'asyncio.runners.', 'asyncio.exceptions.'):
        if name.startswith(prefix):
            return 'asyncio.' + name[len(prefix):]
    if name in {'aiter', 'anext', 'StopAsyncIteration', 'StopIteration', 'GeneratorExit',
                'TimeoutError', 'ExceptionGroup', 'BaseExceptionGroup'}:
        return 'builtins.' + name
    return name


def symbol_in_scope(document, name):
    page = Path(urlsplit(document['url']).path).stem
    if page not in SELECTIVE:
        return True
    if page == 'datamodel':
        return name in SELECTIVE[page]
    short = name.removeprefix('builtins.').removeprefix(page + '.')
    if page == 'os' and short.startswith(('exec', 'spawn', 'posix_spawn')):
        return True
    return short.split('.', 1)[0] in SELECTIVE[page]


def blank_counts():
    return dict.fromkeys(COUNT_FIELDS, 0)


def add_count(counts, event):
    field = {'api_call': 'direct_calls', 'inferred_method': 'inferred_calls',
             'api_reference': 'references'}.get(event['kind'])
    if field is None:
        return
    counts[field] += 1
    if event.get('scope') == 'core':
        counts['core_' + field] += 1


def build_report_data(catalog, inventories):
    registry = {}
    documents = []
    for document in catalog['documents']:
        doc = dict(document, api_names=[], counts={r: blank_counts() for r in inventories})
        if document.get('status') == 'ok':
            for symbol in document.get('symbols', []):
                if not symbol_in_scope(document, symbol['name']):
                    continue
                name = normalize_api(symbol['name'])
                item = registry.setdefault(name, {
                    'name': name, 'docs': [], 'counts': {r: blank_counts() for r in inventories},
                    'occurrences': {r: [] for r in inventories},
                })
                reference = {'document': document['id'], **symbol}
                if reference not in item['docs']:
                    item['docs'].append(reference)
                if name not in doc['api_names']:
                    doc['api_names'].append(name)
        documents.append(doc)
    doc_by_id = {d['id']: d for d in documents}
    candidates, unmapped, syntax = [], [], defaultdict(Counter)
    repo_summary = {}
    for repo, inventory in inventories.items():
        seen = set()
        kinds = Counter()
        page_seen = defaultdict(set)
        for event in inventory['occurrences']:
            identifier = event['id']
            if identifier in seen:
                raise ValueError(f'Duplicate occurrence in {repo}: {identifier}')
            seen.add(identifier)
            kinds[event['kind']] += 1
            row = {'repo': repo, **event}
            if event['kind'] == 'instance_candidate' or event.get('resolution') == 'unresolved':
                candidates.append(row)
                continue
            if event['kind'] not in {'api_call', 'api_reference', 'inferred_method'}:
                if event['kind'] != 'import':
                    syntax[repo][event['kind']] += 1
                continue
            name = normalize_api(event.get('canonical_name') or event['name'])
            target = name
            if target not in registry:
                for child, parent in INHERITANCE.items():
                    if name.startswith(child + '.'):
                        alias = parent + name[len(child):]
                        if alias in registry:
                            target = alias
                            break
            if target not in registry:
                unmapped.append(row)
                continue
            api = registry[target]
            add_count(api['counts'][repo], event)
            api['occurrences'][repo].append(identifier)
            for doc_id in {d['document'] for d in api['docs']}:
                if identifier not in page_seen[doc_id]:
                    add_count(doc_by_id[doc_id]['counts'][repo], event)
                    page_seen[doc_id].add(identifier)
        repo_summary[repo] = {
            'source': inventory.get('source', {}), 'by_kind': dict(sorted(kinds.items())),
            'total_occurrences': len(seen),
        }
    return {
        'schema_version': 1,
        'counting_policy': 'Static source positions. Direct calls, inferred methods, references, imports, syntax and unresolved candidates stay separate. Document pages may overlap; never sum page rows as a repository total.',
        'requested_urls': catalog.get('requested_urls', []),
        'repositories': repo_summary, 'documents': documents,
        'apis': [registry[n] for n in sorted(registry)],
        'candidates': candidates, 'unmapped': unmapped,
        'syntax': {r: dict(sorted(c.items())) for r, c in syntax.items()},
        'selective_reference_scope': {k: sorted(v) for k, v in SELECTIVE.items()},
    }


def cell(value):
    return str(value).replace('&', '&amp;').replace('|', '&#124;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', ' ⏎ ')


def pack_counts(counts, core=False):
    prefix = 'core_' if core else ''
    return ' / '.join(str(counts[prefix + field]) for field in ('direct_calls', 'inferred_calls', 'references'))


def tsv(rows, columns):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=columns, delimiter='\t', lineterminator='\n', extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        writer.writerow({k: json.dumps(v, ensure_ascii=False, sort_keys=True) if isinstance(v, (dict, list)) else v
                         for k, v in row.items()})
    return stream.getvalue()


def render_reports(report, inventories):
    repos = list(inventories)
    outputs = {'report.json': json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n'}
    ok = [d for d in report['documents'] if d.get('status') == 'ok']
    errors = [d for d in report['documents'] if d.get('status') != 'ok']
    api_by_name = {a['name']: a for a in report['apis']}
    ids = {r: {e['id']: e for e in inventory['occurrences']} for r, inventory in inventories.items()}
    scan_command = 'python3 python-async-reference/tools/scan_repositories.py' + ''.join(
        ' \\\n  --repo ' + shlex.quote(repo + '=' + report['repositories'][repo]['source'].get('root', '/path/to/' + repo))
        for repo in repos)
    lines = [
        '# Asyncio 与并发处理：官方文档与三仓库用法统计', '',
        '这里只统计 Asyncio 与直接相关的并发处理：协程、任务、事件循环、线程/进程、执行器、同步、队列、并发 I/O 和异步协议辅助。普通文件操作、通用反射、数值运算及其他无关标准库 API 不纳入。',
        '官方文档目录与本地 Slime、AReaL、verl 的实际源码位置放在一起，用于确定需要学习哪些机制。', '',
        f'已保存 **{len(ok)} 个官方页面**，目录共记录 **{len(report["documents"])} 页**；抓取失败或不存在 **{len(errors)} 页**。',
        f'本次文档范围内保留 **{len(report["apis"])} 个规范化 API/协议条目**，包含使用次数为零的条目。', '',
        '## 1. 从这里进入', '',
        '1. [完整课程设置](curriculum.md)：8 模块、40 个最小单元，安排全部 82 项 API；[学习范围与顺序](learning-plan.md)保存选题依据，[82 项 API 表](current-api-plan.md)保存官网入口和覆盖统计。',
        '2. [官方网址与本地副本](OFFICIAL-DOCS.md)：含用户指定的 12 页和补充理由；[纯网址清单](official/urls.txt)。',
        '3. [按官方页面统计](TOPIC-USAGE.md)：先决定哪些主题值得学习，再进入逐页明细。',
        '4. [核心包 API 矩阵](CORE-API-USAGE.md) / [含测试与示例的完整矩阵](API-USAGE.md) / [TSV](api-usage.tsv)。',
        '5. [语言语法统计](SYNTAX-USAGE.md)：async def、await、async with、async for 等。',
        '6. [待核实的方法](UNRESOLVED.md) / [未匹配到本次文档条目的 API](UNMAPPED.md)。',
        '7. [统计与匹配规则](METHOD.md) / [机器可读汇总](report.json) / [验证记录](VALIDATION.md)。', '',
        '## 2. 固定源码版本', '',
        '| 仓库 | HEAD | 已跟踪 Python 文件 | 解析错误 | 逐条位置 |',
        '| --- | --- | ---: | ---: | --- |',
    ]
    for repo in repos:
        source = report['repositories'][repo]['source']
        files = source.get('files', [])
        count = source.get('tracked_python_file_count', len(files))
        bad = source.get('parse_errors', [])
        lines.append(f'| {repo} | `{source.get("head", "未记录")}` | {count} | {len(bad)} | [清单](repositories/{repo}/occurrences.tsv) · [JSON](repositories/{repo}/inventory.json) |')
    lines += ['', '这里的“次数”始终是静态源码位置，不是运行频率，也不是学习优先级。核心包与测试/示例分开保留；带接收者线索的方法不并入直接调用。', '',
              '文档固定为抓取时的 Python 3.16 开发版，具体版本与时间记录在目录中；本地源码并不因此被认为运行于 Python 3.16。零次只表示这次范围内未命中，不能推断接口无用。', '',
              '## 3. 重新收集与核对', '',
              '从项目根目录执行，源码仓库只读：', '', '```bash',
              'python3 python-async-reference/tools/collect_docs.py',
              scan_command,
              'python3 python-async-reference/tools/build_reports.py',
              'python3 -m unittest discover -s python-async-reference/tests -p "test_*.py"',
              '```', '', '已有快照离线检查：', '', '```bash',
              'python3 python-async-reference/tools/collect_docs.py --check',
              scan_command + ' \\\n  --check',
              'python3 python-async-reference/tools/build_reports.py --check', '```', '',
              '完整的 asyncio 文档目录与明确列出的相关页面构成本次边界；没有无限递归整个 Python 官网，也不声称覆盖所有第三方异步库。', '',
              'HTML 保存原始页面作为来源证据，没有额外打包官网的全部样式资源；离线阅读可直接打开正文 TXT。较大参考页的原始副本不等于其中所有 API 都进入统计。', '']
    outputs['README.md'] = '\n'.join(lines)
    lines = ['# 官方网址与本地副本', '',
             '所有链接限定为 Python 官方文档。相关标准库页面可能还包含大量非异步内容，覆盖字段与纳入理由区分这些范围。', '',
             '## 1. 用户指定的 12 页', '']
    by_url = {d['url'].rstrip('/'): d for d in report['documents']}
    for url in report['requested_urls']:
        doc = by_url.get(url.rstrip('/'))
        label = doc.get('title', url) if doc else url
        lines.append(f'- [{cell(label)}]({url}) — {doc.get("status", "未收集") if doc else "未收集"}')
    lines += ['', '## 2. 完整目录', '', '| 页面 | 范围与理由 | 本地副本 | 抓取记录 |', '| --- | --- | --- | --- |']
    for d in report['documents']:
        local = ' · '.join(f'[{label}]({quote(d[key], safe="/")})' for key, label in [('html_path', 'HTML'), ('text_path', '正文')] if d.get(key))
        reason = f'{d.get("category", "")} / {d.get("coverage", "")}：{d.get("reason", "")}'
        lines.append(f'| [{cell(d.get("title") or d["id"])}]({d["url"]}) | {cell(reason)} | {local or "—"} · [统计](topics/{d["id"]}.md) | {cell(d.get("status"))} · {cell(d.get("fetched_at", ""))} |')
    outputs['OFFICIAL-DOCS.md'] = '\n'.join(lines) + '\n'
    outputs['official/urls.txt'] = '\n'.join(d['url'] for d in report['documents']) + '\n'
    outputs['official/requested-urls.txt'] = '\n'.join(report['requested_urls']) + '\n'
    header = ['# 按官方页面统计', '', '**每格为：直接调用 / 有类型线索的方法调用 / 非调用引用。** 页面之间可能重叠，不可相加当成仓库总数。', '',
              'API 数为 0 的目录、指南、语言规则或命令行工具页面不作使用率判断；Python AST 扫描也不统计 shell/notebook 中的工具命令。']
    header += ['', '## 1. 核心包（不含测试、示例）', '',
               '| 官方页面 | 范围内 API 数 | ' + ' | '.join(repos) + ' |',
               '| --- | ---: | ' + ' | '.join('---' for _ in repos) + ' |']
    for doc in report['documents']:
        header.append(f'| [{cell(doc.get("title") or doc["id"])}](topics/{doc["id"]}.md) | {len(doc["api_names"])} | ' + ' | '.join(pack_counts(doc['counts'][r], core=True) for r in repos) + ' |')
    header += ['', '## 2. 全部已跟踪 Python 文件（含测试、示例）', '',
               '| 官方页面 | 范围内 API 数 | ' + ' | '.join(repos) + ' |',
               '| --- | ---: | ' + ' | '.join('---' for _ in repos) + ' |']
    for doc in report['documents']:
        header.append(f'| [{cell(doc.get("title") or doc["id"])}](topics/{doc["id"]}.md) | {len(doc["api_names"])} | ' + ' | '.join(pack_counts(doc['counts'][r]) for r in repos) + ' |')
    outputs['TOPIC-USAGE.md'] = '\n'.join(header) + '\n'
    matrix = ['# 逐 API 使用矩阵', '', '**每格为：直接调用 / 有类型线索的方法调用 / 非调用引用；含全部扫描范围。** 核心包次数另存 TSV。', '',
              '| API / 协议条目 | 官方出处 | ' + ' | '.join(repos) + ' |',
              '| --- | --- | ' + ' | '.join('---' for _ in repos) + ' |']
    rows = []
    for api in report['apis']:
        refs = api['docs']
        href = refs[0]['url']
        pages = ' · '.join(f'[{d}](topics/{d}.md)' for d in sorted({r['document'] for r in refs}))
        matrix.append(f'| [`{cell(api["name"])}`]({href}) | {pages} | ' + ' | '.join(pack_counts(api['counts'][r]) for r in repos) + ' |')
        row = {'api': api['name'], 'official_urls': [r['url'] for r in refs]}
        for repo in repos:
            row.update({repo + '_' + key: value for key, value in api['counts'][repo].items()})
        rows.append(row)
    outputs['API-USAGE.md'] = '\n'.join(matrix) + '\n'
    core_matrix = ['# 核心包 API 使用矩阵', '', '只含各仓库核心包，排除测试和示例。每格为：直接调用 / 推断方法 / 非调用引用。', '',
                   '| API / 协议条目 | ' + ' | '.join(repos) + ' |', '| --- | ' + ' | '.join('---' for _ in repos) + ' |']
    for api in report['apis']:
        core_matrix.append(f'| [`{cell(api["name"])}`]({api["docs"][0]["url"]}) | ' + ' | '.join(pack_counts(api['counts'][r], core=True) for r in repos) + ' |')
    outputs['CORE-API-USAGE.md'] = '\n'.join(core_matrix) + '\n'
    outputs['api-usage.tsv'] = tsv(rows, ['api', 'official_urls'] + [r + '_' + f for r in repos for f in COUNT_FIELDS])
    for doc in report['documents']:
        lines = [f'# {doc.get("title") or doc["id"]}', '', f'- 官方页面：{doc["url"]}',
                 f'- 抓取状态：{doc.get("status")}', f'- 纳入理由：{doc.get("reason", "")}',
                 f'- 范围：{doc.get("coverage", doc.get("category", ""))}', '',
                 '[总目录](../OFFICIAL-DOCS.md) · [跨主题统计](../TOPIC-USAGE.md)', '',
                 '## 1. 条目与调用位置数', '', '**每格为：直接调用 / 推断方法 / 非调用引用。**', '',
                 '| API / 协议条目 | ' + ' | '.join(repos) + ' |',
                 '| --- | ' + ' | '.join('---' for _ in repos) + ' |']
        for name in sorted(doc['api_names']):
            api = api_by_name[name]
            ref = next(r for r in api['docs'] if r['document'] == doc['id'])
            lines.append(f'| [`{cell(name)}`]({ref["url"]}) | ' + ' | '.join(pack_counts(api['counts'][r]) for r in repos) + ' |')
        if not doc['api_names']:
            lines += ['', '此页为概念、目录、语言规则或无已抽取 API 的页面；语法使用另见 [语言语法统计](../SYNTAX-USAGE.md)。']
        lines += ['', '## 2. 本地源码位置', '',
                  '| 仓库 / 范围 | API | 记录种类 | 源码位置 | 原代码 |',
                  '| --- | --- | --- | --- | --- |']
        for repo in repos:
            matched = {}
            for name in doc['api_names']:
                for identifier in api_by_name[name]['occurrences'][repo]:
                    matched[identifier] = (name, ids[repo][identifier])
            for name, event in sorted(matched.values(), key=lambda pair: (pair[1]['file'], pair[1]['line'], pair[1].get('col', 0))):
                snapshot = event.get('snapshot')
                local = '../repositories/' + repo + '/' + snapshot if snapshot else None
                label = cell(f'{event["file"]}:{event["line"]}')
                location = f'[{label}]({quote(local, safe="/")})' if local else label
                if event.get('source_url'):
                    location += f' · [固定版本]({event["source_url"]})'
                lines.append(f'| {repo} / {cell(event.get("scope", ""))} | `{cell(name)}` | {cell(event["kind"])} | {location} | {cell(event.get("source_line", ""))} |')
        outputs['topics/' + doc['id'] + '.md'] = '\n'.join(lines) + '\n'
    syntax_names = sorted({k for counts in report['syntax'].values() for k in counts})
    lines = ['# 语言语法统计', '', '以下按 AST 节点计数，独立于 API 调用。async def 与异步生成器定义分开，后者内部 yield 另计。', '',
             '| 语法类别 | ' + ' | '.join(repos) + ' |', '| --- | ' + ' | '.join('---:' for _ in repos) + ' |']
    for name in syntax_names:
        lines.append(f'| {name} | ' + ' | '.join(str(report['syntax'].get(r, {}).get(name, 0)) for r in repos) + ' |')
    outputs['SYNTAX-USAGE.md'] = '\n'.join(lines) + '\n'
    for key, title, intro in [
        ('candidates', 'UNRESOLVED', '以下方法缺乏足够接收者类型证据，不计入已确认 API。相同方法名不能证明是 asyncio。'),
        ('unmapped', 'UNMAPPED', '这些已识别名称未匹配到本次文档范围的具体条目。可能是范围外接口、别名或文档版本差异，不等于它不是标准库。'),
    ]:
        lines = [f'# {"待核实的方法" if key == "candidates" else "未匹配的 API"}', '', intro, '', '| 名称 | ' + ' | '.join(repos) + ' |', '| --- | ' + ' | '.join('---:' for _ in repos) + ' |']
        counts = Counter((e.get('canonical_name') or e['name'], e['repo']) for e in report[key])
        for name in sorted({name for name, _ in counts}):
            lines.append(f'| `{cell(name)}` | ' + ' | '.join(str(counts[(name, r)]) for r in repos) + ' |')
        lines += ['', '逐条记录见各仓库清单：' + ' · '.join(f'[{r}](repositories/{r}/{key}.tsv)' for r in repos), '']
        outputs[title + '.md'] = '\n'.join(lines)
        for repo in repos:
            rows = [e for e in report[key] if e['repo'] == repo]
            outputs[f'repositories/{repo}/{key}.tsv'] = tsv(rows, ['id', 'file', 'line', 'scope', 'kind', 'name', 'canonical_name', 'resolution', 'source_line', 'source_url', 'details'])
    for repo, inventory in inventories.items():
        outputs[f'repositories/{repo}/occurrences.tsv'] = tsv(inventory['occurrences'], [
            'id', 'file', 'line', 'end_line', 'col', 'end_col', 'scope', 'symbol', 'kind', 'category',
            'name', 'canonical_name', 'resolution', 'provenance', 'source_line', 'source_url', 'snapshot', 'details'])
    outputs['METHOD.md'] = '\n'.join([
        '# 统计与匹配规则', '',
        '1. 扫描范围以每个 Git 仓库的 git ls-files 为准，仅解析已跟踪 Python 文件；版本、工作区差异与逐文件哈希在 inventory.json 中。',
        '2. 调用、非调用引用、导入、语法节点分别计数。同一个调用表达式不再重复算成引用。',
        '3. 构造函数、已知工厂或注解提供的方法接收者线索放在 inferred_method；它们仍是静态推断，不是运行时类型证明。',
        '4. 同名但未知类型的方法只列为 instance_candidate。不把 Ray、HTTPX、aiohttp、业务对象的方法计成 asyncio。',
        '5. 官方 loop.method 展示名规范到 asyncio.AbstractEventLoop.method；已知执行器、队列子类的继承方法可映射到其基类文档。原名称和证据保留。',
        '6. inspect、contextlib、typing、collections.abc、builtins、unittest 等较大文档仅选择与异步相关的条目，选择集合保存在 report.json。',
        '7. 文档符号目录包含零命中 API。某 API 被多页描述时，页面统计会重叠；逐 API 总矩阵按规范名去重，不能累加页面数字当仓库总量。',
        '8. 文档之外的已识别 API 与未知接收者候选分别导出；二者不能相互替代。没有条目被悄悄丢弃。',
        '9. 这是静态清单：不证明分支实际执行、调用频率、并发正确性或学习掌握程度；不解析运行时 monkey patch、动态导入、任意跨函数数据流和反射。',
        '10. 本资料夹不运行模型、训练、GPU、远程 RPC 或部署；文档获取只访问 Python 官方站点。', ''])
    return outputs


def write_outputs(root, outputs, check=False):
    manifest_name = 'report-files.json'
    manifest = root / manifest_name
    previous = set(json.loads(manifest.read_text())['files']) if manifest.exists() else set()
    outputs = dict(outputs)
    outputs[manifest_name] = json.dumps({'files': sorted([*outputs, manifest_name])}, indent=2) + '\n'
    stale = previous - outputs.keys()
    differences = []
    for name, text in outputs.items():
        path = root / name
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Report path escapes its output folder')
        if check:
            if not path.is_file() or path.read_text() != text:
                differences.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    for name in stale:
        path = root / name
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Stale report path escapes its output folder')
        if path.is_file():
            if check:
                differences.append(name)
            else:
                path.unlink()
    return differences


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    catalog = json.loads((root / 'official/catalog.json').read_text())
    inventories = {r: json.loads((root / 'repositories' / r / 'inventory.json').read_text()) for r in REPOSITORIES}
    report = build_report_data(catalog, inventories)
    outputs = render_reports(report, inventories)
    differences = write_outputs(root, outputs, args.check)
    if differences:
        print('Report drift: ' + ', '.join(differences))
        return 1
    ok_urls = {d['url'].rstrip('/') for d in report['documents'] if d.get('status') == 'ok'}
    missing = [u for u in report['requested_urls'] if u.rstrip('/') not in ok_urls]
    if missing:
        print('Required official pages missing: ' + ', '.join(missing))
        return 1
    print(f'{len(outputs)} reports {"verified" if args.check else "written"}; {len(report["documents"])} official pages; {len(report["apis"])} API entries; {len(report["candidates"])} unresolved method records.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
