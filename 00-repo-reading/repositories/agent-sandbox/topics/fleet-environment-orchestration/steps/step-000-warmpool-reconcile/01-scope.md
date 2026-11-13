# 01 · Step 000：整体主线与本轮阅读

[本步入口](README.md) · [项目进度](../../../../README.md#current-reading) · [看完整主线](#whole-flow) · [阅读导航](#reading-navigation)

> 本步主线：main 的输入与结果交接 → SandboxFleet.run 的策略分派 → run_naive 的准备、执行与清理。3.1 保留完整图与按需展开的阶段说明，3.2 用面包屑、简短调用片段和返回位置连接各张短期卡。

## 1. 本步解决什么问题

看清 SWE-bench 示例怎样提供任务和处理函数，再由运行层完成准备、执行、清理，最后交回结果。Step 000 沿以下三个编排入口接续；构造和任务加载是已发生的局部回查：

1. **main：调用方。** 看 [1] 的任务加载、进入 [2] 前的回调交接，以及如何接住 [4] 返回的结果。
2. **SandboxFleet.run：上层运行入口。** 看策略与执行器选择、初始计划、运行上下文及策略调用。
3. **run_naive：当前主攻。** 看它怎样依次组织 [2] 的 setup、[3] 的 executor 和 [4] 的 teardown；关注调用次序、数据交接与返回时机。

## 2. 这一轮先看哪里

当前沿 Fleet.run 的 fn(...) 进入 [run_naive 方法卡](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md)，仍采用非 recycle、单轮、teardown=True 路径。其他三种策略先看[简表](../../../../references/rl-batch-flow-and-entry.md#strategy-comparison)，不展开实现。

1. **主攻位置**：strategies.py:82–97，只看 setup、executor、teardown 的交接。
2. **当前问题**：何时环境准备好、何时执行任务、何时清理，以及结果何时交回 Fleet.run？
3. **阅读边界**：说明三个阶段与返回次序后，沿原路回到 run 和 main；本轮不继续下钻子函数。

## 3. 整体位置与本轮片段

<a id="whole-flow"></a>

### 3.1 完整主线：用来定位当前步骤

这张图保留任务加载、环境准备、逐任务执行、结果返回及并行补池。图中 [1]–[5] 对应下面的 3.1.1–3.1.5，是程序阶段，不是本步要逐个读透的函数清单。

**图中 NOW 标出当前主攻的 run_naive；Fleet.run 保留为上层调用入口。** main、对象构造和任务加载保留为调用背景；其他节点用于整体定位，不要求本轮逐个进入。NOW 对应下方 3.2 的局部代码。

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
  -> results = fleet.run(_record(swebench_probe), ...)  # Step 000 | caller: SandboxFleet.run
       -> self.plan()  # if self.plan_ is None
       -> with self.overcommit_guard(...), self._obs.run(...):
            -> run_naive(...)  # Step 000 | NOW: run_naive L82-L97
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

### 3.2 阅读导航：保留从起点到当前的完整路径

本步从 main 出发，已经经过对象构造和任务加载，当前来到运行分派。**前面的入口持续保留；当前已从第 4 处 run 的 fn(...) 进入第 5 处 run_naive；读完返回第 4 处，再回到 main。** 这里的 1–5 是阅读位置，和 3.1 的程序阶段编号分开使用。

1. [main：先定位调用方](02-short-term-memory/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md)。
2. 从 main:84 回查 [SandboxFleet 类卡](02-short-term-memory/classes/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.md)和 [__init__](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.__init__.md)，然后回到 main。
3. 从 main:85–87 进入 [load_tasks](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.load_tasks.md)，然后回到 main。
4. 从 main:92–93 进入 [SandboxFleet.run：上层调用](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.run.md)。
5. 从 run 的 fn(...) 进入 [run_naive：当前](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md)，读完返回 run，再回到 main。

下面保留各次跳转对应的最小调用片段。三个代码区域分别属于 main、SandboxFleet.run 和 run_naive，参数与非跳转语句按需省略；__init__ 不会调用 load_tasks，二者由 main 先后调用。

```python
# [1] main:84-93
fleet = SandboxFleet(config)                 # [2] open __init__, then return here
fleet.load_tasks(SweBenchSource(...))         # [3] open load_tasks, then return here
results = fleet.run(_record(swebench_probe), ...)  # [4] caller: SandboxFleet.run

# [4] SandboxFleet.run:2092, 2113-2114
fn = STRATEGIES[strategy]
results = fn(...)  # [5] NOW: run_naive when strategy="naive"

# [5] run_naive:93-97
try:
    fleet.setup()
    return executor(...)
finally:
    if teardown:
        fleet.teardown()
```

| 阅读位置与入口 | 这里要看清什么 | 看完后回到哪里 |
| --- | --- | --- |
| 1. [main](02-short-term-memory/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md) | 配置、任务、处理函数怎样组成一次运行 | 依次进入 2、3、4；最终在 92 行接住 results |
| 2. [SandboxFleet 类卡](02-short-term-memory/classes/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.md) / [__init__](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.__init__.md) | 得到什么管理对象，config 如何变成对象配置和初始状态 | main:84 构造结束，再看 85–87 行的任务加载 |
| 3. [load_tasks](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.load_tasks.md) | source 如何交出 Task 列表，并保存到 fleet.tasks | main:85–87 调用结束，默认跳过预拉取，再到 92–93 行 |
| 4. [SandboxFleet.run](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.run.md) | 策略、执行器、初始计划与运行上下文怎样接好；fn 指向谁 | 从 2113 行的 fn(...) 进入 5；之后接回结果并返回 main |
| 5. [run_naive](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md) | 只看准备、执行、清理的次序与结果交接 | 返回 run:2113，再经 run:2128 回到 main:92 |

**本步边界**：保留以上已经接触和准备接续的入口，具体函数解释分别进入短期卡。run_naive 下的 setup、executor、teardown 本轮只看接口，不继续下钻。以后推进当前标记时，不移走第 1–3 处，也不把它们降成隐藏的备用链接。

<details>
<summary>源码定位、备用资料与采用记录</summary>

- 固定版本：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 调用方源码：[run_swebench_fleet.py:84](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/examples/run_swebench_fleet.py#L84)。
- 上层调用：[fleet.py:2060](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L2060)。
- 当前方法：[strategies.py:82](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py#L82)。
- [本步备用材料](references/reserve/README.md)：按后续选定问题取用。
- 本页把原先分散的入口、阅读深度、导航与停止条件集中到第 2 节和当前片段末尾；接口含义就近说明，源码版本与备用资料折叠保存。
- 3.1 保留完整图与阶段编号，保留 fleet.run 的调用位置，在 run_naive 处标 NOW；五阶段的原有详细说明放入折叠区。3.2 的五个阅读位置持续保留：main、对象构造、任务加载、run、run_naive；片段与导航表同号，具体解释留在短期卡。
- 这条阅读路径在本步内保持稳定；当前阅读位置变化时，更新当前/下一处标记，不用新的函数讲解覆盖 3.2。仅在实际确认新的范围或回查分支后补充必要导航。
1
- 2026-11-04 用户确认采用本版；[替换前的 scope](references/history/2026-11-04-scope-before-current-round-adoption.md)保留原内容与导航。

</details>
