# Step 000 · 已采用的 scope 参考稿

[对照正式 scope](../01-scope.md) · [看完整主线](#whole-flow) · [直接看本轮代码](#current-excerpt)

> 2026-11-04 已按用户要求采用到 [正式 scope](../01-scope.md)。本文件保留采用时的参考稿，后续阅读与更新以正式 scope 为准。

## 1. 本步解决什么问题

看清 SWE-bench 示例怎样提供任务和处理函数，再由运行层完成准备、执行、清理，最后交回结果。Step 000 只展开两个编排函数：

1. **main：本轮主攻。** 看 [1] 的任务加载、进入 [2] 前的回调交接，以及如何接住 [4] 返回的结果。
2. **run_naive：本步稍后阅读。** 看它怎样依次组织 [2] 的 setup、[3] 的 executor 和 [4] 的 teardown；关注调用次序、数据交接与返回时机。

## 2. 这一轮先看哪里

当前先停在 main:84 的 fleet = SandboxFleet(config)，看清构造后得到什么管理对象；已有构造函数记录仅用于回查这一行的结果，尚不展开 setup。

1. **主攻函数与代码位置**：[main 函数卡](../02-short-term-memory/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md)，对应 examples/agent-sandbox-rl/examples/run_swebench_fleet.py 第 84–93 行，只读这段的调用与交接。
2. **当前问题**：调用 fleet.run 时，任务在哪里已经加载，具体处理函数由谁提供？
3. **本轮深度**：能指出任务来源、回调来源和结果接收位置即可。看到 SandboxFleet、SweBenchSource、load_tasks、_record 和 fleet.run 时，先理解调用的作用与输入输出，不继续展开它们的内部实现。

## 3. 整体位置与本轮片段

<a id="whole-flow"></a>

### 3.1 完整主线：用来定位当前步骤

这张图保留任务加载、环境准备、逐任务执行、结果返回及并行补池。图中 [1]–[5] 对应下面的 3.1.1–3.1.5，是程序阶段，不是本步要逐个读透的函数清单。

**图中 NOW 标出本轮主攻的 main 及其调用位置；LATER 标出本步稍后要读的 run_naive。** 其他节点作为上下文保留，显示被调用部分位于哪里，不要求本轮逐个进入。NOW 所在行与 3.2 的局部代码对应。

当前仍选择 SWE-bench 示例的 naive、非 recycle、PREPULL=False、keep_warm=False 路径。这里的箭头混合展示调用与资源交接，跨 Kubernetes 组件的部分由异步协调完成；[5] 从领取处触发，可与任务执行重叠。

```python
main()  # Step 000 | NOW: main L84-L93, call sites only
  # [1] load tasks
  -> fleet = SandboxFleet(config)  # NOW: create manager
  -> fleet.load_tasks(SweBenchSource(...))  # NOW: create source, then load tasks
       # source is a parameter of load_tasks, not a local variable in main
       -> to_tasks(source) -> source.load() -> tasks: list[Task]
       -> fleet.tasks = tasks

  # [2] prepare environments
  -> results = fleet.run(_record(swebench_probe), ...)  # NOW: provide callback; receive results after [4]
       -> run_naive(...)  # Step 000 | LATER: setup, executor, teardown
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

下面五项按需展开；每项标题保留阶段作用，展开后查看原有细分步骤。[5] 是与执行重叠的支路。

<details>
<summary>3.1.1 [1] 加载任务：数据来源 → fleet.tasks（展开细节）</summary>

1. main 创建 SandboxFleet，最初 fleet.tasks 为空。
2. main 创建 SweBenchSource，保存数据集、split、读取数量等条件。
3. fleet.load_tasks 通过 to_tasks 调用 source.load()，读取数据并生成 Task 列表。
4. fleet.load_tasks 将列表保存到 fleet.tasks。此时还未调用 fleet.run，也未进入 run_naive 的 setup。

本段的结果是任务数据，交给 [2] 规划环境，也交给 [3] 逐项执行。

</details>

<details>
<summary>3.1.2 [2] 准备环境：任务需求 → 可领取的环境（展开细节）</summary>

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

</details>

<details>
<summary>3.1.3 [3] 执行任务：Task + 环境 → 单任务结果（展开细节）</summary>

1. process_parallel 接到 fleet.tasks，为已有 Task 安排 _one(task)。
2. _one 调用 fleet.acquire(task)，通过 Claim 领取环境并取得 handle。
3. 领取成功时，Sandbox 离开备用池，触发图中的 [5] 支路。
4. _one 调用 process_fn(task, handle)。
5. 当前回调执行 swebench_probe，通过 handle 向容器发送固定命令。
6. 回调取得文本，包装任务与环境标识，返回结果字典。
7. _one 在 finally 中调用 fleet.release(handle)，随后完成这条任务。

多条任务可以并发进行。[5] 与这里的后续执行可以重叠，不需要等待整批任务结束。

</details>

<details>
<summary>3.1.4 [4] 整批收束：收集结果、清理资源、返回 main（展开细节）</summary>

1. process_parallel 将各任务结果放回原输入位置，完成整批收集后返回列表。
2. run_naive 进入 finally。当前 keep_warm=False 对应 teardown=True，因此执行 fleet.teardown。
3. 清理正常结束后，run_naive 将结果交回 fleet.run。
4. fleet.run 将整批结果返回 main。
5. main 打印 JSON 结果。未配置 REPORT_DIR 的默认路径到此结束。

单任务 release 属于 [3]，整批 teardown 属于 [4]，两者的管理范围不同。

</details>

<details>
<summary>3.1.5 [5] 并行补池：领取后出现差额 → 补充备用环境（展开细节）</summary>

1. [3] 中成功领取的 Sandbox 转归 Claim 管理，不再计作池内备用成员。
2. WarmPool controller 在后续协调中观察当前备用数量与目标的差额。
3. 满足创建条件时，控制器补充 Sandbox CR。
4. 新增 Sandbox 再通过核心控制器及 Kubernetes 形成备用环境。

本支路接回 [2] 中的环境供给机制，并可与 [3] 的任务执行重叠；它不是必须等 [4] 完成后再执行的第五个顺序阶段。备用目标只约束池内备用数量，已领取、正在使用的环境另计。

</details>

<a id="current-excerpt"></a>

### 3.2 本轮主攻 main:84–93：任务、回调与运行结果的交接

**本步 Step 000 在大图中的范围**：通过 main 与 run_naive，看清 [1] 加载任务如何接到 [2] 准备、[3] 执行和 [4] 收束；这一步理解的是编排与交接。[5] 补池保留为背景。

**本轮展开的位置**：[1] 的任务加载，以及进入 [2] 前提供回调、调用 fleet.run 的位置。要解决的问题是：任务与处理函数分别从哪里来，怎样交给整批运行？代码末尾的 results 则在 [4] 完成后才拿到。

以下是 3.1 中 NOW 标记对应的 main:84–93 教学裁剪，从运行配置已取得的位置开始，省略未启用的预拉取分支及数据源参数。注释中的阶段号与 3.1 相同。全图与下方代码均保留源码的嵌套调用形式：main 没有名为 source 或 process_fn 的中间变量；这些对象传入方法后，才由对应形参接收。

```python
# NOW: main L84-L93, call sites only
# Phase [1]: create the manager
fleet = SandboxFleet(config)

# Phase [1]: load tasks before running
fleet.load_tasks(SweBenchSource(...))

# Enter phase [2]: provide the callback and start the batch
# Receive results after phase [4]
results = fleet.run(_record(swebench_probe), strategy=strategy,
                    concurrency=max_concurrent)
```

1. **创建对象，对应 [1]**：main 取得 fleet 管理对象，供后续调用使用。
2. **加载任务，对应 [1]**：fleet.load_tasks 完成后，运行层可以使用 fleet.tasks。
3. **提供回调，对应 [2] 入口前**：Python 先求值 _record(swebench_probe)，取得传给 fleet.run 的 process_fn；此时尚未执行探针。
4. **发起运行，对应 [2] 入口**：main 调用 fleet.run，把处理函数、策略和并发度交给运行层。
5. **接收结果，对应 [4] 返回**：main 等待整批运行返回，再把返回值保存为 results。中间经历的准备、执行和清理由 run_naive 组织，留到本步稍后阅读。

**本轮停在 main 接住 results：能指出任务加载位置、回调来源和整批运行的交接点即可。** 暂不从 fleet.run 向下追读。随后仍在 Step 000 内，从图中 LATER 标记的 [run_naive 函数卡](../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md)看它怎样连接 [2]、[3]、[4]；环境创建、单任务执行和补池的内部机制保留为后续问题。

<details>
<summary>源码定位、备用资料与候选说明</summary>

- 固定版本：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 当前源码：[run_swebench_fleet.py:84](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/examples/run_swebench_fleet.py#L84)。
- 下一入口：[strategies.py:82](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py#L82)。
- [本步备用材料](reserve/README.md)：按后续选定问题取用。
- 本候选把原先分散的入口、阅读深度、导航与停止条件集中到第 2 节和当前片段末尾；接口含义就近说明，源码版本与备用资料折叠保存。
- 3.1 保留完整图与阶段编号，在 main 的当前调用处标 NOW，在 run_naive 处标 LATER；五阶段的原有详细说明放入折叠区。3.2 沿用相同标记与阶段号，分别说明本步覆盖范围与本轮实际展开位置。
- 实际阅读转到下一轮时，只需在正式采用后更新当前入口、局部片段及停止位置；不因本轮切换重写完整主线，也不把历史状态改成已掌握。

</details>
