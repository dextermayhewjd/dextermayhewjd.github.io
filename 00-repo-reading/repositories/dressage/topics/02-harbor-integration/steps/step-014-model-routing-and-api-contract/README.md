# Step 014 · 准备并运行 Agent，接清运行中的模型请求

[项目唯一进度](../../../../README.md) · [本步 scope](01-scope.md) · [前一步范围与遗留项](../step-013-harbor-kubernetes-environment/01-scope.md)

2026-11-14，按用户确认收窄深入范围：Harbor 执行与 Dressage 配置/登记主干已有记录，第三部分 _on_agent_start 已建卡；用户追问 3.5.1 后，open_turn 的用途已讨论，operation 调度仍可回访；HTTP 分派主干已讨论；当前回到 _run_agent_phase 的结束段，接清回调与输出同步的返回位置。公共 Proxy 已于 2026-11-16 在 Step 006 补读正常请求与生成交接，并按用户要求收束；StepRecord 写入和响应转换内部不继续下钻。当前只需回顾 Agent 整体结束、AGENT_END 与输出同步的交接，然后考虑 Step 015 的产物与评测，不能把运行中采集等同于最终结果已汇总。

- [当前收束：Trial._run_agent_phase 结束段](02-short-term-memory/functions/harbor/trial/trial.py/Trial._run_agent_phase.md#run-agent-phase-finish)
- [已讨论的 HTTP 主干：_GatewayASGI._handle_http](02-short-term-memory/functions/dressage/integrations/harbor/gateway.py/_GatewayASGI._handle_http.md#gateway-http-route)
- [前一处短回查：AttemptHandle.open_turn](02-short-term-memory/functions/dressage/integrations/harbor/gateway.py/AttemptHandle.open_turn.md#open-turn-mainline)
- [主卡：DressageHarborPlugin._on_agent_start](02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_agent_start.md#agent-start-mainline)，阅读位置见 [scope 第三部分](01-scope.md#reading-part-3)。
- [登记背景：GatewayRuntime._register](02-short-term-memory/functions/dressage/integrations/harbor/gateway.py/GatewayRuntime._register.md#runtime-register-mainline)
- [调度机制回查：GatewayRuntime.call](02-short-term-memory/functions/dressage/integrations/harbor/gateway.py/GatewayRuntime.call.md#runtime-call-mainline)
- [调用方：GatewayLease.register](02-short-term-memory/functions/dressage/integrations/harbor/gateway.py/GatewayLease.register.md#lease-register-mainline)
- [调用方：_on_start](02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_start.md#trial-start-mainline)
- [登记来源：on_job_start](02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin.on_job_start.md#job-start-hooks)
- [子调用：_inject_agent_routing](02-short-term-memory/functions/dressage/integrations/harbor/plugin.py/_inject_agent_routing.md#inject-routing-mainline)
- [后续接回的执行入口：ClaudeCode.run](02-short-term-memory/functions/harbor/agents/installed/claude_code.py/ClaudeCode.run.md#claude-run-mainline)
- [调用方：Trial._run_agent_phase](02-short-term-memory/functions/harbor/trial/trial.py/Trial._run_agent_phase.md#run-agent-phase-mainline)
- [调用方：SingleStepTrial._run_agent](02-short-term-memory/functions/harbor/trial/single_step.py/SingleStepTrial._run_agent.md#run-agent-mainline)
- [已讨论：BaseInstalledAgent.setup](02-short-term-memory/functions/harbor/agents/installed/base.py/BaseInstalledAgent.setup.md#installed-agent-setup-mainline)
- [上层委派：Trial._setup_agent](02-short-term-memory/functions/harbor/trial/trial.py/Trial._setup_agent.md#setup-agent-mainline)
- [调用方：Trial._prepare](02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md#prepare-agent-call)
- [本步函数索引](02-short-term-memory/overview.md)
- [前序累计 98 份记录](03-long-term-memory/overview.md)
- [形成过程](04-flow.md)

Step 013 的未读接口和实际适配验证继续保留；这里按环境接口可用的假设阅读，不代表先前阶段全部完成或已经运行成功。
