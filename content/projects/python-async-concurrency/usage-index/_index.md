---
title: "全部用法索引"
description: "按原生机制查看完整位置，区分语法、直接 API 和对象方法候选。"
weight: 900
hideMeta: true
hideSummary: true
---

先按问题学习，再用这里回查源码。当前统计覆盖 Slime 固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的 **381 个 Python 文件**，其中 90 个文件含目标记录。

| 统计口径 | 数量 |
| --- | ---: |
| 协程函数定义 | 281 |
| 异步生成器定义 | 7 |
| await 表达式 | 409 |
| async with | 42 |
| async for | 1 |
| 直接标准库 API 调用 | 433 |
| 非调用 API 引用 | 85 |
| 待核实的对象方法候选 | 876 |

这些是静态源码位置，不是运行次数。导入、语法、API 引用和候选分别计数；对象方法不能只凭名字断定类型，候选不混入直接 API 总数。

[源码用法与教程对照](../coverage/)把各 API、语法和对象方法接到具体讲解；每章末尾也能展开对应的全部源码位置。

## 按机制查找

| 分类 | 导入 | 调用 | 引用 | 语法 | 候选 |
| --- | ---: | ---: | ---: | ---: | ---: |
| [异步语法](syntax/) | 0 | 0 | 0 | 747 | 0 |
| [asyncio 任务与事件循环](asyncio/) | 39 | 246 | 28 | 0 | 0 |
| [线程与同步](threading/) | 23 | 46 | 2 | 0 | 0 |
| [同步队列](queue/) | 2 | 2 | 3 | 0 | 0 |
| [执行器与 Future](executors/) | 13 | 20 | 3 | 0 | 0 |
| [多进程](multiprocessing/) | 6 | 10 | 1 | 0 | 0 |
| [外部命令](subprocess/) | 15 | 27 | 27 | 0 | 0 |
| [系统信号](signal/) | 4 | 6 | 7 | 0 | 0 |
| [任务上下文](contextvars/) | 2 | 3 | 2 | 0 | 0 |
| [异步上下文辅助](contextlib-async/) | 3 | 0 | 3 | 0 | 0 |
| [异步对象检查](inspect-async/) | 2 | 2 | 0 | 0 | 0 |
| [异步内置函数](async-builtins/) | 0 | 0 | 0 | 0 | 0 |
| [异步类型标记](async-typing/) | 3 | 0 | 4 | 0 | 0 |
| [同步休眠](time-sleep/) | 23 | 35 | 0 | 0 | 0 |
| [进程控制辅助](os-process/) | 9 | 32 | 0 | 0 | 0 |
| [文件锁](fcntl/) | 2 | 3 | 5 | 0 | 0 |
| [I/O 就绪等待](select/) | 1 | 1 | 0 | 0 | 0 |
| [协程装饰辅助](coroutine-helpers/) | 0 | 0 | 0 | 0 | 0 |
| [待核实的对象方法](candidates/) | 0 | 0 | 0 | 0 | 876 |

## 下载原始清单

- [逐条位置 TSV](/python-async-concurrency/inventory.tsv)：用表格工具筛选文件、函数与机制。
- [完整 JSON](/python-async-concurrency/inventory.json)：包含行号、识别来源和哈希。
- [统计 JSON](/python-async-concurrency/summary.json)与[按 API 的完整统计](/python-async-concurrency/STATISTICS.md)。
- [文档中的 29 段 Python 示例](/python-async-concurrency/DOCUMENTATION-SNIPPETS.md)，独立于 `.py` 源码计数。
- [原文件索引](/python-async-concurrency/FILES.md)与[静态校验结果](/python-async-concurrency/VALIDATION.json)。

清单和源码快照来自独立的 `python-async-concurrency/` 文件夹；分类页直接读取同一份清单，更新统计后无需维护第二套位置表。
