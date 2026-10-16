#!/usr/bin/env python3
"""Check every selected API has a teaching unit and render the staged curriculum."""

import argparse
from collections import Counter
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT.parent / "content/projects/python-async-concurrency"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_plan(curriculum, scope):
    expected = {name for group in scope["api_groups"] for name in group["apis"]}
    lessons = curriculum["lessons"]
    if [row["number"] for row in lessons] != list(range(1, len(lessons) + 1)):
        raise ValueError("Lesson numbers must be consecutive")
    introduced = Counter(name for row in lessons for name in row["introduces"])
    if set(introduced) != expected or any(count != 1 for count in introduced.values()):
        raise ValueError(
            f"API coverage mismatch: missing={sorted(expected - introduced.keys())}, "
            f"extra={sorted(introduced.keys() - expected)}, "
            f"duplicates={sorted(name for name, count in introduced.items() if count != 1)}"
        )
    if curriculum["target_api_count"] != len(expected):
        raise ValueError("Declared API count does not match current API scope")
    previous = set()
    owners = {}
    for row in lessons:
        number = row["number"]
        if any(not isinstance(dep, int) or not 1 <= dep < number for dep in row["depends_on"]):
            raise ValueError(f"Future or invalid prerequisite in lesson {number}")
        if set(row["revisits"]) - previous:
            raise ValueError(f"Revisit before formal introduction in lesson {number}")
        for field in ("title", "question", "takeaway", "check"):
            if not row[field].strip():
                raise ValueError(f"Empty {field} in lesson {number}")
        if "parts" in row:
            parts = row["parts"]
            if row["status"] == "partial":
                states = {part.get("status") for part in parts}
                if states != {"existing", "planned"}:
                    raise ValueError(f"Partial unit needs existing and planned sublessons: {number}")
                if any(part["status"] == "existing" and not part["source_lessons"] for part in parts):
                    raise ValueError(f"Existing sublesson needs a source page: {number}")
            labels = [f"{number}.{index}" for index in range(1, len(parts) + 1)]
            if len(parts) < 2 or [part["label"] for part in parts] != labels:
                raise ValueError(f"Invalid sublesson order in lesson {number}")
            sources = [slug for part in parts for slug in part["source_lessons"]]
            if sources != row["source_lessons"] or len(sources) != len(set(sources)):
                raise ValueError(f"Invalid sublesson source mapping in lesson {number}")
            earlier_parts = set()
            part_apis = Counter(name for part in parts for name in part.get('introduces', []))
            if part_apis != Counter(row['introduces']):
                raise ValueError(f'Invalid sublesson API mapping in lesson {number}')
            for part in parts:
                for field in ("title", "question", "takeaway", "check"):
                    if not part[field].strip():
                        raise ValueError(f"Empty sublesson {field} in lesson {number}")
                for dep in part.get("depends_on", row["depends_on"]):
                    if not ((isinstance(dep, int) and 1 <= dep < number) or dep in earlier_parts):
                        raise ValueError(f"Invalid sublesson prerequisite in lesson {number}")
                earlier_parts.add(part["label"])
            for field in ("syntax", "exception_types"):
                expanded = {name for part in parts for name in part.get(field, row[field])}
                if expanded != set(row[field]):
                    raise ValueError(f"Invalid sublesson {field} mapping in lesson {number}")
        previous.update(row["introduces"])
        owners.update({name: number for name in row["introduces"]})
    for field in ("syntax", "exception_types"):
        covered = {name for row in lessons for name in row[field]}
        if covered != set(scope[field]):
            raise ValueError(f"Incomplete or unexpected {field}: {covered ^ set(scope[field])}")
    staged = [number for stage in curriculum["stages"] for number in range(stage["first"], stage["last"] + 1)]
    if staged != list(range(1, len(lessons) + 1)):
        raise ValueError("Stages must partition the complete ordered curriculum")
    expected_first = [
        "01-async-def", "02-await", "03-tasks", "04-with-async-with", "04-taskgroup", "05-gather",
    ]
    if [row["source_lessons"] for row in lessons[:6]] != [[slug] for slug in expected_first]:
        raise ValueError("The syntax prerequisite must precede TaskGroup in the first six lessons")
    return owners


