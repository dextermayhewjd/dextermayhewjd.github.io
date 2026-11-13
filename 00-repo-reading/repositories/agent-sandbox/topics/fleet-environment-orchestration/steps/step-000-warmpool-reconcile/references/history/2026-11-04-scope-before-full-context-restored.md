> 2026-11-04：恢复完整上下文主线之前的局部 scope，保留作调整历史。

# 01 · Step 000：先看整体调用骨架

[本步入口](../../README.md) · [当前两张函数卡](../../02-short-term-memory/overview.md) · [项目进度](../../../../../../README.md#current-reading)

## 1. 阅读目标

本步只回答：**SWE-bench 示例由谁提供任务和处理函数，怎样进入准备、执行、清理，并把结果交回来？**

当前只读两个函数，顺序固定为：

1. main：看调用方怎样接好输入与输出。
2. run_naive：看整批执行的三个阶段。

采用脚本的默认 naive、非 recycle、PREPULL=False、keep_warm=False 路径。SandboxFleet 的内部、数据字段转换、执行器和具体探针只按接口理解；此前积累的详细记录放在本步备用区，出现调用名不代表本步继续下钻。

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

## 3. 两个函数怎样接起来

### 3.1 整体图

图中的 [1]、[2] 对应本步的两张函数卡，也对应下面两个小节。其他调用保留为接口。本图展示正常路径；run_naive 的清理实际放在 finally 中。

```python
main()                                      # [1] Step 000: first
  -> config = FleetConfig(...)
  -> fleet = SandboxFleet(config)
  -> fleet.load_tasks(SweBenchSource(...))
  -> fleet.run(_record(swebench_probe), ...)
       -> run_naive(...)                    # [2] Step 000: next
            -> fleet.setup()
            -> executor(fleet, fleet.tasks, process_fn, concurrency)
            -> fleet.teardown()
       <- results
  -> print(json.dumps(...))
```

#### 3.1.1 [1] main：接好本次运行的输入与输出

1. 取得运行配置。
2. 创建 fleet 管理对象。
3. 调用 load_tasks，将任务保存在 fleet.tasks。
4. 通过 _record(swebench_probe) 取得本例的处理函数。
5. 将处理函数交给 fleet.run；选择 naive 时会进入 run_naive。
6. 等整批结果返回后，打印 JSON。

本步只要明确：**任务加载发生在 fleet.run 之前；处理函数也是由调用方传入的。** 具体如何加载数据、处理函数内部执行什么，留给对应的后续问题。

<a id="task-loading-before-setup"></a>

任务加载的最小顺序是：main 先调用 fleet.load_tasks(...)，再调用 fleet.run(...)；后者进入 run_naive 后才调用 fleet.setup()。因此 setup 开始时，fleet.tasks 已经存在。

#### 3.1.2 [2] run_naive：安排准备、执行与清理

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

### 3.2 当前阅读导航

| 从哪里看 | 读到哪里返回 |
| --- | --- |
| [main](../../02-short-term-memory/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md) | 看到 fleet.run 的调用，带着任务来源和回调来源进入 run_naive |
| [run_naive](../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md) | 看清三次交接，回到 main 接收并打印 results |

### 3.3 本步停止位置

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
