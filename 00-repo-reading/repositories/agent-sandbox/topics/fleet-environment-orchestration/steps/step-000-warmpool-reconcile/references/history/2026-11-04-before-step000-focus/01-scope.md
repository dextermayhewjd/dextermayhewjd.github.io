> 2026-11-04：Step 000 收窄为第一步整体骨架之前的快照；链接按实际保存位置调整。

# 01 · SWE-bench 探针示例：从任务数据到执行结果

[本步入口](README.md) · [项目当前接续](../../../../../../../README.md#current-reading) · [函数记录](02-short-term-memory/overview.md) · [本次过程](../../../04-flow.md)

## 1. 阅读目标

整体沿用已经确定的四项：**预热与环境供给、不同任务与环境的抽象、不同 Agent 的接入与隔离、大规模 rollout 的运行保障**。此前 12 组 examples 是这些目标的[材料索引](../../../../../../../references/rl-environments-and-jd.md#learning-scope)，按问题选用。

**Step 000 的实际问题：SWE-bench 探针示例中的任务数据，怎样进入环境准备、回调执行和结果返回这条基础调用链？** 最初从 run_naive 切入；随后按用户的问题回查对象初始化、任务来源、执行器、具体回调和命令通道。因此，本步骤已经覆盖多个函数，不能再用某一个调用位置代表整个 Step。

当前采用 strategy="naive"、epochs=1、recycle=False、keep_warm=False 的正常场景。下面归纳的是本步已经实际涉及的内容，不表示这些函数的全部细节都已掌握。

| 已涉及的关系 | 对应记录 |
| --- | --- |
| 管理对象与批次编排 | SandboxFleet 类卡、__init__、setup、run_naive |
| 单任务执行与结果交接 | process_parallel、_record.fn、swebench_probe、SandboxHandle.exec |
| 调用方与任务数据来源 | main、SweBenchSource.load |

共 9 个函数/方法记录和 1 张类卡，入口统一见[记录索引](02-short-term-memory/overview.md)。preflight、plan、acquire/release、teardown 等只按当前需要使用接口或局部源码；底层 WarmPool/Claim/Sandbox controller 与 Kubernetes 调度仍主要作为背景定位。

本步边界收拢在这条基础调用链的职责和数据交接。后续独立研究副本规划、Claim 协调或完整 Agent 运行等机制时，应另行确定阅读步骤，不因它们出现在图里就继续扩展本步。此前的[补池 scope](../2026-11-04-scope-before-confirmed-run-naive.md)保留为历史参考。

## 2. 找到指挥官函数

初始切入函数是 **run_naive**。它组织这一批任务的准备、执行与清理；外层 SandboxFleet.run 按策略名选择它。当前步骤已沿其输入、调用方和子调用建立更完整的基础链路，阅读范围以上面的记录为准。

| 定位 | 内容 |
| --- | --- |
| 本地仓库 | `/home/fredkeira/projects/agent-sandbox` |
| 固定版本 | `37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1`，2026-11-04 核对时工作区干净 |
| 源文件 | `examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py` |
| 初始切入点 | [run_naive，第 82 行](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py#L82)；[本步函数卡](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md) |
| 外层调用 | [SandboxFleet.run，第 2113 行](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L2113) |

进入前只需知道三个输入：

1. fleet 是 SandboxFleet 的 Python 管理对象，持有本批任务及运行配置；对象结构见 [SandboxFleet 类卡](../2026-11-04-SandboxFleet-before-reactivation.md)。
2. process_fn 是接入方提供的单任务处理函数。
3. concurrency 是交给执行器的任务并发度。

当前 executor 为默认的 process_parallel，teardown=True。执行器主干已有记录，整批清理内部仍只作接口定位。

## 3. 给出真正干活的核心骨架

### 3.1 放回强化学习的环境供给主线

图中 [1]–[5] 是程序工作阶段，分别对应下面的 3.1.1–3.1.5，不是五个学习 Step。**Step 000 是这条基础调用链的首轮阅读单元；current lookup 只标最近的源码回查位置。** 当前回查 [1] 的任务加载，不代表本步仅学习了这一段。

[1]–[4] 构成要串起的正常主线；其中底层资源协调仍按上面的深度边界保留。[5] 是在 [3] 领取时触发的补池背景，本步尚未深入其控制器实现。

这里固定为 SWE-bench 示例的 naive、非 recycle、PREPULL=False、keep_warm=False 路径。图中拆开显示 Source 和回调的构造，省略辅助检查与规划；多条任务可以并发，跨 Kubernetes 资源的关系由异步协调完成。这是流程示意，不是可执行代码。

```python
# Step 000: basic call flow [1]-[4]; see scope for reading depth
main()
  # [1] load tasks
  -> fleet = SandboxFleet(config)
  -> source = SweBenchSource(...)
  -> fleet.load_tasks(source)
       -> to_tasks(source) -> source.load() -> tasks: list[Task]  # current lookup
       -> fleet.tasks = tasks

  # [2] prepare environments
  -> process_fn = _record(swebench_probe)
  -> fleet.run(process_fn, ...)
       -> run_naive(...)
            -> fleet.setup()
                 -> SandboxTemplate + SandboxWarmPool
                 -> WarmPool controller -> Sandbox CR
                 -> core Sandbox controller -> Pod
                 -> scheduler -> kubelet / runtime -> Ready

            # [3] run each task
            -> process_parallel(fleet, fleet.tasks, ...)
                 -> _one(task)
                      -> handle = fleet.acquire(task)
                           -> claim adoption --async--> [5]
                      -> process_fn(task, handle) -> result
                      -> fleet.release(handle)

            # [4] collect, clean up, return
            <- results from process_parallel
            -> fleet.teardown()
            -> return results
       -> return results
  -> print(json.dumps(...))

# [5] background: replenish after adoption; overlaps [3]
claim adoption
  -> Sandbox leaves warm pool
  -> WarmPool controller observes a deficit
  -> Sandbox CR -> core Sandbox controller -> Pod
```

fleet.run 跨越 [2]–[4]；它并非在环境准备完成后就返回。[3] 中每个 _one 处理一条已有 Task；它不会创建 Task 数据。当前回调执行的是固定探针，随后返回记录字典。

#### 3.1.1 [1] 加载任务：先有 Task 数据

1. main 创建 SandboxFleet，最初 fleet.tasks 为空。
2. main 创建 SweBenchSource，保存数据集、split、读取数量等条件。
3. fleet.load_tasks 通过 to_tasks 调用 source.load()，读取数据并生成 Task 列表。
4. fleet.load_tasks 将列表保存到 fleet.tasks。此时还未调用 fleet.run，也未进入 run_naive 的 setup。

本段的结果是任务数据，交给 [2] 规划环境，也交给 [3] 逐项执行。

#### 3.1.2 [2] 准备环境：使用已加载的 Task

1. main 调用 _record(swebench_probe)，取得稍后执行任务的回调。
2. main 将回调交给 fleet.run，后者通过 naive 策略进入 run_naive。
3. run_naive 调用 fleet.setup，根据已有 fleet.tasks 组织检查、规划和环境准备。
4. 准备 SandboxTemplate，描述环境配置。
5. 创建或更新 SandboxWarmPool，表达备用数量目标。
6. WarmPool controller 按目标创建所需 Sandbox CR。
7. 核心 Sandbox controller 协调 Pod 等子资源。
8. Kubernetes 调度器为 Pod 选择节点。
9. kubelet 和容器运行时启动容器。
10. setup 等待当前场景要求的就绪条件，正常返回后才进入 [3]。

本段的结果是可供领取的环境。具体副本数由规划决定，不能直接把 Task 数量当作 Pod 数量。

#### 3.1.3 [3] 执行任务：领取、使用、释放

1. process_parallel 接到 fleet.tasks，为已有 Task 安排 _one(task)。
2. _one 调用 fleet.acquire(task)，通过 Claim 领取环境并取得 handle。
3. 领取成功时，Sandbox 离开备用池，触发图中的 [5] 支路。
4. _one 调用 process_fn(task, handle)。
5. 当前回调执行 swebench_probe，通过 handle 向容器发送固定命令。
6. 回调取得文本，包装任务与环境标识，返回结果字典。
7. _one 在 finally 中调用 fleet.release(handle)，随后完成这条任务。

多条任务可以并发进行。[5] 与这里的后续执行可以重叠，不需要等待整批任务结束。

#### 3.1.4 [4] 整批收束：结果返回与资源清理

1. process_parallel 将各任务结果放回原输入位置，完成整批收集后返回列表。
2. run_naive 进入 finally。当前 keep_warm=False 对应 teardown=True，因此执行 fleet.teardown。
3. 清理正常结束后，run_naive 将结果交回 fleet.run。
4. fleet.run 将整批结果返回 main。
5. main 打印 JSON 结果。未配置 REPORT_DIR 的默认路径到此结束。

单任务 release 属于 [3]，整批 teardown 属于 [4]，两者的管理范围不同。

#### 3.1.5 [5] 并行补池：由领取触发的支路

1. [3] 中成功领取的 Sandbox 转归 Claim 管理，不再计作池内备用成员。
2. WarmPool controller 在后续协调中观察当前备用数量与目标的差额。
3. 满足创建条件时，控制器补充 Sandbox CR。
4. 新增 Sandbox 再通过核心控制器及 Kubernetes 形成备用环境。

本支路接回 [2] 中的环境供给机制，并可与 [3] 的任务执行重叠；它不是必须等 [4] 完成后再执行的第五个顺序阶段。备用目标只约束池内备用数量，已领取、正在使用的环境另计。

### 3.2 naive 策略的核心骨架

<a id="task-loading-before-setup"></a>

#### 3.2.1 调用方先加载任务

下面按 main:84–93 的真实顺序等价拆写，source 是为展示中间对象而命名的局部变量；原代码在 load_tasks 的参数位置直接构造它。当前 PREPULL=False，省略其可选分支。

```python
fleet = SandboxFleet(config)                         # [A1]
source = SweBenchSource(...)                         # [A2]
fleet.load_tasks(source)                             # [A3]
results = fleet.run(_record(swebench_probe),          # [A4]
                   strategy=strategy, concurrency=max_concurrent)
```

1. **[A1] 创建管理对象**：初始 tasks 为空。
2. **[A2] 创建数据来源对象**：保存从哪里读取、读取多少等条件。
3. **[A3] 加载任务**：load_tasks 调用 to_tasks；后者调用 source.load()，取得 Task 列表；load_tasks 将其保存到 self.tasks。
4. **[A4] 开始整批运行**：此时 fleet.tasks 已存在，随后才进入下面的 run_naive。

#### 3.2.2 进入 run_naive 后准备和使用环境

下面是 run_naive 的教学裁剪，保留当前问题需要的 fleet.tasks 实参，以及实际的返回、finally 和清理开关。默认 executor 是 process_parallel。

```python
try:
    fleet.setup()          # [1] prepare the image pools
    return executor(fleet, fleet.tasks, process_fn, concurrency)  # [2]
finally:
    if teardown:
        fleet.teardown()   # [3] clean up this run
```

1. 先调用 fleet.setup，依据已加载的 fleet.tasks 准备本批各镜像的预热池；它不负责创建 Source 或加载数据集。
2. 再调用 executor，执行本批任务并取得结果。naive 不表示任务必须串行。
3. 最后根据 teardown 决定是否清理。当前场景为 True；正常返回结果前会先经过 finally。

### 3.3 与 Kubernetes 及其他策略的关系

1. run_naive 决定这批工作何时准备、何时执行、何时清理。
2. Fleet 和执行器通过资源接口、SDK 发起环境管理与任务操作。
3. Kubernetes 及 Agent Sandbox controllers 在下游协调 Sandbox、Pod 等资源。

naive 可以作为理解这些关系的朴素基线。其他策略由同一个 STRATEGIES 表并列选择；不是都调用或继承 run_naive。策略比较见[本步函数卡](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md#strategy-position)，本轮只确认职责，不展开其他策略实现。

<a id="reading-navigation"></a>

### 3.4 一次打开一个函数

最近的源码回查点是 [SweBenchSource.load](../../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/adapters/swebench.py/SweBenchSource.load.md)。下表保留本步各处导航；“当前”只表示此刻的位置，其他行继续保存来路与返回关系。

现有材料怎样重新回读、如何按问题拆步，见[回读顺序与拟拆步方案](../../../../../../../references/reading-order-proposal.md)。该建议不改变下列原始阅读记录的来源。

| 编号与源码入口 | 本次要看清什么 | 看完回到哪里 |
| --- | --- | --- |
| 当前数据回查：[SweBenchSource.load](../../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/adapters/swebench.py/SweBenchSource.load.md) | 读取数据集，逐行转换为 Task | fleet.load_tasks 保存结果，再返回 main |
| 调用方：[main](02-short-term-memory/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md) | 配置、加载任务、构造回调、调用 Fleet、打印结果 | main:92，回调作为 process_fn 传入 |
| 前置回查：[SandboxFleet.__init__](../2026-11-04-before-init-method-separation/SandboxFleet.__init__.md) | 当前对象怎样初始化；本轮已明确进入 | 对象构造处，随后登记任务并接回主线 |
| [1] [SandboxFleet.setup](../../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md) | 本批任务的环境准备入口；本轮已明确进入 | run_naive:94，调用执行器 |
| [2] [process_parallel](../../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/process_parallel.md) | 默认执行器，负责单任务领取、处理与释放，汇集结果 | run_naive:95，进入 finally |
| [2.2] 回调：[_record.fn](../../reserve/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/_record.fn.md) | 被传入的 process_fn；取得探针输出并包装字典 | process_parallel 的 _one，随后释放环境 |
| [2.2.1] [swebench_probe](../../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/adapters/swebench.py/swebench_probe.md) | 回调内部使用的具体探针 | 返回文本给 _record.fn |
| 命令入口：[SandboxHandle.exec](../../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/handles.py/SandboxHandle.exec.md) | 用 handle 定位 Pod/容器，经 exec API 执行命令 | 回到 swebench_probe 的 strip，再返回 fn |
| [3] [SandboxFleet.teardown:1835](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1835) | 本次运行的整体资源清理入口 | 返回 SandboxFleet.run:2113 的调用处 |

当前已展开的记录与来源统一见[记录索引](02-short-term-memory/overview.md)；`03` 暂无前序继承。

**本步停止位置**：能连贯说明 Source 如何产生 Task、Fleet 如何组织环境准备、执行器如何调用具体回调，以及结果如何返回调用方。相关底层机制保留为明确未知；图和卡片已经存在不等于全部读完或掌握，也不据此将本步标记为完成。
