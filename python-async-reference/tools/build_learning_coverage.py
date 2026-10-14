#!/usr/bin/env python3
"""核算显式学习 API 清单覆盖的核心包静态调用位置，不推断场景覆盖率。"""

import argparse
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOS = ("slime", "areal", "verl")
LABELS = {"slime": "Slime", "areal": "AReaL", "verl": "verl"}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def fraction(count, total):
    return f"{count}/{total}（{100 * count / total:.1f}%）" if total else "0/0（无调用）"


def render(scope, report, inventories):
    registry = {api["name"]: api for api in report["apis"]}
    baseline = set(scope["baseline_apis"])
    selected = set(baseline)
    if len(baseline) != len(scope["baseline_apis"]):
        raise ValueError("Duplicate baseline API")
    for group in scope["supplements"]:
        names = set(group["apis"])
        if len(names) != len(group["apis"]) or names & selected:
            raise ValueError(f"Duplicate API in supplement: {group['id']}")
        selected.update(names)
    if missing := selected - registry.keys():
        raise ValueError(f"API not in official report registry: {sorted(missing)}")

    stats = {}
    for repo in REPOS:
        core = {
            event["id"]: event
            for event in inventories[repo]["occurrences"]
            if event["scope"] == "core"
            and event["kind"] in {"api_call", "inferred_method"}
        }

        def occurrences(names):
            return {
                identifier
                for name in names
                for identifier in registry[name]["occurrences"][repo]
                if identifier in core
            }

        covered = occurrences(baseline)
        before = set(covered)
        groups = {}
        for group in scope["supplements"]:
            added = occurrences(group["apis"]) - covered
            groups[group["id"]] = added
            covered.update(added)
        async_core = {
            identifier for identifier, event in core.items()
            if (event.get("canonical_name") or "").startswith("asyncio.")
        }
        stats[repo] = dict(
            core=core, before=before, after=covered, groups=groups,
            async_core=async_core, remaining=core.keys() - covered,
        )

    lines = [
        f"# {len(selected)} 项 API 选题清单的调用位置覆盖与缺口",
        "",
        "由 `tools/build_learning_coverage.py` 生成；选题与 API 清单维护在 [learning-scope.json](learning-scope.json)。",
        "",
        "这是**阶段性选题清单覆盖了多少已识别静态调用位置**，不是课程完成度、运行频率或实际场景覆盖率。核算对应 [learning-plan.md](learning-plan.md) 第 4.2 节；当前具体 API 以 [82 项清单](current-api-plan.md)为准，本页 53 项保留为历史基线。",
        "",
        "## 1. 同一统计口径下的前后变化",
        "",
        f"原清单明确列出 {len(baseline)} 个 API 名称，补充 {len(selected) - len(baseline)} 个。构造对象与调用对象的方法分别匹配，不因列了 `Thread` 就自动算上 `Thread.start`。",
        "",
        "| 仓库 | 原清单 / 全部相关调用 | 补充后 / 全部相关调用 | 原清单 / asyncio 调用 | 补充后 / asyncio 调用 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for repo, data in stats.items():
        before, after, core, async_core = (
            data[key] for key in ("before", "after", "core", "async_core")
        )
        lines.append(
            f"| {LABELS[repo]} | {fraction(len(before), len(core))} | "
            f"{fraction(len(after), len(core))} | "
            f"{fraction(len(before & async_core), len(async_core))} | "
            f"{fraction(len(after & async_core), len(async_core))} |"
        )
    lines += [
        "",
        "1. 分母是固定清单中 `scope=core` 且 `kind` 为 `api_call` 或 `inferred_method` 的去重记录；包括已识别但尚未映射到官方文档的调用。",
        "2. 分子按 `report.json` 的 API → occurrence ID 映射与分母取交集，沿用别名和继承方法的文档映射；不按网页计数相加。",
        "3. 导入、单纯引用、语法节点、类型不明的候选不计入分子或分母。`TimeoutError` 本组次数来自异常构造调用，`except TimeoutError` 等引用另计。",
        "4. 仅覆盖本资料夹选定的标准库异步与并发范围；Ray、HTTP 客户端、torch.distributed 及业务编排不在这个百分比里。",
        "5. 原清单是此前估算百分比时的显式 API 集合，不是全部现有课程索引。补充项可能在旧课中已有内容，仍需按学习规划核对深度。原生异步与并发路线中未列入该清单的内容，不能沿用此比例声称已经覆盖。",
        "",
        "## 2. 补充的操作与新增调用位置",
        "",
        "表格按概念位置排列；同一行可拆成多个最小学习单元，不表示要新加一整章。",
        "",
        "| 补充内容 | API | Slime | AReaL | verl | 官方入口 |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for group in scope["supplements"]:
        counts = " | ".join(str(len(stats[r]["groups"][group["id"]])) for r in REPOS)
        apis = "、".join(f"`{name}`" for name in group["apis"])
        links = "、".join(f"[文档 {i}]({url})" for i, url in enumerate(group["official_urls"], 1))
        lines.append(f"| {group['title']} | {apis} | {counts} | {links} |")
    lines += [
        "",
        "零调用的方法仍可能是解释生命周期的必要配套，例如 `Thread.join` 与 `Event.clear`；它们不增加该仓库的分子。低频配套只讲必要关系，不扩大为完整模块导读。",
        "",
        "<details>",
        "<summary>按需核对：各补充组的源码例子</summary>",
        "",
    ]
    for group in scope["supplements"]:
        lines += [f"### {group['title']}", "", group["placement"], ""]
        for repo, data in stats.items():
            examples = sorted(
                (data["core"][i] for i in data["groups"][group["id"]]),
                key=lambda event: (event["file"], event["line"], event["id"]),
            )
            if examples:
                event = examples[0]
                source = inventories[repo]["source"]
                url = f"{source['repository']}/blob/{source['head']}/{event['file']}#L{event['line']}"
                lines.append(f"- {LABELS[repo]}：[{event['file']}:{event['line']}]({url})，`{event['canonical_name']}`。")
            else:
                lines.append(f"- {LABELS[repo]}：本组没有新增调用位置。")
        lines.append("")
    lines += ["</details>", "", "## 3. 补充后仍留下什么", ""]
    lines += [
        "以下展示每库剩余调用最多的前 8 项，用于按需回查；不自动纳入必读路线。次数按原始规范名显示。",
        "",
        "| 仓库 | 剩余位置 | 主要剩余调用（次数） |",
        "| --- | ---: | --- |",
    ]
    for repo, data in stats.items():
        counts = Counter(data["core"][i]["canonical_name"] for i in data["remaining"])
        top = sorted(counts.items(), key=lambda row: (-row[1], row[0]))[:8]
        description = "、".join(f"`{name}`（{count}）" for name, count in top)
        lines.append(f"| {LABELS[repo]} | {len(data['remaining'])} | {description} |")
    lines += [
        "",
        "Slime 的后续按需范围包括可重入锁/条件变量、手动事件循环、同步队列与信号。verl 的信号超时和 AReaL 的进程/执行器配套也保留为源码驱动的后续补充。`os.getpid` 等辅助调用计入分母，但无需为提高比例单独开课。",
        "",
        "## 4. 固定来源与复算", "",
    ]
    for repo in REPOS:
        source = inventories[repo]["source"]
        lines.append(f"- {LABELS[repo]}：`{source['head']}`，[逐条清单](repositories/{repo}/inventory.json)。")
    lines += [
        "", "```bash",
        "python3 python-async-reference/tools/build_learning_coverage.py",
        "python3 python-async-reference/tools/build_learning_coverage.py --check",
        "```", "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render(
        read_json(ROOT / "learning-scope.json"),
        read_json(ROOT / "report.json"),
        {repo: read_json(ROOT / "repositories" / repo / "inventory.json") for repo in REPOS},
    )
    destination = ROOT / "learning-coverage.md"
    if args.check:
        if not destination.exists() or destination.read_text(encoding="utf-8") != content:
            raise SystemExit("Stale learning-coverage.md; run build_learning_coverage.py")
        print("Learning coverage is up to date.")
    else:
        destination.write_text(content, encoding="utf-8")
        print(f"Wrote {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
