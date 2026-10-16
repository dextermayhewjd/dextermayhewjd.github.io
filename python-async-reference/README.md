# Asyncio 与并发处理：官方文档与三仓库用法统计

这里只统计 Asyncio 与直接相关的并发处理：协程、任务、事件循环、线程/进程、执行器、同步、队列、并发 I/O 和异步协议辅助。普通文件操作、通用反射、数值运算及其他无关标准库 API 不纳入。
官方文档目录与本地 Slime、AReaL、verl 的实际源码位置放在一起，用于确定需要学习哪些机制。

已保存 **46 个官方页面**，目录共记录 **47 页**；抓取失败或不存在 **1 页**。
本次文档范围内保留 **922 个规范化 API/协议条目**，包含使用次数为零的条目。

## 1. 从这里进入

1. [完整课程设置](curriculum.md)：8 模块、41 个编号单元（复杂单元分成独立子课），安排全部 97 项 API；[学习范围与顺序](learning-plan.md)保存选题依据，[当前 API 表](current-api-plan.md)保存官网入口和覆盖统计。
   [01–41 课全部 API 与语法出现次数](lesson-api-frequency.md)按首次引入的课号列出完整规划中的 97 项接口及配套语法，展示四库核心包的统计并标注待编写课程；最右侧“本课占比”将同课各项的四库使用次数相加，以四库全部已识别调用、引用与七类语法的统计总量为分母，包含尚未选入课程的接口。每课合并显示一次，单项占比不变，复习旧 API 不重复计数。用 `python3 python-async-reference/tools/build_lesson_api_frequency.py` 重新生成，加 `--check` 可核对。
2. [官方网址与本地副本](OFFICIAL-DOCS.md)：含用户指定的 12 页和补充理由；[纯网址清单](official/urls.txt)。
3. [按官方页面统计](TOPIC-USAGE.md)：先决定哪些主题值得学习，再进入逐页明细。
4. [核心包 API 矩阵](CORE-API-USAGE.md) / [含测试与示例的完整矩阵](API-USAGE.md) / [TSV](api-usage.tsv)。
5. [语言语法统计](SYNTAX-USAGE.md)：async def、await、async with、async for 等。
6. [待核实的方法](UNRESOLVED.md) / [未匹配到本次文档条目的 API](UNMAPPED.md)。
7. [统计与匹配规则](METHOD.md) / [机器可读汇总](report.json) / [验证记录](VALIDATION.md)。
8. [关联地图资料目录](relationship-map/README.md)：单独保存概念之间的关系，供后续绘制思维导图使用。

### Miles 补充对照

本地 Miles 使用 `/home/hongshi/projects/miles`，本次固定为 `cf91d625b3074f480b31ddcfd6604298407899f3`。核心包为 `miles/`；完整扫描保留入口脚本、插件、测试和示例的独立范围。原三库快照与固定覆盖基线继续保留。

- [Miles 扫描清单](repositories/miles/inventory.json)与[API 计数](repositories/miles/api-counts.json)，来源行和相应文件快照保存在同一目录。
- 当前范围由原 82 项扩充为 97 项；[四库加权核算](current-api-plan.md)保留扩充前后对比，[原 82 项](api-plan-82.json)保留作历史基线。
- [四库课程对照表](lesson-api-frequency.md)已增加 Miles 列；[源码用法说明](../content/projects/python-async-concurrency/miles-async-usage/index.md)连接任务创建、结果收集、缓冲与清理。
- 更新命令：

```bash
python3 python-async-reference/tools/scan_repositories.py --repo miles=/home/hongshi/projects/miles
python3 python-async-reference/tools/build_repository_api_counts.py --repo miles
python3 python-async-reference/tools/build_lesson_api_frequency.py
```

以上命令加 `--check` 可核对快照、计数和表格；它们不运行 Miles 的训练或服务。

## 2. 固定源码版本

| 仓库 | HEAD | 已跟踪 Python 文件 | 解析错误 | 逐条位置 |
| --- | --- | ---: | ---: | --- |
| slime | `22a89f96835969a47055a659c588f46151f8b07a` | 388 | 0 | [清单](repositories/slime/occurrences.tsv) · [JSON](repositories/slime/inventory.json) |
| areal | `298412a40f5b84ae6b2042987e81777e6dd0f284` | 1051 | 0 | [清单](repositories/areal/occurrences.tsv) · [JSON](repositories/areal/inventory.json) |
| verl | `1d367a4f459a43768f76312c0d3430a99ec46b8c` | 675 | 0 | [清单](repositories/verl/occurrences.tsv) · [JSON](repositories/verl/inventory.json) |

这里的“次数”始终是静态源码位置，不是运行频率，也不是学习优先级。核心包与测试/示例分开保留；带接收者线索的方法不并入直接调用。

文档固定为抓取时的 Python 3.16 开发版，具体版本与时间记录在目录中；本地源码并不因此被认为运行于 Python 3.16。零次只表示这次范围内未命中，不能推断接口无用。

## 3. 重新收集与核对

从项目根目录执行，源码仓库只读：

```bash
python3 python-async-reference/tools/collect_docs.py
python3 python-async-reference/tools/scan_repositories.py \
  --repo slime=/home/fredkeira/projects/slime \
  --repo areal=/home/fredkeira/projects/AReaL \
  --repo verl=/home/fredkeira/projects/verl
python3 python-async-reference/tools/build_reports.py
python3 -m unittest discover -s python-async-reference/tests -p "test_*.py"
```

已有快照离线检查：

```bash
python3 python-async-reference/tools/collect_docs.py --check
python3 python-async-reference/tools/scan_repositories.py \
  --repo slime=/home/fredkeira/projects/slime \
  --repo areal=/home/fredkeira/projects/AReaL \
  --repo verl=/home/fredkeira/projects/verl \
  --check
python3 python-async-reference/tools/build_reports.py --check
```

完整的 asyncio 文档目录与明确列出的相关页面构成本次边界；没有无限递归整个 Python 官网，也不声称覆盖所有第三方异步库。

HTML 保存原始页面作为来源证据，没有额外打包官网的全部样式资源；离线阅读可直接打开正文 TXT。较大参考页的原始副本不等于其中所有 API 都进入统计。
