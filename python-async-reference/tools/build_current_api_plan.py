#!/usr/bin/env python3
"""Generate the current native async/concurrency API plan and its static coverage."""

import argparse
from collections import Counter

from api_usage_data import LABELS, REPOS, ROOT, load_usage, read_json
from build_learning_coverage import fraction


def render():
    plan = read_json(ROOT / "current-api-plan.json")
    registry, loaded_inventories = load_usage()
    groups = plan["api_groups"]
    names = [name for group in groups for name in group["apis"]]
    if len(names) != len(set(names)):
        raise ValueError("API occurs in more than one learning group")
    if missing := set(names + plan["exception_types"]) - registry.keys():
        raise ValueError(f"Names missing from official registry: {sorted(missing)}")
    old = read_json(ROOT / plan['expansion']['baseline'])
    old_names = {name for group in old['api_groups'] for name in group['apis']}
    expansion = plan['expansion']
    additions = [name for group in expansion['selected_groups'] for name in group['apis']]
    additions += expansion['required_companions']
    if len(additions) != len(set(additions)) or set(names) != old_names | set(additions) or old_names & set(additions):
        raise ValueError('Expansion must preserve the baseline and introduce each addition once')
    if not old_names <= set(names):
        raise ValueError("Current plan unexpectedly removed a baseline API")

    inventories, core, counts, old_counts = {}, {}, {}, {}
    for repo in REPOS:
        inventories[repo] = loaded_inventories[repo]
        core[repo] = {
            event["id"]: event for event in inventories[repo]["occurrences"]
            if event["scope"] == "core"
            and event["kind"] in {"api_call", "inferred_method"}
        }

    def matching(repo, selected):
        return {
            identifier for name in selected
            for identifier in registry[name]["occurrences"][repo]
            if identifier in core[repo]
        }

    for repo in REPOS:
        counts[repo] = matching(repo, names)
        old_counts[repo] = matching(repo, old_names)

    total = sum(len(core[repo]) for repo in REPOS)
    covered = sum(len(counts[repo]) for repo in REPOS)
    old_covered = sum(len(old_counts[repo]) for repo in REPOS)
    headers = ' | '.join(LABELS[repo] for repo in REPOS)

    lines = [
        "# 当前要学的 Python 原生异步与并发 API",
        "",
        "依据 [current-api-plan.json](current-api-plan.json) 与四库固定清单生成。只处理 Python 原生异步与并发；课程安排及逐 API 单元映射见 [curriculum.md](curriculum.md)。",
        "",
        "## 1. 结论与统计范围",
        "",
        f"当前清单为 **{len(names)} 项调用/方法**：保留原 {len(old_names)} 项，纳入六组共 11 项接口，以及 4 项必要配套操作。语法和异常类型另列。",
        "",
        f"**四库按调用量加权：{fraction(covered, total)}**；扩充前为 {fraction(old_covered, total)}。先把四库的调用位置数相加再相除，不取四个覆盖率的算术平均，也不按 API 种类数计算。",
        "",
        f"| 仓库 | 原 {len(old_names)} 项覆盖 / 全部相关调用 | 当前 {len(names)} 项覆盖 / 全部相关调用 | 新覆盖位置 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for repo in REPOS:
        lines.append(
            f"| {LABELS[repo]} | {fraction(len(old_counts[repo]), len(core[repo]))} | "
            f"{fraction(len(counts[repo]), len(core[repo]))} | "
            f"{len(counts[repo] - old_counts[repo])} |"
        )
    lines += [
        "",
        f"四库合计新增 {covered - old_covered} 个调用位置。70%–80% 是原先的选题目标，不是删去必要操作来维持的上限。",
        "",
        "1. 分母沿用原统计：核心包中已识别的原生异步/并发及其配套标准库调用，含有类型线索的方法推断。测试、示例、导入、语法节点、单纯引用与未知类型候选不计入。",
        "2. 分子以显式调用/方法名匹配 `report.json` 的 occurrence ID，与分母取交集并去重。类构造与各方法分开列出；继承方法沿用官方文档映射。",
        "3. 这是静态调用位置覆盖，不是运行频率、实际场景覆盖率、全仓代码覆盖率或已经掌握的比例。四个框架的第三方 API 不在分母中。",
        "4. 下表的零调用不表示不学：`async with` 的隐式获取/释放、装饰器引用等不算显式调用，必要配套仍列入。",
        "",
        "## 2. 本次纳入的六组与必要配套",
        "",
        "按四库使用次数筛选范围，按概念依赖安排顺序；必要操作不因零调用而隐藏。这里是课程规划，不表示新增子课已经写完。",
        "",
        f"| 内容 | 新增接口 | {headers} | 合计 | 占全部调用 |",
        '| --- | --- | ' + ' | '.join('---:' for _ in REPOS) + ' | ---: | ---: |',
    ]
    for group in expansion['selected_groups'] + [{'title': '必要配套：运行、关闭循环与完成 Future', 'apis': expansion['required_companions']}]:
        totals = [len(matching(repo, group['apis'])) for repo in REPOS]
        apis = '、'.join(f'`{name}`' for name in group['apis'])
        lines.append(f'| {group["title"]} | {apis} | ' + ' | '.join(map(str, totals)) + f' | {sum(totals)} | {sum(totals) / total:.2%} |')
    lines += [
        "",
        "六组覆盖 74 个新增调用位置；4 项必要配套再覆盖 7 个，共新增 81 个。`AsyncExitStack.pop_all` 继承的接口说明位于 [ExitStack.pop_all](https://docs.python.org/3.16/library/contextlib.html#contextlib.ExitStack.pop_all)；从原始清单补回该映射，不改变原三库报告和四库调用总数。",
        "",
        "## 3. 按概念依赖学习的完整调用/方法表",
        "",
        "一行是概念组，不是一课；同组也按最小心智模型拆开。前三组中的 TaskGroup 先学正常退出，取消之后再回看失败路径。",
        "",
        f"| 学习内容 | 明确要学的调用/方法 | {headers} | 官方页面 |",
        '| --- | --- | ' + ' | '.join('---:' for _ in REPOS) + ' | --- |',
    ]
    for group in groups:
        apis = "、".join(f"`{name}`" for name in group["apis"])
        totals = " | ".join(str(len(matching(repo, group["apis"]))) for repo in REPOS)
        links = "、".join(f"[文档 {index}]({url})" for index, url in enumerate(group["urls"], 1))
        lines.append(f"| {group['title']} | {apis} | {totals} | {links} |")
    lines += ["", *[f"{i}. {note}" for i, note in enumerate(plan["learning_depth"], 1)], ""]
    lines += [
        "## 4. 语法和异常类型另列",
        "",
        "语法：" + "、".join(f"`{item}`" for item in plan["syntax"]) + "。",
        "",
        "异常类型：" + "、".join(f"`{item}`" for item in plan["exception_types"]) + "。",
        "",
        "这些必须能辨认和处理，但不把 `await`、`except` 等位置塞进 API 调用分子。`TimeoutError(...)` 的构造已在前表明确列出；其他类型不因为会捕获就自动算作会构造。",
        "",
        "<details>",
        "<summary>逐 API 核对：调用位置数</summary>",
        "",
        f"| API | {headers} |",
        '| --- | ' + ' | '.join('---:' for _ in REPOS) + ' |',
    ]
    for name in names:
        totals = " | ".join(str(len(matching(repo, [name]))) for repo in REPOS)
        lines.append(f"| `{name}` | {totals} |")
    lines += ["", "</details>", "", "## 5. 未覆盖内容与后续边界", ""]
    lines += [
        "| 仓库 | 剩余位置 | 剩余调用最多的 8 项 |",
        "| --- | ---: | --- |",
    ]
    for repo in REPOS:
        remaining = core[repo].keys() - counts[repo]
        counter = Counter(core[repo][identifier]["canonical_name"] for identifier in remaining)
        top = sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:8]
        description = "、".join(f"`{name}`（{total}）" for name, total in top)
        lines.append(f"| {LABELS[repo]} | {len(remaining)} | {description} |")
    lines += [
        "",
        "主要按需范围：Condition/RLock、进程间队列、进程池、信号/进程组、文件锁与更低层 I/O。`os.getpid` 等辅助调用仍在原分母中，不为了增加分子单独开课。",
        "",
        f"当前 {len(names)} 项不声称列完标准库的每个 API。原 82 项范围保留在 [api-plan-82.json](api-plan-82.json)，原 53 项核算保留在 [learning-coverage.md](learning-coverage.md)。",
        "",
        "## 6. 固定来源与复算",
        "",
    ]
    for repo in REPOS:
        source = inventories[repo]["source"]
        lines.append(f"- {LABELS[repo]}：`{source['head']}`，[原始位置清单](repositories/{repo}/inventory.json)。")
    lines += [
        "", "```bash",
        "python3 python-async-reference/tools/build_current_api_plan.py",
        "python3 python-async-reference/tools/build_current_api_plan.py --check",
        "```", "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    destination = ROOT / "current-api-plan.md"
    content = render()
    if args.check:
        if not destination.exists() or destination.read_text(encoding="utf-8") != content:
            raise SystemExit("Stale current-api-plan.md; run build_current_api_plan.py")
        print("Current API plan is up to date.")
    else:
        destination.write_text(content, encoding="utf-8")
        print(f"Wrote {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
