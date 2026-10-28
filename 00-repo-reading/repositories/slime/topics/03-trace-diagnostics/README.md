# 03 · Trace 与运行诊断

[Slime 项目入口](../../README.md) · [当前进度](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续) · [前一主题](../02-rollout-reward/README.md)

> **Trace 暂缓研究。** 2026-10-28 用户明确暂停本主题当前的 Step 014，已有内容保留，未记为完成。下文供恢复时回查；实时状态见[唯一路线](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)。

## 核心问题

任务执行过程怎样留下可关联的记录，怎样据此理解耗时与排查问题？本主题从一个实际阶段的 Trace 入手，不以遍历所有埋点或追踪工具为起点。

主题 02 关注生成、评分和结果交付；本主题关注这些业务过程怎样被观察。相同源码可在不同主题按不同问题复用。

<a id="trace-utils-purpose"></a>

## 先看 trace_utils.py 到底做什么

**它是一组给业务执行过程做结构化记录的工具，方便事后查看某个样本经过哪些阶段、各阶段何时发生、持续多久、带着什么结果。**

可以先把它理解成能关联样本和阶段的执行日志。业务计算仍由生成、工具调用和评分代码完成；trace_utils 在这些过程周围留下记录。

仓库已有专门的[中文文档《Trace 可视化》](/home/hongshi/projects/slime/docs/zh/developer_guide/trace.md)，其中的[示例图](/home/hongshi/projects/slime/docs/_static/image/trace.png)给出了这些记录的最终用途：每行是一条 sample，条形块是阶段，长度体现时间范围，详情显示属性。图里是官方示例的数据，不是本次 agent_run 的实际运行结果。

```text
业务执行： 生成 / Agent / 工具调用 / 评分
                │ 在需要观察的位置使用 Trace 工具
                ▼
trace_utils.py：给目标记录阶段开始、结束、瞬时事件和属性
                │ 当前 Sample 路径写入 sample.trace
                ▼
rollout 保存逻辑：将样本及 trace 放入 debug dump（.pt）
                ▼
trace_timeline_viewer.py：把保存的记录呈现为时间线
```

保存文件与画时间线属于后续组件，不是 trace_utils.py 独自完成整条链。

### 从使用者角度，只先认识四个入口

| 要做的事 | 使用的入口 | 留下或准备什么 |
| --- | --- | --- |
| 观察一段代码从开始到结束 | trace_span | 同一个阶段的开始与结束记录 |
| 记录某个瞬间发生的事 | trace_event | 一条带时间的事件 |
| 观察整个函数调用 | trace_function | 在同步或异步函数外层使用 trace_span |
| 给样本准备记录位置 | bind_trace | 关联 sample.trace，得到对应的 TraceHandle |

这些是使用方式，不是需要从上到下依次调用的四个步骤。暂缓前的主例是 agent_run 的 trace_span。

需要完整清单时，先看 [scope 的工具分类与导航](steps/step-014-agent-run-trace/01-scope.md#tool-catalog)，再进入[短期记录里的具体用法](steps/step-014-agent-run-trace/02-short-term-memory/overview.md)。内存记录到 .pt / JSONL 的路径保存在辅助参考 [Trace 的保存与查看](steps/step-014-agent-run-trace/references/trace-output-and-viewing.md)，需要导出或查看时再读。上表只保留最常见的四个入口，不代表模块只提供四个函数。

### 当前代码到底用它做了什么

真实调用节选；仅省略 harness.run 的实参：

```python
with trace_span(base_sample, "agent_run", record_error=False) as span:
    agent_exit_code = await harness.run(...)
    span.set("exit_code", agent_exit_code)
```

这段代码在运行 Agent 的同时，给 base_sample 留下“agent_run 从何时开始、何时结束、退出码是多少”的记录。后续才能在时间线上找到这个阶段，并观察它的耗时与结果。

TraceHandle 是找到记录位置的对象，TraceSpanContext 是本次阶段的临时操作对象；_coerce_handles、_append_event 等是完成这些记录的内部步骤。先明确模块用途，再按当前问题回查它们，不把每个内部符号都变成理解模块之前必须读完的前置。

<a id="trace-design-responsibilities"></a>

### 从设计问题对应到已有实现

先限定目标：给一段业务记录开始、结束和附加结果。以下是理解当前版本的设计拆解，不是源码的历史演化，也不要求重新实现一套工具。

| 设计时必须回答的问题 | 当前实现放在哪里 | 先理解到什么程度 |
| --- | --- | --- |
| 记录最终保存在哪里？ | 当前 Sample 路径中的 sample.trace["events"] | 一份事件列表可以保存多个阶段，阶段靠编号区分 |
| 记录工具如何找到对应目标？ | TraceHandle | 统一携带身份与 carrier 引用；不复制一份 Trace |
| 当前这一段执行要暂存什么？ | TraceSpanContext | 关联本次阶段与待写属性；不是另开一条 Trace |
| 谁决定什么时候写开始、结束？ | trace_span | 进入时写开始，yield 交给业务，退出后写结束并恢复上下文 |

从最小需求看，核心是“存放记录的位置”和“包住执行区间的控制逻辑”。当前版本另外用句柄统一不同目标，用阶段对象承接本次状态，方便多阶段复用和业务补充属性。不是每经过一个对象就再运行一层业务。

阅读时先把 trace_span 看成一个完整接口：输入目标与阶段名，业务执行后留下可配对的事件。只在不明白某一步如何兑现这个行为时，再进入相应对象或辅助函数。既有类卡、函数卡继续作回查，不变成强制阅读顺序。

暂缓前保留的阅读顺序是：**本节的模块职责 → [scope 的分类、骨架与阅读导航](steps/step-014-agent-run-trace/01-scope.md#reading-order) → [函数卡的具体用法](steps/step-014-agent-run-trace/02-short-term-memory/overview.md) → [examples 的前后数据](steps/step-014-agent-run-trace/02-short-term-memory/examples/README.md)。** 函数内部机制按需回查。

<details>
<summary>固定版本与后续工具入口</summary>

- 固定版本 18868a79：[Trace 文档](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/docs/zh/developer_guide/trace.md)、[trace_utils.py](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/observability/trace_utils.py)。
- 官方文档用 --save-debug-rollout-data 保存包含 Trace 的 rollout dump，再用 tools/trace_timeline_viewer.py 打开。本轮只定位用途，没有启动保存、查看器或训练任务。
- export_trace / import_trace 是传播追踪身份与父阶段上下文的接口；export_trace 并不导出完整的 events，也不是上图中的文件保存步骤。跨进程场景暂留回查。

</details>

## 主入口与当前边界

- 首个场景：examples/coding_agent_rl/generate.py 中的 agent_run 包装，286–295 行。
- 核心函数：slime/observability/trace_utils.py::trace_span。
- 本轮先看一个阶段的正常进入、业务执行与属性记录、正常退出；其他埋点、传播与取消对照按后续问题展开。

## 步骤索引

| 步骤 | 本步问题 | 入口 |
| --- | --- | --- |
| Step 014 | 一个 agent_run 阶段怎样留下 Trace | [范围与记录](steps/step-014-agent-run-trace/README.md) |

步骤继续全局编号，跨主题仍按上一实际步骤的 03 + 02 继承。当前进度仅由唯一路线维护，创建材料不代表已经掌握。
