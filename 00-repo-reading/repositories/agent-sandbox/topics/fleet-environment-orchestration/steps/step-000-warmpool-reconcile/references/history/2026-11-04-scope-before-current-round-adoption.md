# 01 · Step 000：先看整体调用骨架

[本步入口](../../README.md) · [当前两张函数卡](../../02-short-term-memory/overview.md) · [项目进度](../../../../../../README.md#current-reading)

## 1. 阅读目标

本步只回答：**SWE-bench 示例由谁提供任务和处理函数，怎样进入准备、执行、清理，并把结果交回来？**

当前只读两个函数，顺序固定为：

1. main：看调用方怎样接好输入与输出。
2. run_naive：看整批执行的三个阶段。

采用脚本的默认 naive、非 recycle、PREPULL=False、keep_warm=False 路径。SandboxFleet 的内部、数据字段转换、执行器和具体探针只按接口理解；此前积累的详细记录放在本步备用区，出现调用名不代表本步继续下钻。

整体位置由第 3.1 节的完整主线提供；本步只展开第 3.2 节的两个函数。其余节点用于定位，详细材料继续放在备用区。

## 2. 找到入口与编排函数

| 顺序 | 当前入口 | 这一遍要看什么 |
| --- | --- | --- |
| 1 | [main 函数卡](../../02-short-term-memory/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md) | 创建管理对象、加载任务、提供回调、取得整批结果 |
| 2 | [run_naive 函数卡](../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md) | setup、executor、teardown 的调用次序与交接 |

源码固定在 /home/fredkeira/projects/agent-sandbox 的提交 37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。main 位于 examples/agent-sandbox-rl/examples/run_swebench_fleet.py:47；run_naive 位于 examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py:82。

当前需要知道的接口含义：

| 名称 | 本步只需知道 |
| --- | --- |
| fleet | 保存任务与配置、提供环境管理方法的对象 |
| fleet.load_tasks(...) | 把数据来源转换成任务列表，保存到 fleet.tasks |
| process_fn | 调用方提供的单任务处理函数 |
| executor | 执行整批任务、交回结果列表；本例使用 process_parallel |
| fleet.setup() / teardown() | 整批运行前的环境准备 / 退出时的资源清理 |

## 3. 整体位置与本步阅读范围

### 3.1 完整主线：用来定位当前步骤

这张图保留任务加载、环境准备、逐任务执行、结果返回及并行补池。图中 [1]–[5] 对应下面的 3.1.1–3.1.5，是程序阶段，不是本步要逐个读透的函数清单。

**Step 000 只展开带注释标记的 main 和 run_naive。** main 组织本次运行的输入输出；run_naive 在其中连接环境准备、任务执行和清理。其他节点保持可见，帮助看清这两个函数处在什么位置。

当前仍选择 SWE-bench 示例的 naive、非 recycle、PREPULL=False、keep_warm=False 路径。这里的箭头混合展示调用与资源交接，跨 Kubernetes 组件的部分由异步协调完成；[5] 从领取处触发，可与任务执行重叠。

```python
main()  # Step 000: first function
  # [1] load tasks
  -> fleet = SandboxFleet(config)
  -> fleet.load_tasks(SweBenchSource(...))
       # source is a parameter of load_tasks, not a local variable in main
       -> to_tasks(source) -> source.load() -> tasks: list[Task]
       -> fleet.tasks = tasks

  # [2] prepare environments
  -> results = fleet.run(_record(swebench_probe), ...)
       -> run_naive(...)  # Step 000: second function
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

### 3.2 本步展开：只看两个编排函数

#### 3.2.1 main：接好本次运行的输入与输出

1. 取得运行配置。
2. 创建 fleet 管理对象。
3. 调用 load_tasks，将任务保存在 fleet.tasks。
4. 通过 _record(swebench_probe) 取得本例的处理函数。
5. 将处理函数交给 fleet.run；选择 naive 时会进入 run_naive。
6. 等整批结果返回后，打印 JSON。

本步只要明确：**任务加载发生在 fleet.run 之前；处理函数也是由调用方传入的。** 具体如何加载数据、处理函数内部执行什么，留给对应的后续问题。

<a id="task-loading-before-setup"></a>

任务加载的最小顺序是：main 先调用 fleet.load_tasks(...)，再调用 fleet.run(...)；后者进入 run_naive 后才调用 fleet.setup()。因此 setup 开始时，fleet.tasks 已经存在。

#### 3.2.2 run_naive：安排准备、执行与清理

```python
try:
    fleet.setup()          # [2.1] prepare
    return executor(fleet, fleet.tasks, process_fn, concurrency)  # [2.2]
finally:
    if teardown:
        fleet.teardown()   # [2.3] clean up
```

1. [2.1] 准备：调用 fleet.setup。
2. [2.2] 执行：把同一个 fleet、任务列表、处理函数和并发度交给 executor。
3. [2.3] 清理：退出时进入 finally，按 teardown 决定是否清理，再完成返回。

本步先把 executor 当成“收到任务后执行，并交回结果列表”的接口。

<a id="reading-navigation"></a>

### 3.3 当前阅读导航

| 从哪里看 | 读到哪里返回 |
| --- | --- |
| [main](../../02-short-term-memory/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md) | 看到 fleet.run 的调用，带着任务来源和回调来源进入 run_naive |
| [run_naive](../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md) | 看清三次交接，回到 main 接收并打印 results |

### 3.4 本步停止位置

1. 能指出任务列表在进入运行前由谁加载。
2. 能指出 process_fn 由谁提供。
3. 能说明准备、执行、清理的先后关系。
4. 能说明整批结果回到哪里。

达到这些关系的理解后，再确定下一步。当前不把子函数内部、Kubernetes 控制器或探针命令扩展进来。

<details>
<summary>备用材料与调整历史</summary>

- [本步备用区](../reserve/README.md)：7 张函数卡和 1 张类卡，保留已有内容，按后续需要选用。
- [收窄前的 scope](2026-11-04-before-step000-focus/01-scope.md)：保留此前探索的范围和图示。
- [实际讨论过程](../../04-flow.md#step000-current-only)：说明这次只调整当前范围，不改变原始认识和来源。

</details>
