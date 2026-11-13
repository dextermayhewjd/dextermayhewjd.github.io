# Step 000 · 整体调用骨架

[项目入口与唯一进度](../../../../README.md#current-reading) · [打开 scope](01-scope.md)

## 本步问题

SWE-bench 示例由谁提供任务和处理函数，怎样经过准备、执行、清理，最后交回结果？

当前主线连接三个入口：

1. [main](02-short-term-memory/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md)：先看输入从哪里来、结果回到哪里。
2. [SandboxFleet.run](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.run.md)：当前看策略、执行器、运行条件与结果交接。
3. [run_naive](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md)：再看整批运行的三个阶段。

scope 保留完整主线，用于看清这些入口在整体流程中的位置。当前同时使用 [SandboxFleet 类卡](02-short-term-memory/classes/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.md)理解 main 第一处调用的对象职责与初始状态；数据加载、执行器和探针的内部实现继续按需回查。

main 第一处构造调用的初始化流程，单独进入 [SandboxFleet.__init__ 方法卡](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.__init__.md)，读完返回 main。类卡只保留状态、摘要和入口。

下一处任务加载调用使用 [SandboxFleet.load_tasks 方法卡](02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.load_tasks.md)，记录任务来源怎样转换成列表、保存到 fleet.tasks 并返回。

## 本步入口

1. [阅读范围与骨架](01-scope.md)。
2. [本步短期记忆](02-short-term-memory/overview.md)。
3. [前序长期记忆](03-long-term-memory/overview.md)：仍按首步保留“暂无前序继承”。
4. [实际讨论过程](04-flow.md)。
5. [本步任务交接总结](05-task-flow.md)：配置、任务、运行策略、清理与结果返回的完整关系；保留后续未知。

<details>
<summary>此前积累的材料</summary>

- [备用函数与类卡](references/reserve/README.md)：暂不作为当前步骤的阅读内容，保留原话、来源、未知和认识时间。
- [收窄前的范围与入口快照](references/history/2026-11-04-before-step000-focus/README.md)。

</details>

源码版本仍为 37ced32b5d500f1c4baf4eaa38d5cfaedd2998e1。此前从 run_naive 出发的讨论与用户表述完整保留；2026-11-04 按用户要求收窄当前步骤、将其余记录暂存备用。归位不是新的掌握，也不表示需要清零后重学。
