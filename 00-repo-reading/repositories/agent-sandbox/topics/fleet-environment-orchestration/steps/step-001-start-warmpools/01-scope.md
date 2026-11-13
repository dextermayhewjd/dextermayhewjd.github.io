# 01 · Step 001：资源计划怎样进入预热与就绪等待

[本步入口](README.md) · [项目进度](../../../../README.md#current-reading) · [完整主线](#whole-flow) · [本步阅读导航](#reading-navigation) · [上一步完整路径](../step-000-warmpool-reconcile/01-scope.md#reading-navigation)

## 1. 本步解决什么问题

上一步知道 run_naive 会调用 setup 准备环境。这一步追问：**已有镜像池资源计划，怎样按预算交给预热执行，等待到什么时候才能继续任务？**

1. 已回查 setup 的准备顺序，现在看 start_warmpools：取得计划条目、按创建预算分波、提交预热与等待。
2. 需要解释它的委派时，再进入 _warm_entries 和 _warm_entry 两层，接到模板、预热池及就绪检查的接口。
3. 本步停在 Python 侧的资源接口交接；计划的放置算法、Kubernetes 控制器内部及任务执行循环继续作为背景。

## 2. 从哪个函数进入

**当前进入 [SandboxFleet.start_warmpools](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.start_warmpools.md)。** 入口仍是 setup 的第 [6] 项，即 fleet.py:1422 的调用。

1. **从哪里来**：[setup](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md) 已检查运行条件并调用 plan，随后传入 wait=True、create_budget。
2. **这一轮的问题**：先确认预热池提前准备了什么、任务怎样领取，再通过[术语与调用时机说明](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.start_warmpools.md#warm-pool-wave)分清 warm、warm pool、wave 与任务进度，再回到分波和 wait；暂不继续下钻。
3. **第一轮停在哪里**：看清本函数如何向 _warm_entries 交付计划；下一层先按接口理解，不展开线程分发与单池创建。

进入 start_warmpools 的最小背景：

| 名称 | 本步先知道什么 |
| --- | --- |
| entries | FleetPlan 中的 PlanEntry 列表；每项描述一个镜像在选定集群上的池，包含 image、cluster、template、pool、replicas 等信息 |
| budget | 一波按目标副本数汇总的创建预算；不是 Task 数或线程数。create_budget 未传时取 config.warm_create_budget，当前默认 1000 |
| wait | 是否要求等待；当前 setup 调用传 True。分波路径中间波始终等待，末波使用传入的 wait |

先沿正常新建路径：adopt_existing=False、budget>0、wait=True。单个池不会被拆开，若它自身的 replicas 已超过预算，会单独形成一波；不能把 budget 理解为无例外的严格上限。

## 3. 整体位置与本步阅读导航

<a id="whole-flow"></a>

### 3.1 完整主线：用来定位当前步骤

这张图保留任务加载、环境准备、逐任务执行、结果返回及并行补池。图中 [1]–[5] 对应下面的 3.1.1–3.1.5，是程序阶段，不是本步要逐个读透的函数清单。

**图中 NOW 标出当前的 start_warmpools，setup 作为它的调用方保留。** Step 000 的输入、运行和返回路径完整保留；_warm_entries 与 _warm_entry 是本步按需下钻的两层，资源接口和控制器只作背景。

当前仍选择 SWE-bench 示例的 naive、非 recycle、PREPULL=False、keep_warm=False 路径。这里的箭头混合展示调用与资源交接，跨 Kubernetes 组件的部分由异步协调完成；[5] 从领取处触发，可与任务执行重叠。

```python
main()  # Step 000 context
  # [1] load tasks
  -> fleet = SandboxFleet(config)  # earlier: create manager
  -> fleet.load_tasks(SweBenchSource(...))  # earlier: create source, then load tasks
       # source is a parameter of load_tasks, not a local variable in main
       -> to_tasks(source) -> source.load() -> tasks: list[Task]
       -> fleet.tasks = tasks

  # [2] prepare environments
  -> results = fleet.run(_record(swebench_probe), ...)  # Step 000 context
       -> self.plan()  # if self.plan_ is None
       -> with self.overcommit_guard(...), self._obs.run(...):
            -> run_naive(...)  # Step 000 context
                 -> fleet.setup()  # caller context
                      -> fleet.start_warmpools(...)  # Step 001 | NOW
                           -> self._warm_entries(...)  # a wave of plan entries
                                -> self._warm_entry(...)  # one image pool
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

### 3.2 本步面包屑：从 setup 进入预热入口，再逐层返回

[main](03-long-term-memory/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md) → [Fleet.run](03-long-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.run.md) → [run_naive](03-long-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md) → [setup：调用方](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md) → **[start_warmpools：当前](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.start_warmpools.md)** → [_warm_entries：按需下一层](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1111) → [_warm_entry：再下一层](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1008)

前面的对象构造、任务加载、策略分派仍在 3.1 完整图和[上一步导航](../step-000-warmpool-reconcile/01-scope.md#reading-navigation)中保留。本步的 1–5 是下面表格的阅读位置，不是程序新增加的五个阶段；各入口会持续保留，只移动当前标记。

以下是定位用的真实调用片段，不是完整函数体。start_warmpools 的两次 wave 调用分别位于分波循环的提交位置和循环后的末波位置；这里省略组装 wave 的语句，具体解释留到实际函数阅读。

```python
# [2] setup:1422 -> [3] start_warmpools
self.start_warmpools(wait=True, create_budget=create_budget)

# [3] start_warmpools:1164-1165
budget = self.config.warm_create_budget if create_budget is None else create_budget
entries = (self.plan_ or self.plan()).entries

# [3] loop submission:1184 -> [4] _warm_entries
self._warm_entries(wave, wait=True)

# [3] final-wave submission:1192 -> [4] _warm_entries
self._warm_entries(wave, wait=wait)
```

| 阅读位置与入口 | 这里要弄清什么 | 读完回到哪里 |
| --- | --- | --- |
| 1. [run_naive](03-long-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md)，已读背景 | setup 返回前，executor 还没有开始处理任务 | 定位第 2 处，不重读上一阶段 |
| 2. [setup](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md)，调用方回查 | 计划怎样作为已有条件，何处调用 start_warmpools | 第 1422 行进入 3；返回后 setup 才返回给 run_naive |
| 3. [start_warmpools](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.start_warmpools.md)，当前主攻 | 按什么单位分波，什么时候提交，什么时候等待 | 首轮在对 4 的委派处停；整个调用完成后回到 setup:1422 |
| 4. [_warm_entries](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1111)，需要时展开 | 一组条目怎样顺序或并发交给 _warm_entry，何时这一组才完成 | 回到 start_warmpools:1184 或 1192，再处理后续条目或返回 |
| 5. [_warm_entry](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1008)，最多到此层 | 一项计划怎样定位集群、提交模板与池、登记状态并等待就绪 | 回到 _warm_entries；资源接口与控制器内部不继续展开 |

**本步停止边界**：连起“计划条目 → 预热一组 → 预热一个池 → 资源接口与就绪结果”，再返回 setup 和 run_naive。短期卡按实际阅读建立，当前已有 setup 和 start_warmpools 两张卡；表中的下一层不代表已经读过。

<details>
<summary>其他分支、已有资料与源码边界</summary>

1. adopt_existing=True 或 budget<=0 时，start_warmpools 直接把全部 entries 交给 _warm_entries；这些分支保留定位，本轮先不展开接管已有池的机制。
2. wait=False 不保证整个分波过程不等待：中间波仍传 True，末波才传 wait。本轮从 setup 的 wait=True 入口开始。
3. _warm_entry 中的已有预热复用、跨运行归属冲突与共享池路径先作为分支背景；资源创建/更新与状态检查的 API 内部、Go controllers 另行确定范围。
4. 本步只知道 entries 的用途，不重推 plan 的放置和副本计算算法。必要时查看 [PlanEntry 定义](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L85)，不预建类型卡。
5. [此前 setup 详细记录](../step-000-warmpool-reconcile/references/reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md)仍在原步骤备用区；保留为原始来源；本步已按用户要求复制到 02，调取本身不代表新的掌握。
6. [前序继承索引](03-long-term-memory/overview.md)包含上一阶段的五张函数/方法卡和一张类卡；原始讨论、日期和未知完整保留。
7. 固定源码：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。入口 1144–1192；下一层 1111–1142、1008–1081；setup 调用位置 1422。
8. 本页是静态阅读范围与导航，没有部署、拉取镜像、运行任务或验证吞吐；本步尚无完成总结。

</details>
