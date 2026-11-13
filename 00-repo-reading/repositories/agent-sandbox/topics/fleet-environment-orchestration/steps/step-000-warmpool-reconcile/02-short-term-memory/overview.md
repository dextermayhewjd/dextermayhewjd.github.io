# 02 · 本步函数与类记录

[本步 scope](../01-scope.md) · [项目进度](../../../../../README.md#current-reading)

| 阅读顺序 | 源码文件 | 函数记录 | 本步重点 |
| --- | --- | --- | --- |
| 1 | examples/agent-sandbox-rl/examples/run_swebench_fleet.py | [main](functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md) | 任务和处理函数从哪里来，整批结果回到哪里 |
| 2 | examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py | [SandboxFleet.__init__](functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.__init__.md) | 初始化顺序与副作用；当前具体看配置复制，读完返回 main |
| 3 | examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py | [SandboxFleet.load_tasks](functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.load_tasks.md) | 来源转换为 Task 列表、保存到 fleet.tasks、返回同一列表 |
| 4 | examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py | [SandboxFleet.run](functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.run.md) | 选择策略和执行器，准备计划与运行上下文，调用策略并返回 |
| 5 | examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py | [run_naive](functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md) | 当前：setup、executor、teardown 三段交接与 finally 后返回 |

## 当前对象记录

| 源码文件 | 类记录 | 本轮重点 |
| --- | --- | --- |
| examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py | [SandboxFleet](classes/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.md) | 对象职责、字段初始状态、初始化摘要与方法入口 |

当前有两张编排函数卡、三张 Fleet 方法卡和一张类卡。类卡说明对象状态，__init__、load_tasks、run 方法卡分别支持 main 的构造、任务加载和整批运行调用；其余六张方法记录仍在[本步备用区](../references/reserve/README.md)，原话、来源与未知继续保留。
