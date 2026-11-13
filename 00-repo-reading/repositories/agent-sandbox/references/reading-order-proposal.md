# 已有材料的回读顺序与拟拆步方案

> 历史拟拆步方案，不是当前进度表。实际 Step 000 已包含构造、任务加载及运行分派的阅读；用户现已确认开始 [Step 001：预热入口](../topics/fleet-environment-orchestration/steps/step-001-start-warmpools/01-scope.md)。下文编号保留当时方案，不能据此重复创建“输入准备”步骤。

[项目当前进度](../README.md#current-reading) · [已有记录索引](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/02-short-term-memory/overview.md) · [本轮讨论](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/04-flow.md#reading-order-and-step-split)

当时的结构调整：用户明确保留现有结构。当前 Step 000 只保留 main 和 run_naive，其他记录已放到同一步的[备用区](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/references/reserve/README.md)。此前项目级资料库方案未采用；下面的 Step 001–004 仍是后续阅读建议，没有建立新步骤。

2026-11-04，按现有 9 个函数/方法记录与 1 张类卡组织导读。以下是建议的阅读结构，不是当时真实的学习时间顺序，也不表示这些拟定步骤已经执行或完成。现有卡片与首次接触记录保留。

## 1. 第一处从哪里开始

先看 [run_swebench_fleet.py 的 main](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/02-short-term-memory/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md)，只提取下方几个交接。

```python
fleet = SandboxFleet(config)
fleet.load_tasks(SweBenchSource(...))
results = fleet.run(_record(swebench_probe), strategy=strategy,
                    concurrency=max_concurrent)
```

这是从真实调用裁剪的骨架；配置、可选预拉取和输出报告先作为背景。先回答：

1. 谁创建管理对象？
2. 谁把数据加载成 Task？
3. 谁选择并传入 process_fn？
4. 整批执行交给谁，结果回到哪里？

接着看 [run_naive](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md) 的 setup、executor、teardown 三个阶段。到这里先有整个任务的骨架，再选择局部实现。

此次把 main 放在回读入口，是因为实际反复出现的缺口是 Task 和回调的来路。并非要求所有仓库都从 main 的第一行深入，也不把配置初始化变成全量前置课。

## 2. 按问题组织的五个拟定步骤

| 拟定步骤 | 这一单元的问题 | 已有材料的顺序 | 阅读边界 |
| --- | --- | --- | --- |
| Step 000 · 整体调用骨架 | 一次运行由谁提供任务和回调，如何进入准备、执行与清理？ | main → run_naive | 只看交接；具体配置、子函数实现先保持接口层 |
| Step 001 · 输入怎样准备好 | 进入策略前，fleet 和 tasks 是怎样得到的？ | SandboxFleet 类卡 → SandboxFleet.__init__ → SweBenchSource.load | 类先看主要字段；以 load_tasks 的最小片段连接 Source 返回值与 fleet.tasks，不追锁、信号和全部客户端构造 |
| Step 002 · 环境怎样准备 | 已有 Task 怎样成为环境准备的输入，setup 返回前完成什么？ | SandboxFleet.setup | 看检查、规划、预热、等待；控制器与副本算法留给独立问题 |
| Step 003 · 一批任务怎样执行 | 执行器怎样用任务、回调和并发度，怎样回收并整理结果？ | process_parallel | 看 _one 与外层线程池的配合；acquire/release 先按输入输出理解 |
| Step 004 · 具体回调做什么 | 选定的回调收到 task/handle 后执行什么，怎样拿回结果？ | _record.fn → swebench_probe → SandboxHandle.exec | 看本例固定命令、Pod 执行通道和结果字典；SDK 底层协议不继续追 |

Step 000 的 main 与 run_naive 是整体定位；后续单元用同一骨架返回相应调用点。Step 004 结束后，再回到 process_parallel 的结果列表和 main 的输出位置，完成这一条探针示例的回顾。

## 3. 全部已有材料的建议回读次序

当前只执行第 1–2 项；第 3–10 项已暂存备用，等进入相应问题时再选用。

1. [main](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/02-short-term-memory/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md)：先定位任务来源、回调来源和输出。
2. [run_naive](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md)：看三个阶段。
3. [SandboxFleet 类卡](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/02-short-term-memory/classes/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.md)：认识主要对象字段。
4. [SandboxFleet.__init__](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.__init__.md)：看初始管理状态。
5. [SweBenchSource.load](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/references/reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/adapters/swebench.py/SweBenchSource.load.md)：看数据如何变成 Task，补上保存到 fleet.tasks 的交接。
6. [SandboxFleet.setup](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/references/reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md)：看环境准备的输入、阶段与结束条件。
7. [process_parallel](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/references/reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/process_parallel.md)：看回调调用与结果整理。
8. [_record.fn](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/references/reserve/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/_record.fn.md)：看本例实际传入的函数，区分返回函数和执行函数。
9. [swebench_probe](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/references/reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/adapters/swebench.py/swebench_probe.md)：看实际命令与返回文本。
10. [SandboxHandle.exec](../topics/fleet-environment-orchestration/steps/step-000-warmpool-reconcile/references/reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/handles.py/SandboxHandle.exec.md)：看命令如何进入既有 Pod。

## 4. 处理已有历史与尚未展开的部分

1. 当前已按用户要求在 Step 000 内归位：02 只留 main 和 run_naive，其他卡片移至 references/reserve。原话、首次接触时间和未知保留。
2. 真正拆分目录时，需要把原 Step 000 作为历史保存，并明确新结构是重组后的导读顺序，不能伪装成当时依次完成了这些步骤。
3. SandboxFleet.run 的策略选择、load_tasks 的转交作为已有代码片段回查；acquire、release、teardown 仍只保留当前已知合同。不能因为新路线需要连接就补出已完成的阅读卡。
4. 对已经说清楚的关系只需短回顾；重新组织材料不清零理解，也不要求全部从头重学。

依据继续采用[先核心、后补前置](../../../../.agents/skills/repo-reading-order/references/inside-out-method.md)和[整体骨架样例](../../../../.agents/skills/repo-reading-scope/references/coding-agent-scope.md)。这里重新确定的是当前具体任务的入口与前置关系，不是新增一套通用课程。
