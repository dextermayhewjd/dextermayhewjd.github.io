#!/usr/bin/env python3
"""Map every fixed-snapshot inventory entry to a real tutorial explanation.

Reads the original scanner outputs without modifying them. Unknown receiver
methods stay candidates: a lesson destination is not a runtime type proof.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

MATERIAL = Path(__file__).resolve().parents[1]
CONTENT = MATERIAL.parent / 'content/projects/python-async-concurrency'


def read_json(name):
    return json.loads((MATERIAL / name).read_text())


def make_coverage():
    inventory = read_json('inventory.json')
    config = read_json('teaching-topics.json')
    topics = config['topics']
    by_api, by_method, by_syntax, by_import = {}, {}, {}, {}
    by_id = {}
    for topic in topics:
        if topic['id'] in by_id:
            raise ValueError('Duplicate topic id: ' + topic['id'])
        by_id[topic['id']] = topic
        page = CONTENT / topic['lesson'] / 'index.md'
        if not page.exists() or 'id="' + topic['anchor'] + '"' not in page.read_text():
            raise ValueError('Missing teaching anchor: ' + topic['lesson'] + '#' + topic['anchor'])
        for field, table in [('apis', by_api), ('methods', by_method),
                             ('syntax', by_syntax), ('imports', by_import)]:
            for key in topic.get(field, []):
                table.setdefault(key, topic)
    candidate_topic = by_id[config['candidate_topic']]
    rows = []
    for source in inventory['occurrences']:
        kind, name = source['kind'], source['name']
        status = 'explained'
        receiver_type = None
        if kind == 'instance_candidate':
            evidence = source['details'].get('receiver_evidence')
            if evidence:
                receiver_type = evidence['type']
                key = receiver_type + '.' + name
                if key not in by_method:
                    raise ValueError('Unexplained inferred receiver method: ' + key)
                topic, status = by_method[key], 'inferred'
            else:
                topic, status = candidate_topic, 'candidate'
        elif kind in ('api_call', 'api_reference'):
            if name not in by_api:
                raise ValueError('Unexplained direct API: ' + name)
            topic = by_api[name]
        elif kind == 'import':
            if name not in by_import and name not in by_api:
                raise ValueError('Unexplained import: ' + name)
            topic = by_import.get(name) or by_api[name]
        else:
            if kind not in by_syntax:
                raise ValueError('Unexplained syntax: ' + kind)
            topic = by_syntax[kind]
        row = {key: source[key] for key in (
            'id', 'file', 'line', 'end_line', 'kind', 'name', 'source_line',
            'source_url', 'snapshot', 'symbol',
        )}
        row.update(topic_id=topic['id'], lesson=topic['lesson'],
                   anchor=topic['anchor'], status=status,
                   receiver_type=receiver_type,
                   receiver=source.get('details', {}).get('receiver'))
        rows.append(row)
    docs = read_json('documentation-snippets.json')
    snippets = []
    names = {'async def': 'async_def', 'await': 'await', 'async with': 'async_with',
             'async for': 'async_for', 'yield': 'async_yield'}
    for snippet in docs['snippets']:
        topic_ids = []
        for syntax in snippet['native_python_syntax']:
            if syntax in names:
                topic_ids.append(by_syntax[names[syntax]]['id'])
        for api, topic in by_api.items():
            if '.' in api and api in snippet['snippet']:
                topic_ids.append(topic['id'])
        topic_ids = list(dict.fromkeys(topic_ids))
        if not topic_ids:
            raise ValueError('Unmapped documentation snippet: ' + snippet['id'])
        snippets.append(dict(snippet, topic_ids=topic_ids))
    candidate_counts = Counter(row['name'] for row in rows if row['status'] == 'candidate')
    candidate_methods = []
    for name, count in sorted(candidate_counts.items()):
        related = [topic['id'] for topic in topics
                   if topic['id'] != candidate_topic['id']
                   and any(method.rsplit('.', 1)[-1] == name for method in topic.get('methods', []))]
        candidate_methods.append({'name': name, 'count': count, 'related_topic_ids': related})
    topic_counts = Counter(row['topic_id'] for row in rows)
    statuses = Counter(row['status'] for row in rows)
    return {
        'schema_version': 1,
        'source_revision': inventory['source']['head'],
        'scope': 'All scanned tracked Python positions and the separately inventoried Markdown snippets; no runtime completeness claim.',
        'counts': {'tracked_python_files': inventory['source']['tracked_python_file_count'],
                   'source_positions': len(rows), 'direct_api_names': len(by_api.keys() & inventory['summary']['by_api'].keys()),
                   'direct_api_positions': sum(row['kind'] in ('api_call', 'api_reference') for row in rows),
                   'syntax_positions': sum(row['kind'] not in ('api_call', 'api_reference', 'import', 'instance_candidate') for row in rows),
                   'import_positions': sum(row['kind'] == 'import' for row in rows),
                   'documentation_snippets': len(snippets), **dict(statuses)},
        'topics': [dict(topic, source_positions=topic_counts[topic['id']]) for topic in topics],
        'occurrences': rows,
        'candidate_methods': candidate_methods,
        'documentation_snippets': snippets,
    }


def markdown(coverage):
    counts = coverage['counts']
    lines = ['# 源码用法与教程对照', '',
             '固定源码：`' + coverage['source_revision'] + '`。', '',
             f"{counts['source_positions']} 条静态位置均有教程去向；{counts['direct_api_positions']} 个直接 API 位置和 {counts['syntax_positions']} 个语法位置逐项映射。", '',
             '对象方法的 inferred/candidate 标记保留原扫描器的证据强度，不能把有讲解入口等同于运行时类型证明。', '',
             '| 讲解 | API / 实例方法 / 语法 | 源码位置数 |', '| --- | --- | ---: |']
    for topic in coverage['topics']:
        identifiers = topic.get('apis', []) + topic.get('methods', []) + topic.get('syntax', [])
        label = ', '.join('`' + name + '`' for name in identifiers) or '源码类型与第三方边界'
        target = '/projects/python-async-concurrency/' + topic['lesson'] + '/#' + topic['anchor']
        lines.append(f"| [{topic['title']}]({target}) | {label} | {topic['source_positions']} |")
    lines += ['', '## 原始记录', '',
              '[完整映射 JSON](/python-async-concurrency/teaching-coverage.json) 保留每条 ID、源文件、行号、原代码行、源码链接与教程锚点。', '',
              f"另外 {counts['documentation_snippets']} 段 Markdown 中的代码保留完整原文与讲解去向，区别于实际 `.py` 文件。", '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        coverage = make_coverage()
    except (ValueError, KeyError, FileNotFoundError) as error:
        print(error, file=sys.stderr)
        return 1
    outputs = {'teaching-coverage.json': json.dumps(coverage, ensure_ascii=False, indent=2) + '\n',
               'teaching-coverage.md': markdown(coverage)}
    for name, data in outputs.items():
        path = MATERIAL / name
        if args.check:
            if not path.exists() or path.read_text() != data:
                print('Coverage drift: ' + str(path), file=sys.stderr)
                return 1
        else:
            path.write_text(data)
    print('OK: ' + str(coverage['counts']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
