# Step 000 备用材料

[返回当前 scope](../../01-scope.md) · [当前短期记忆](../../02-short-term-memory/overview.md)

这里集中保留此前讨论积累、当前暂不完整展开的 6 张函数卡。SandboxFleet 类卡与 __init__ 方法卡已按用户要求调回本步 02；原话、来源、认识时间和未知没有因移动而改变。下方同时保留通向这两张活动卡的导航。

当前 Step 000 通过 main 与 run_naive 看整体骨架，并用 SandboxFleet 类卡支持理解对象。备用方法记录按当前问题回查，不默认全部展开。

## 1. 输入与管理对象

1. [SandboxFleet 类卡](../../02-short-term-memory/classes/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.md)。
2. [SandboxFleet.__init__](../../02-short-term-memory/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.__init__.md)。
3. [SweBenchSource.load](functions/examples/agent-sandbox-rl/agent_sandbox_rl/adapters/swebench.py/SweBenchSource.load.md)。

## 2. 环境准备

1. [SandboxFleet.setup](functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md)。

## 3. 整批执行

1. [process_parallel](functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/process_parallel.md)。

## 4. 具体回调与命令通道

1. [_record.fn](functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/_record.fn.md)。
2. [swebench_probe](functions/examples/agent-sandbox-rl/agent_sandbox_rl/adapters/swebench.py/swebench_probe.md)。
3. [SandboxHandle.exec](functions/examples/agent-sandbox-rl/agent_sandbox_rl/handles.py/SandboxHandle.exec.md)。

备用卡中的“本轮”“当前”等文字保留原讨论语境；本次实际阅读位置以项目入口和当前 scope 为准。移动本身不表示遗忘、未读或已掌握，也不自动把这些记录归入新的学习步骤。

当时的完整范围见[收窄前 scope](../history/2026-11-04-before-step000-focus/01-scope.md)，归位依据见[本次讨论](../../04-flow.md#step000-current-only)。
