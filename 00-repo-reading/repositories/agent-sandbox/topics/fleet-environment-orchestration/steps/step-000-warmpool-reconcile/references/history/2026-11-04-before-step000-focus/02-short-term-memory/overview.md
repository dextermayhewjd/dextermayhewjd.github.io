> 2026-11-04：Step 000 收窄为第一步整体骨架之前的快照；链接按实际保存位置调整。

# 02 · 本步函数与对象记录

[本步入口](../README.md) · [scope 与阅读导航](../01-scope.md#reading-navigation) · [本步过程](../../../../04-flow.md)

本页只索引本步实际接触的函数与对象；当前阅读位置以[项目入口](../../../../../../../../README.md#current-reading)为准，调用主线见 scope。

下表按[建议回读顺序](../../../../../../../../references/reading-order-proposal.md)排列，序号不是当时的接触顺序，也不表示已完成或掌握。原始来源与认识记录保持。

| 回读序 | 源码文件 | 函数与记忆入口 | 首次接触 | 最近认识更新 |
| --- | --- | --- | --- | --- |
| 1 | examples/agent-sandbox-rl/examples/run_swebench_fleet.py | [main](functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/main.md) | Step 000，2026-11-04 | 开始脚本入口、回调构造与传入的阅读 |
| 2 | examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py | [run_naive](functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/run_naive.md) | Step 000，2026-11-04 | 本轮用户提出初步理解与疑问；校准尚待反馈 |
| 3 | examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py | [SandboxFleet 类卡](../../2026-11-04-SandboxFleet-before-reactivation.md) | Step 000，2026-11-04 | 按用户要求查看对象结构；字段与方法用法尚待反馈 |
| 4 | examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py | [SandboxFleet.__init__](../../2026-11-04-before-init-method-separation/SandboxFleet.__init__.md) | Step 000，2026-11-04 | 已明确进入初始化过程；机制理解尚待反馈 |
| 5 | examples/agent-sandbox-rl/agent_sandbox_rl/adapters/swebench.py | [SweBenchSource.load](../../../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/adapters/swebench.py/SweBenchSource.load.md) | Step 000，2026-11-04 | 开始数据读取条件及行到 Task 的映射；尚待反馈 |
| 6 | examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py | [SandboxFleet.setup](../../../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/fleet.py/SandboxFleet.setup.md) | Step 000，2026-11-04 | 用户已概括主要职责，内部机制仍保留未知 |
| 7 | examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py | [process_parallel](../../../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/strategies.py/process_parallel.md) | Step 000，2026-11-04 | 用户已归纳返回值不限定为奖励；继续核对 Future 与业务完成的区别 |
| 8 | examples/agent-sandbox-rl/examples/run_swebench_fleet.py | [_record.fn](../../../reserve/functions/examples/agent-sandbox-rl/examples/run_swebench_fleet.py/_record.fn.md) | Step 000，2026-11-04 | 用户已概括具体执行与返回标识；正在校准 output 类型和沙箱层边界 |
| 9 | examples/agent-sandbox-rl/agent_sandbox_rl/adapters/swebench.py | [swebench_probe](../../../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/adapters/swebench.py/swebench_probe.md) | Step 000，2026-11-04 | 用户选择 SWE-bench 路径；探针与结果包装尚待理解反馈 |
| 10 | examples/agent-sandbox-rl/agent_sandbox_rl/handles.py | [SandboxHandle.exec](../../../reserve/functions/examples/agent-sandbox-rl/agent_sandbox_rl/handles.py/SandboxHandle.exec.md) | Step 000，2026-11-04 | 本轮定位命令进入 Pod 与输出返回的路径；尚待复述 |

用户原话、明确未知和助手核对的源码说明分别保留。
