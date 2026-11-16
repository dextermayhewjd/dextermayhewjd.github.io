# Step 014 · 本步函数记录

| 函数 | 当前记录 |
| --- | --- |
| [Trial._prepare（调取）](functions/harbor/trial/trial.py/Trial._prepare.md) | 保留 Step 013 的调用背景；从默认用户上下文进入 _setup_agent |
| [Trial._setup_agent](functions/harbor/trial/trial.py/Trial._setup_agent.md) | 用户已确认委派 Agent.setup；继续进入继承的实现 |
| [BaseInstalledAgent.setup](functions/harbor/agents/installed/base.py/BaseInstalledAgent.setup.md) | 用户已概括基本安装准备；具体 install 内部暂缓 |
| [Trial.run（调取）](functions/harbor/trial/trial.py/Trial.run.md) | 只回看 _prepare 返回后进入 _run 的交接 |
| [SingleStepTrial._run（调取）](functions/harbor/trial/single_step.py/SingleStepTrial._run.md) | 只接到第一项 _run_agent，保留已有完整记录 |
| [SingleStepTrial._run_agent](functions/harbor/trial/single_step.py/SingleStepTrial._run_agent.md) | 用户反馈已大致理解，继续共用执行过程 |
| [Trial._run_agent_phase](functions/harbor/trial/trial.py/Trial._run_agent_phase.md) | 当前回看 run 完成后的 AGENT_END 与返回；不重读整个执行阶段 |
| [ClaudeCode.run](functions/harbor/agents/installed/claude_code.py/ClaudeCode.run.md) | 用户已概括 CLI 执行包装、输出格式与位置；后端执行和日志解析未展开 |
| [_inject_agent_routing](functions/dressage/integrations/harbor/plugin.py/_inject_agent_routing.md) | 用户已概括地址改写；具体 URL、token 引用的区别已校准 |
| [DressageHarborPlugin.on_job_start](functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin.on_job_start.md) | 用户已概括配置与回调登记；当前接到 Trial START 的回调 |
| [DressageHarborPlugin._on_start](functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_start.md) | 已接到路由登记调用，进入 GatewayLease.register |
| [GatewayLease.register](functions/dressage/integrations/harbor/gateway.py/GatewayLease.register.md) | 已展示租约检查与委派，继续 call 的执行位置与返回 |
| [GatewayRuntime.call](functions/dressage/integrations/harbor/gateway.py/GatewayRuntime.call.md) | 调度机制保留回查；当前先返回实际路由登记业务 |
| [GatewayRuntime._register](functions/dressage/integrations/harbor/gateway.py/GatewayRuntime._register.md) | 已有登记背景：创建 Proxy、保存路由绑定并返回 handle |
| [DressageHarborPlugin._on_agent_start](functions/dressage/integrations/harbor/plugin.py/DressageHarborPlugin._on_agent_start.md) | 第三部分当前函数：确定 turn_id、调用已有 handle 打开本轮交互 |
| [AttemptHandle.open_turn](functions/dressage/integrations/harbor/gateway.py/AttemptHandle.open_turn.md) | 用户已概括本轮交互的用途；operation 调度仍有疑问，暂留回访 |
| [_GatewayASGI._handle_http](functions/dressage/integrations/harbor/gateway.py/_GatewayASGI._handle_http.md) | HTTP 主干已讨论；响应空闲超时与服务保护先认职责 |

[此前累计 98 份记录](../03-long-term-memory/overview.md)。具体 install、环境执行与模型请求内部尚未在本步展开，不提前建卡。

2026-11-14 范围已收窄，剩余主读入口见 [scope 3.2](../01-scope.md#reading-sequence)；未开始阅读的函数不在这里预建记录。既有调度与登记卡保留供回查。
