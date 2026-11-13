# Step 013 · 创建并启动 Environment，对齐 Agent Sandbox 能力

[项目唯一进度](../../../../README.md) · [scope](01-scope.md) · [前一步总结](../step-012-task-agent-verifier/05-task-flow.md)

2026-11-13，用户确认开始本步。接住 Step 012 的 config、Task 与 Agent 对象，从 Trial.__init__ 的 _init_agent_environment 进入，先看环境对象怎样创建，再接后面的 start；本步整体范围继续包括环境合同与 Agent Sandbox 对齐，当前已讨论创建入口，已沿启动包装进入 _start_agent_environment；调用与超时已讨论，当前从 BaseEnvironment.start 核对后端接口，具体 K8s 实现待定位。

- [已讨论：Trial._init_agent_environment](02-short-term-memory/functions/harbor/trial/trial.py/Trial._init_agent_environment.md)
- [上层计时包装：Trial._setup_agent_environment](02-short-term-memory/functions/harbor/trial/trial.py/Trial._setup_agent_environment.md)
- [启动调用：Trial._start_agent_environment](02-short-term-memory/functions/harbor/trial/trial.py/Trial._start_agent_environment.md)
- [当前接口：BaseEnvironment.start](02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.start.md)
- [准备阶段：Trial._prepare（本步调取）](02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md)
- [创建调用方：Trial.__init__（本步调取）](02-short-term-memory/functions/harbor/trial/trial.py/Trial.__init__.md)
- [阅读骨架与入口](01-scope.md)
- [本步函数索引](02-short-term-memory/overview.md)
- [前序累计：86 份函数/类记录](03-long-term-memory/overview.md)
- [本次开始与形成过程](04-flow.md)

当前先沿 hello-world / Docker 的静态例子理解共用创建入口。K8s/Agent Sandbox 的选择与接口对照按 scope 后续展开，不把例子视为后端适配已完成。当前没有实际启动环境或执行安装、模型及集群验证，也未生成本步完成总结。