def code_list(names):
    return "、".join(f"`{name}`" for name in names)


def display_lessons(row):
    """Expand reading parts without changing the parent unit or API ownership."""
    return [
        {**row, **part}
        for part in row.get("parts", [{"label": f"{row['number']:02d}"}])
    ]


def render_body(curriculum, manifest, web=False):
    pages = manifest["lessons"] + manifest.get("curriculum_lessons", [])
    titles = {row["slug"]: row["title"] for row in pages}
    # Reused page URLs and the legacy catalog retain their historical numbering.
    # Active units use the current curriculum title everywhere in this table.
    titles.update({
        row['source_lessons'][0]: f"{row['label']} · {row['title']}"
        for unit in curriculum['lessons']
        for row in display_lessons(unit)
        if row['status'] == 'existing' and row['source_lessons']
    })
    lessons = {row["number"]: row for row in curriculum["lessons"]}
    lines = [
        "## 分阶段课程",
        "",
        "| 模块 | 学习单元 | 每阶段先解决什么 | 首次正式讲解的 API 数 |",
        "| --- | --- | --- | ---: |",
    ]
    for i, stage in enumerate(curriculum["stages"], 1):
        count = sum(len(lessons[n]["introduces"]) for n in range(stage["first"], stage["last"] + 1))
        lines.append(
            f"| {i}. {stage['title']} | {stage['first']:02d}–{stage['last']:02d} | "
            f"{stage['focus']} | {count} |"
        )
    lines += ["", "下面按模块展开。每个单元都列出唯一问题、正式引入的 API、前置和自查；同一 API 后续复用不重复计数。", ""]
    for i, stage in enumerate(curriculum["stages"], 1):
        rows = [
            part for n in range(stage["first"], stage["last"] + 1)
            for part in display_lessons(lessons[n])
        ]
        lines += [
            f'<details id="curriculum-stage-{stage["id"]}">',
            f"<summary>模块 {i} · {stage['title']}（{stage['first']:02d}–{stage['last']:02d}）</summary>",
            "",
            "| 单元 | 本次新增的问题 | 正式引入的 API / 语法 | 前置单元 |",
            "| --- | --- | --- | --- |",
        ]
        for row in rows:
            mechanism = code_list(row["introduces"] + row["syntax"])
            if row["revisits"]:
                mechanism += ("；" if mechanism else "") + "回访 " + code_list(row["revisits"])
            if not mechanism:
                mechanism = "复用已有语法，增加新的行为关系"
            deps = "、".join(f"{n:02d}" if isinstance(n, int) else n for n in row["depends_on"]) or "普通函数基础"
            lines.append(f"| {row['label']} · {row['title']} | {row['question']} | {mechanism} | {deps} |")
        lines += ["", "<details>", "<summary>本模块的原子结论与自查</summary>", ""]
        for row in rows:
            lines += [
                f"### {row['label']} · {row['title']}", "",
                f"1. **带走：** {row['takeaway']}",
                f"2. **自查：** {row['check']}",
            ]
            if row["exception_types"]:
                lines.append("3. **需要辨认的异常：** " + code_list(row["exception_types"]) + "。")
            if row["prerequisite_notes"]:
                lines += ["", *row["prerequisite_notes"]]
            lines.append("")
        lines += ["</details>", "", "<details>", "<summary>可复用的旧课材料与编写状态</summary>", ""]
        for row in rows:
            sources = []
            for slug in row["source_lessons"]:
                url = f"/projects/python-async-concurrency/{slug}/" if web else f"../content/projects/python-async-concurrency/{slug}/index.md"
                sources.append(f"[{titles[slug]}]({url})")
            status = "已有独立学习主线" if row["status"] == "existing" else "规划单元，待从旧课拆分或补写"
            reference = "材料：" + "、".join(sources) + "。" if sources else "待按本单元问题编写独立材料。"
            lines.append(f"- {row['label']}：{status}。" + reference)
        lines += ["", "</details>", "", "</details>", ""]
    return "\n".join(lines)


