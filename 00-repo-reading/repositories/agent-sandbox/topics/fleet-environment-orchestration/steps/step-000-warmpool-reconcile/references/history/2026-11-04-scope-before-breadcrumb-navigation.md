# 01 · Step 000：整体主线与本轮阅读

[本步入口](../../README.md) · [项目进度](../../../../../../README.md#current-reading) · [看完整主线](#whole-flow) · [直接看本轮代码](#current-excerpt)

> 本步主线：main 的输入与结果交接 → SandboxFleet.run 的策略分派 → run_naive 的准备、执行与清理。3.1 保留完整图与按需展开的阶段说明，3.2 聚焦本轮代码。

## 1. 本步解决什么问题

看清 SWE-bench 示例怎样提供任务和处理函数，再由运行层完成准备、执行、清理，最后交回结果。Step 000 沿以下三个编排入口接续；构造和任务加载是已发生的局部回查：

1. **main：调用方。** 看 [1] 的任务加载、进入 [2] 前的回调交接，以及如何接住 [4] 返回的结果。
2. **SandboxFleet.run：当前主攻。** 看策略与执行器选择、初始计划、运行上下文及策略调用。
3. **run_naive：本步稍后阅读。** 看它怎样依次组织 [2] 的 setup、[3] 的 executor 和 [4] 的 teardown；关注调用次序、数据交接与返回时机。

## 2. 这一轮先看哪里

当前从 main:92–93 进入 [SandboxFleet.run 方法卡](../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.run.md)，固定 naive、epochs=1、recycle=False、keep_warm=False 路径。

1. **主攻位置**：fleet.py:2086–2114，先分清 process_fn、executor、局部变量 fn，再看计划与策略交接。
2. **当前问题**：已有 config 和 tasks，run 怎样安排整批运行，并将它交给 run_naive？
3. **阅读边界**：跟到调用 run_naive 的位置，说明 results 的返回去向后停；plan、监控和报告先按职责理解，暂不进入它们的内部机制。

## 3. 整体位置与本轮片段

<a id="whole-flow"></a>

### 3.1 完整主线：用来定位当前步骤

这张图保留任务加载、环境准备、逐任务执行、结果返回及并行补池。图中 [1]–[5] 对应下面的 3.1.1–3.1.5，是程序阶段，不是本步要逐个读透的函数清单。

**图中 NOW 标出当前主攻的 SandboxFleet.run；LATER 标出接下来要读的 run_naive。** main、对象构造和任务加载保留为调用背景；其他节点用于整体定位，不要求本轮逐个进入。NOW 对应下方 3.2 的局部代码。

当前仍选择 SWE-bench 示例的 naive、非 recycle、PREPULL=False、keep_warm=False 路径。这里的箭头混合展示调用与资源交接，跨 Kubernetes 组件的部分由异步协调完成；[5] 从领取处触发，可与任务执行重叠。

```python
main()  # Step 000 | caller
  # [1] load tasks
  -> fleet = SandboxFleet(config)  # earlier: create manager
  -> fleet.load_tasks(SweBenchSource(...))  # earlier: create source, then load tasks
       # source is a parameter of load_tasks, not a local variable in main
       -> to_tasks(source) -> source.load() -> tasks: list[Task]
       -> fleet.tasks = tasks

  # [2] prepare environments
  -> results = fleet.run(_record(swebench_probe), ...)  # Step 000 | NOW: SandboxFleet.run L2086-L2114
       -> self.plan()  # if self.plan_ is None
       -> with self.overcommit_guard(...), self._obs.run(...):
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

<a id="task-loading-before-setup"></a>

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
2. main 将回调交给 fleet.run；run 选中 naive 策略和默认执行器。
3. run 在计划不存在时调用 plan，取得初始资源计划。
4. run 进入资源监控与运行记录的范围，然后调用选中的 run_naive。
5. run_naive 调用 fleet.setup，根据已有 fleet.tasks 组织检查、规划和环境准备。
6. 准备 SandboxTemplate，描述环境配置。
7. 创建或更新 SandboxWarmPool，表达备用数量目标。
8. WarmPool controller 按目标创建所需 Sandbox CR。
9. 核心 Sandbox controller 协调 Pod 等子资源。
10. Kubernetes 调度器为 Pod 选择节点。
11. kubelet 和容器运行时启动容器。
12. setup 等待当前场景要求的就绪条件，正常返回后才进入 [3]。

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
4. fleet.run 退出运行记录与监控上下文，将整批结果返回 main。
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

<a id="reading-navigation"></a>
<a id="current-excerpt"></a>

### 3.2 本轮主攻 SandboxFleet.run：把整批任务交给策略

对应 3.1 的 [2] 入口，位于 main 完成任务加载之后、run_naive 准备环境之前。当前任务列表已在 self.tasks；process_fn 是 main 提供的单任务处理函数。

以下是默认单轮路径的教学裁剪，省略检查、复用、多轮循环、环境信息采集和日志；保留计划、运行上下文、调用及返回。

```python
# [1] choose strategy and executor
conc = concurrency or self.config.max_concurrent
fn = STRATEGIES[strategy]
executor = process_parallel

# [2] prepare the initial plan
if self.plan_ is None:
    self.plan()
expected = self.plan_.total_replicas if self.plan_ else None

# [3] enter run contexts
with self.overcommit_guard(expected), self._obs.run(strategy) as report:
    self.report = report
    # [4] delegate to run_naive in the current path
    results = fn(self, process_fn, conc, teardown=not keep_warm,
                 executor=executor)

# [5] return to main
return results
```

这里 [1]–[5] 仅对应本段 run 内部的五处位置，与全图的程序阶段分开理解：

1. **选择**：fn 当前为 run_naive；executor 为 process_parallel；process_fn 仍是单任务回调。
2. **计划**：已有任务与配置共同用于生成初始资源计划，expected 提供监控依据。
3. **运行上下文**：监控与报告包围实际策略调用，报告保存到 self.report。
4. **交接**：把同一个 Fleet、回调、并发度、执行器和清理开关交给 run_naive。
5. **返回**：正常完成后退出上下文，results 返回 main；self.report 是独立的运行记录。

**本轮停止位置**：看清第 4 处交接及第 5 处返回，不展开策略内部。具体输入、三个函数角色、源码行号与尚不清楚见 [SandboxFleet.run 方法卡](../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.run.md)；下一入口仍是 [run_naive](../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md)。

<details>
<summary>源码定位、备用资料与采用记录</summary>

- 固定版本：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 调用方源码：[run_swebench_fleet.py:84](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/examples/run_swebench_fleet.py#L84)。
- 当前方法：[fleet.py:2060](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L2060)。
- 下一入口：[strategies.py:82](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py#L82)。
- [本步备用材料](../reserve/README.md)：按后续选定问题取用。
- 本页把原先分散的入口、阅读深度、导航与停止条件集中到第 2 节和当前片段末尾；接口含义就近说明，源码版本与备用资料折叠保存。
- 3.1 保留完整图与阶段编号，在 fleet.run 的当前调用处标 NOW，在 run_naive 处标 LATER；五阶段的原有详细说明放入折叠区。3.2 沿用相同标记与阶段号，分别说明本步覆盖范围与本轮实际展开位置。
- 实际阅读转到下一轮时，只需更新当前入口、局部片段及停止位置；不因本轮切换重写完整主线，也不把历史状态改成已掌握。

- 2026-11-04 用户确认采用本版；[替换前的 scope](2026-11-04-scope-before-current-round-adoption.md)保留原内容与导航。

</details>
