# Step 013 · 创建并启动 Environment，对齐 Agent Sandbox 能力

[项目唯一进度](../../../../README.md) · [scope](01-scope.md) · [前一步总结](../step-012-task-agent-verifier/05-task-flow.md)

2026-11-13，用户确认开始本步。环境对象创建、启动包装和 BaseEnvironment.start 的接口已讨论。按最新边界，本轮继续认清 exec、文件传输和 stop 合同，不下钻具体后端；这六个方法已按用户要求建卡，待逐项讨论。_prepare 的其他环境消费动作只带用途，Agent.setup 留到 Step 014。首轮接口阅读仍未结束，Agent Sandbox 实现与运行验证另列待办。

- [已讨论：Trial._init_agent_environment](02-short-term-memory/functions/harbor/trial/trial.py/Trial._init_agent_environment.md)
- [上层计时包装：Trial._setup_agent_environment](02-short-term-memory/functions/harbor/trial/trial.py/Trial._setup_agent_environment.md)
- [启动调用：Trial._start_agent_environment](02-short-term-memory/functions/harbor/trial/trial.py/Trial._start_agent_environment.md)
- [已读接口：BaseEnvironment.start](02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.start.md)
- 当前回到 [Trial._prepare 的技能上传返回处](02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md#prepare-agent-call)；下一处建议为 Step 014 的 _setup_agent，本步其余接口与验证仍待回查。
- 文件传输接口：[upload_file](02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.upload_file.md) · [upload_dir](02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.upload_dir.md) · [download_file](02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.download_file.md) · [download_dir](02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.download_dir.md)
- [停止接口：BaseEnvironment.stop](02-short-term-memory/functions/harbor/environments/base.py/BaseEnvironment.stop.md)
- [准备阶段：Trial._prepare（本步调取）](02-short-term-memory/functions/harbor/trial/trial.py/Trial._prepare.md)
- [创建调用方：Trial.__init__（本步调取）](02-short-term-memory/functions/harbor/trial/trial.py/Trial.__init__.md)
- [阅读骨架与入口](01-scope.md)
- [本步函数索引](02-short-term-memory/overview.md)
- [前序累计：86 份函数/类记录](03-long-term-memory/overview.md)
- [本次开始与形成过程](04-flow.md)

前面的 hello-world / Docker 只用于理解共用参数。当前接口阅读不要求先看 Docker、ACK 或 GKE 的具体启动；实际 Agent Sandbox 适配缺口仍保留。当前没有实际启动环境或执行安装、模型及集群验证，也未生成本步完成总结。

2026-11-13 后续接续：用户已确认进入 [Step 014](../step-014-model-routing-and-api-contract/01-scope.md#current-reading)，从同一 _prepare 中的 _setup_agent 开始。本步尚未读完的接口和实际验证继续保留。