def build_outputs():
    curriculum = read_json(ROOT / "curriculum.json")
    scope = read_json(ROOT / "current-api-plan.json")
    manifest = read_json(ROOT.parent / "python-async-concurrency/project-manifest.json")
    owners = validate_plan(curriculum, scope)
    for row in curriculum["lessons"]:
        for slug in row["source_lessons"]:
            if not (CONTENT / slug / "index.md").exists():
                raise ValueError(f"Missing reusable lesson: {slug}")
    introduction = [
        "# Python 原生异步与并发：完整课程设置", "",
        f"**{len(curriculum['stages'])} 个模块，{len(curriculum['lessons'])} 个编号单元，覆盖 {len(owners)}/{len(owners)} 项调用与方法。**",
        "",
        f"这是课程规划，不是 {len(curriculum['lessons'])} 篇都已编写完成的声明。各单元编写状态见下表。旧版 23 页目录保留历史编号，既有 URL 保留；现行单元号以本课程表为准。",
        "",
        f"输入范围：[{len(owners)} 项 API](current-api-plan.md)；唯一课程数据：[curriculum.json](curriculum.json)。课程按概念递进；每学完一个模块完成对应自查，不要求先记住整张清单。",
        "",
        "## 阅读与完成规则", "",
        *[f"{i}. {note}" for i, note in enumerate(curriculum["notes"], 1)],
        "5. 每单元先写前课结论，再给新增要求；机制实验只增加当前必要关系。纯语法前置的结构示意标明不能直接运行，再由下一单元的完整实验验证。",
        "6. 模块结束能解释该模块的正常、失败或退出行为；全课结束再串联一个只含已学原生机制的综合例子。",
        "7. API 正式讲解必须解释对象、调用时机、返回值以及必要的等待/异常/退出边界；仅在代码中出现不算完成讲解。",
        "",
    ]
    audit = ["", "## API 到正式讲解单元的检查表", "", "| API | 正式讲解单元 |", "| --- | --- |"]
    for group in scope["api_groups"]:
        for name in group["apis"]:
            unit = curriculum['lessons'][owners[name] - 1]
            part = next(part for part in display_lessons(unit) if name in part['introduces'])
            audit.append(f"| `{name}` | {part['label']} · {part['title']} |")
    audit += ["", "## 语法与异常的检查表", "", "| 类别 | 内容 | 单元 |", "| --- | --- | --- |"]
    for field, label in (("syntax", "语法"), ("exception_types", "异常类型")):
        for name in scope[field]:
            units = "、".join(
                row['label'] for unit in curriculum["lessons"]
                for row in display_lessons(unit) if name in row[field]
            )
            audit.append(f"| {label} | `{name}` | {units} |")
    audit += [
        "", "检查保证所有输入 API 各有一个正式引入单元，语法与异常类型无遗漏，前置只指向更早单元。它不证明待编写课程的正文已经实现了这些讲解。",
        "", "```bash", "python3 python-async-reference/tools/build_curriculum.py",
        "python3 python-async-reference/tools/build_curriculum.py --check", "```", "",
    ]
    return {
        ROOT / "curriculum.md": "\n".join(introduction) + "\n" + render_body(curriculum, manifest) + "\n".join(audit),
        ROOT / "curriculum-web.md": render_body(curriculum, manifest, web=True),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build_outputs()
    for path, content in outputs.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Stale curriculum output: {path.name}")
        else:
            path.write_text(content, encoding="utf-8")
    if args.check:
        curriculum = read_json(ROOT / 'curriculum.json')
        print(f"Curriculum verified: {len(curriculum['lessons'])} units, "
              f"{curriculum['target_api_count']}/{curriculum['target_api_count']} APIs, "
              "complete syntax and exception mapping.")
    else:
        print("Wrote curriculum.md and curriculum-web.md")


if __name__ == "__main__":
    main()
