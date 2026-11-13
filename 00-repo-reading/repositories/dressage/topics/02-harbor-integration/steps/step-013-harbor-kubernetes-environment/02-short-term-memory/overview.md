# Step 013 · 本步函数记录

| 函数 | 本轮范围 |
| --- | --- |
| [Trial.__init__（调取）](functions/harbor/trial/trial.py/Trial.__init__.md) | 从前序完整记录调取，保留 config/task 理解与创建现场；本步由环境初始化调用进入 |
| [Trial._init_agent_environment](functions/harbor/trial/trial.py/Trial._init_agent_environment.md) | 用户已复述按配置创建的主线；当前校准三类输入、题目资源要求与对象输出，下一处已进入启动包装，实际 start 内部未展开 |
| [Trial._prepare（调取）](functions/harbor/trial/trial.py/Trial._prepare.md) | 沿用 Step 011 准备主干，当前从 await _setup_agent_environment 进入 |
| [Trial._setup_agent_environment](functions/harbor/trial/trial.py/Trial._setup_agent_environment.md) | 用户已复述准备阶段的启动委派，当前追问实际 start 时机；现已接到 _start_agent_environment 子卡 |

| [Trial._start_agent_environment](functions/harbor/trial/trial.py/Trial._start_agent_environment.md) | 已讨论 start 调用、传参与超时；用户概括沙箱构建用途，后续按 K8s 目标核对接口和适配，Docker start 不列为必读 |

| [BaseEnvironment.start](functions/harbor/environments/base.py/BaseEnvironment.start.md) | 用户已认清这是接口而无具体启动实现；具体 K8s 实现尚未定位 |

[前序累计：86 份函数/类记录](../03-long-term-memory/overview.md)。当前未读的具体后端 start、工厂内部与适配器只保留 scope/源码定位，不提前建卡。
