> 2026-11-04：显式补入 Source 与 Task 加载时间线前的 scope；相对链接已调整。

# 01 · run_naive：一批任务的准备、执行与清理

[本步入口](../../README.md) · [项目当前接续](../../../../../../README.md#current-reading) · [函数记录](../../02-short-term-memory/overview.md) · [本次过程](../../04-flow.md)

## 1. 阅读目标

整体沿用已经确定的四项：**预热与环境供给、不同任务与环境的抽象、不同 Agent 的接入与隔离、大规模 rollout 的运行保障**。此前 12 组 examples 是这些目标的[材料索引](../../../../../../references/rl-environments-and-jd.md#learning-scope)，按问题选用。

**Step 000 从 run_naive 开始：一批已经给定的任务，怎样先准备环境，再执行任务，最后交回结果并清理？** 用户已于 2026-11-04 确认从这里开始。本轮先区分训练侧的策略编排与 Kubernetes 的资源管理，再认识它作为学习基线的意义。

本轮采用已配置 Fleet、已登记任务的正常场景：strategy="naive"、epochs=1、recycle=False、keep_warm=False。从 run_naive 的三个调用建立主线后，已回查 SandboxFleet.__init__ 与 setup；用户概括了 setup 的主要职责，现明确要求返回 executor，进入 process_parallel。此前的[补池 scope](2026-11-04-scope-before-confirmed-run-naive.md)保留为历史参考。

## 2. 找到指挥官函数

首读 **run_naive**。它组织这一批任务的准备、执行与清理，适合先看完整批次怎样流转。外层 SandboxFleet.run 按策略名选择它；Kubernetes 侧的具体资源创建位于下游。

| 定位 | 内容 |
| --- | --- |
| 本地仓库 | `/home/fredkeira/projects/agent-sandbox` |
| 固定版本 | `37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1`，2026-11-04 核对时工作区干净 |
| 源文件 | `examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py` |
| 首读入口 | [run_naive，第 82 行](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py#L82)；[本步函数卡](../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md) |
| 外层调用 | [SandboxFleet.run，第 2113 行](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L2113) |

进入前只需知道三个输入：

1. fleet 是 SandboxFleet 的 Python 管理对象，持有本批任务及运行配置；当前按用户要求单独查看 [SandboxFleet 类卡](2026-11-04-SandboxFleet-before-reactivation.md)。
2. process_fn 是接入方提供的单任务处理函数。
3. concurrency 是交给执行器的任务并发度。

当前 executor 为默认的 process_parallel，teardown=True。它们的详细实现先保留为后续问题。

## 3. 给出真正干活的核心骨架

### 3.1 放回强化学习的环境供给主线

下图是职责与资源交接总图，`# Step 000` 标出本步位置。当前具体路径选择 SandboxFleet 的 naive 策略；LookaheadWarmer 是外部训练循环可用的预热入口，本步不经过它。跨控制器的箭头由 Kubernetes 资源变化连接，不表示一串同步函数调用，也不是可执行代码。

```python
RL batch demand
  -> SandboxFleet / LookaheadWarmer  # Step 000: SandboxFleet -> run_naive
  -> SandboxTemplate + SandboxWarmPool
  -> WarmPool controller
  -> Sandbox CR -> core Sandbox controller -> Pod

rollout -> SandboxClaim -> available Sandbox -> task / tool calls -> result -> release
              |
              +-> claimed Sandbox leaves pool -> WarmPool reconciles again
```

这条主线跟随一批训练任务所需环境的供给与使用过程。上半段准备环境，下半段使用这些环境；领取后的补池流程单独列出。

#### 3.1.1 上半段负责准备环境

1. 提出环境需求。训练侧确定需要哪类环境、备用多少。
2. 准备环境模板。编排层通过 SandboxTemplate 描述所需环境；图中的 SandboxFleet / LookaheadWarmer 承接训练侧需求。
3. 设置备用目标。编排层在 SandboxWarmPool 中指定备用数量，并关联对应模板。
4. 补充 Sandbox 对象。WarmPool controller 根据目标与现有数量，在允许创建时补充缺少的 Sandbox CR。
5. 协调 Pod。核心 Sandbox controller 为 Sandbox 管理对应的 Pod 等子资源。
6. 调度 Pod。Kubernetes 调度器为 Pod 选择运行节点。
7. 启动环境。节点上的 kubelet 和容器运行时负责启动容器。

#### 3.1.2 下半段使用上半段准备的环境

1. 领取环境。rollout 通过 SandboxClaim 取得一个准备好的 Sandbox。
2. 完成题目初始化。任务执行逻辑把本题需要的数据、文件或初始状态准备到领取的环境中。
3. 进行工具交互。Agent 在任务过程中使用环境提供的命令、文件等接口。
4. 取回所需结果。任务执行逻辑收集后续评分或处理需要的输出、文件等产物。
5. 释放环境。使用结束后，调用方释放本次申请的环境资源。

#### 3.1.3 领取后的补池流程

这条分支从 3.1.2 的第 1 步接出，可以与第 2–5 步并行推进。

1. 移出备用池。成功领取的 Sandbox 转归 Claim 管理，不再作为池内备用成员。
2. 观察备用缺口。WarmPool controller 在后续协调中比较当前成员数量与备用目标。
3. 补充备用环境。满足创建条件时，WarmPool controller 按缺口发起补充。

因此，备用目标 3 个指向池内尚未领取的环境数量；已领取、正在执行任务的环境另计。补池无需等到这些任务完成并释放资源后才开始。

#### 3.1.4 Step 000 当前位于哪里

本步位于图中的 SandboxFleet 编排层，由 run_naive 连接环境准备与整批执行。它不是 Kubernetes 自身的调度策略。

1. 看清准备。fleet.setup 怎样作为“先准备本批所需预热池”的交接点。
2. 看清执行。executor 怎样接到任务、处理函数和并发度。
3. 看清清理。teardown 参数怎样决定是否做整批清理。
4. 看清策略位置。naive 怎样作为学习基线，与其他并列策略区分。

本步先沿三个调用建立关系。预热池补充、Pod 管理、单任务执行器等内部实现继续按问题下钻。

### 3.2 naive 策略的核心骨架

下面是 run_naive 的教学裁剪，调用参数用 `...` 省略，保留实际的返回、finally 和清理开关。默认 executor 是 process_parallel。

```python
try:
    fleet.setup()          # [1] prepare the image pools
    return executor(...)   # [2] run the task batch
finally:
    if teardown:
        fleet.teardown()   # [3] clean up this run
```

1. 先调用 fleet.setup，准备本批各镜像的预热池；数量由 Fleet 规划决定。
2. 再调用 executor，执行本批任务并取得结果。naive 不表示任务必须串行。
3. 最后根据 teardown 决定是否清理。当前场景为 True；正常返回结果前会先经过 finally。

### 3.3 与 Kubernetes 及其他策略的关系

1. run_naive 决定这批工作何时准备、何时执行、何时清理。
2. Fleet 和执行器通过资源接口、SDK 发起环境管理与任务操作。
3. Kubernetes 及 Agent Sandbox controllers 在下游协调 Sandbox、Pod 等资源。

naive 可以作为理解这些关系的朴素基线。其他策略由同一个 STRATEGIES 表并列选择；不是都调用或继承 run_naive。策略比较见[本步函数卡](../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md#strategy-position)，本轮只确认职责，不展开其他策略实现。

<a id="reading-navigation"></a>

### 3.4 一次打开一个函数

从 run_naive:94 进入 process_parallel 后，用户选择 SWE-bench 作为具体回调例子。已沿 _record.fn、swebench_probe 和 SandboxHandle.exec 定位固定命令执行；当前按用户问题回查 [SweBenchSource.load](../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/adapters/swebench.py/SweBenchSource.load.md)，看执行前的任务数据怎样进入 Fleet。下表保留此前来路与返回位置。

| 编号与源码入口 | 本次要看清什么 | 看完回到哪里 |
| --- | --- | --- |
| 当前数据回查：[SweBenchSource.load](../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/adapters/swebench.py/SweBenchSource.load.md) | 读取数据集，逐行转换为 Task | fleet.load_tasks 保存结果，再返回 main |
| **当前调用方：[main](../../02-short-term-memory/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md)** | 配置、加载任务、构造回调、调用 Fleet、打印结果 | main:92，回调作为 process_fn 传入 |
| 前置回查：[SandboxFleet.__init__](2026-11-04-before-init-method-separation/SandboxFleet.__init__.md) | 当前对象怎样初始化；本轮已明确进入 | 对象构造处，随后登记任务并接回主线 |
| [1] [SandboxFleet.setup](../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md) | 本批任务的环境准备入口；本轮已明确进入 | run_naive:94，调用执行器 |
| [2] [process_parallel](../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/process_parallel.md) | 默认执行器，负责单任务领取、处理与释放，汇集结果 | run_naive:95，进入 finally |
| [2.2] **当前回调：[_record.fn](../reserve/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/_record.fn.md)** | 被传入的 process_fn；取得探针输出并包装字典 | process_parallel 的 _one，随后释放环境 |
| [2.2.1] [swebench_probe](../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/adapters/swebench.py/swebench_probe.md) | 回调内部使用的具体探针 | 返回文本给 _record.fn |
| 当前命令入口：[SandboxHandle.exec](../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/handles.py/SandboxHandle.exec.md) | 用 handle 定位 Pod/容器，经 exec API 执行命令 | 回到 swebench_probe 的 strip，再返回 fn |
| [3] [SandboxFleet.teardown:1835](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1835) | 本次运行的整体资源清理入口 | 返回 SandboxFleet.run:2113 的调用处 |

当前已展开的记录与来源统一见[记录索引](../../02-short-term-memory/overview.md)；`03` 暂无前序继承。

**本步停止位置**：能说明 run_naive 的三个交接点，并区分批次策略与下层资源机制。下一处函数根据实际卡点选择；函数内容已写好或出现在图中，不等于已读或已掌握。
