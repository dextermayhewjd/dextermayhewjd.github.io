#!/usr/bin/env python3
"""Generate the current native async/concurrency API plan and its static coverage."""

import argparse
from collections import Counter

from build_learning_coverage import LABELS, REPOS, ROOT, fraction, read_json


def render():
    plan = read_json(ROOT / "current-api-plan.json")
    registry = {api["name"]: api for api in read_json(ROOT / "report.json")["apis"]}
    groups = plan["api_groups"]
    names = [name for group in groups for name in group["apis"]]
    if len(names) != len(set(names)):
        raise ValueError("API occurs in more than one learning group")
    if missing := set(names + plan["exception_types"]) - registry.keys():
        raise ValueError(f"Names missing from official registry: {sorted(missing)}")
    old = read_json(ROOT / "learning-scope.json")
    old_names = set(old["baseline_apis"]) | {
        name for group in old["supplements"] for name in group["apis"]
    }
    if not old_names <= set(names):
        raise ValueError("Current plan unexpectedly removed a baseline API")

    inventories, core, counts, old_counts = {}, {}, {}, {}
    for repo in REPOS:
        inventories[repo] = read_json(ROOT / "repositories" / repo / "inventory.json")
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

    lines = [
        "# 当前要学的 Python 原生异步与并发 API",
        "",
        "依据 [current-api-plan.json](current-api-plan.json) 与固定三库清单生成；重算命令见末尾。只处理 Python 原生异步与并发，测试、日志和业务框架不作为独立选题。完整课程安排及逐 API 单元映射见 [curriculum.md](curriculum.md)。",
        "",
        "## 1. 结论与统计范围",
        "",
        f"原来的 {len(old_names)} 项调用/方法清单已达到每库至少 70%，但漏列队列、通知、执行器退出等必要操作。当前补齐为 **{len(names)} 项调用/方法**，另列异常类型和语言语法。该范围足以作为本轮学习清单；剩余机制在读到相应源码时再补。",
        "",
        "| 仓库 | 原 53 项覆盖 / 全部相关调用 | 当前 82 项覆盖 / 全部相关调用 | 新覆盖位置 |",
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
        "Slime 与 verl 位于 70%–80% 区间，AReaL 为 83.6%，略高于目标；不为把比例压回 80% 而删掉必要方法。这里满足的是“至少 70%、大约 80%”的选题覆盖目标。",
        "",
        "1. 分母沿用原统计：核心包中已识别的原生异步/并发及其配套标准库调用，含有类型线索的方法推断。测试、示例、导入、语法节点、单纯引用与未知类型候选不计入。",
        "2. 分子以显式调用/方法名匹配 `report.json` 的 occurrence ID，与分母取交集并去重。类构造与各方法分开列出；继承方法沿用官方文档映射。",
        "3. 这是静态调用位置覆盖，不是运行频率、实际场景覆盖率、全仓代码覆盖率或已经掌握的比例。三个框架的第三方 API 不在分母中。",
        "4. 下表的零调用不表示不学：`async with` 的隐式获取/释放、装饰器引用等不算显式调用，必要配套仍列入。",
        "",
        "## 2. 按概念依赖学习的完整调用/方法表",
        "",
        "一行是概念组，不是一课；同组也按最小心智模型拆开。前三组中的 TaskGroup 先学正常退出，取消之后再回看失败路径。",
        "",
        "| 学习内容 | 明确要学的调用/方法 | Slime | AReaL | verl | 官方页面 |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for group in groups:
        apis = "、".join(f"`{name}`" for name in group["apis"])
        totals = " | ".join(str(len(matching(repo, group["apis"]))) for repo in REPOS)
        links = "、".join(f"[文档 {index}]({url})" for index, url in enumerate(group["urls"], 1))
        lines.append(f"| {group['title']} | {apis} | {totals} | {links} |")
    lines += ["", *[f"{i}. {note}" for i, note in enumerate(plan["learning_depth"], 1)], ""]
    lines += [
        "## 3. 语法和异常类型另列",
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
        "| API | Slime | AReaL | verl |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name in names:
        totals = " | ".join(str(len(matching(repo, [name]))) for repo in REPOS)
        lines.append(f"| `{name}` | {totals} |")
    lines += ["", "</details>", "", "## 4. 未覆盖内容与后续边界", ""]
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
        "主要按需范围：手动事件循环生命周期、Condition/RLock、进程间队列、进程池、信号/进程组、文件锁与更低层 I/O。`os.getpid` 等辅助调用仍在原分母中，不为了增加分子单独开课。",
        "",
        "当前 82 项是本轮原生基础清单，不声称列完标准库的每个 API。源码中遇到上述剩余机制时再展开；基础语法与方法的解释仍需包括结果、异常、取消和退出边界。",
        "",
        "## 5. 固定来源与复算",
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
