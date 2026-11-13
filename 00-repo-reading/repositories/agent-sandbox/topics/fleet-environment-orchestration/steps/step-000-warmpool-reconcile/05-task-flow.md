# 05 · 从任务输入到一批沙箱任务的执行与返回

> main 创建 Fleet、加载任务并提供处理函数；Fleet.run 选择策略，run_naive 安排准备、执行和清理；任务结果随后沿调用链返回 main。

[本步 scope 与完整导航](01-scope.md) · [函数与类记录](02-short-term-memory/overview.md) · [本次收束](04-flow.md#step000-skeleton-closure) · [项目唯一进度](../../../../README.md#current-reading)

## 1. 本步建立哪一层整体模型

采用 SWE-bench 示例的 naive、单轮、非 recycle、结束后清理路径。本步从 main 的配置、任务和回调输入，连接到运行策略、结果返回；环境准备和执行器内部先理解接口。

1. config 说明运行规则和可用资源，包括集群、环境模板及并发预算。
2. source 提供具体任务，load_tasks 将其保存为 fleet.tasks。
3. process_fn 指定每条任务实际做什么。本例是探针回调，不是完整解题与评分。

## 2. 已读部分怎样接起来

以下是调用层级摘要，不是可执行代码。保留本步已接触的关键关系；配置解析、日志及失败处理细节省略。

```text
main
  1. fleet = SandboxFleet(config)
       -> __init__: configuration, clients, initial state
  2. fleet.load_tasks(SweBenchSource(...))
       -> source.load() via to_tasks -> fleet.tasks
  3. results = fleet.run(_record(swebench_probe), ...)
       -> choose strategy and executor
       -> plan if missing; enter monitoring and reporting
       -> run_naive(fleet, process_fn, concurrency, ...)
            a. fleet.setup()
            b. executor(fleet, fleet.tasks, process_fn, concurrency)
            c. finally: fleet.teardown() when teardown=True
            <- task results after cleanup
       <- task results after context exit
  4. print results
```

1. [构造 Fleet](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.__init__.md)得到管理对象；这不等于容器群已经运行。[类卡](02-short-term-memory/classes/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.md)集中说明对象状态。
2. [load_tasks](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.load_tasks.md)保存完整 Task 列表，image 只是每条任务的一个字段；此时还没有执行任务。
3. [Fleet.run](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.run.md)选择 run_naive 和默认执行器，并把同一个 Fleet、回调、并发度和清理开关继续传下去。
4. [run_naive](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md)先准备环境，再调用 executor，最后按开关清理。可领取的是沙箱环境，清理对象是运行资源。
5. 正常完成后，结果经 Fleet.run 返回 [main](02-short-term-memory/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md)。return 表达式先取得结果，finally 执行后才真正完成 run_naive 的返回。

## 3. 最后得到什么

1. 调用方得到任务结果列表。当前成功项包含 instance_id、image、cluster、hostname 和探针输出文本；默认执行器也可能将单任务普通异常放入相应位置。
2. Fleet 上保留运行报告，和业务结果列表是不同的记录。
3. 当前路径执行整批清理。管理对象、任务数据和任务结果不能与远端运行资源混为一谈。

naive、sliding、pipelined、none 是并列策略，主要改变镜像池准备与任务执行的节奏。共有职责和接口不表示它们都调用或继承 run_naive。

## 4. 本步的收束与后续衔接

本步按“读通整体调用骨架”收束：已实际讨论配置与任务的区别、对象初始化、任务登记、策略分派及准备／执行／清理。用户已经能概括这些主要职责；具体对象边界和返回机制仍有待巩固，原话和未知继续保留在函数卡中。

当前不再追加必读函数。资源计划怎样计算、模板与预热池怎样创建、领取与回收怎样协调、其他策略的内部实现，留到对应问题单独阅读。

下一步建议另选“环境准备”问题：从 setup 调用处定位 [SandboxFleet.start_warmpools](https://github.com/dextermayhewjd/agent-sandbox/blob/37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py#L1144)，看已有资源计划怎样交给预热执行并等待就绪。这里只记录候选与理由，尚未开始 Step 001 或创建对应函数卡。

<details>
<summary>来源与验证范围</summary>

- 固定源码：37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。
- 当前调用方：examples/agent-sandbox-rl/examples/run_swebench_fleet.py:79–99。
- 主要实现：fleet.py 的 __init__:139、load_tasks:429、run:2060；strategies.py 的 run_naive:82、process_parallel:34。
- 本页是对已发生阅读的助手总结；原始表述、澄清及用户明确未知见 04-flow 和各函数卡。阅读范围收束不表示每项内部机制均已掌握。
- 仅有静态源码核对与此前记录的 Python 层替代环境实验，没有运行真实 Kubernetes 沙箱、Agent 解题或训练。

</details>
