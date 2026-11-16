# Step 013 · 本步函数记录

| 函数 | 本轮范围 |
| --- | --- |
| [Trial.__init__（调取）](functions/harbor/trial/trial.py/Trial.__init__.md) | 从前序完整记录调取，保留 config/task 理解与创建现场；本步由环境初始化调用进入 |
| [Trial._init_agent_environment](functions/harbor/trial/trial.py/Trial._init_agent_environment.md) | 用户已复述按配置创建的主线；当前校准三类输入、题目资源要求与对象输出，下一处已进入启动包装，实际 start 内部未展开 |
| [Trial._prepare（调取）](functions/harbor/trial/trial.py/Trial._prepare.md) | 沿用 Step 011 准备主干，当前从技能上传返回，下一处建议 _setup_agent（Step 014） |
| [Trial._setup_agent_environment](functions/harbor/trial/trial.py/Trial._setup_agent_environment.md) | 用户已复述准备阶段的启动委派，当前追问实际 start 时机；现已接到 _start_agent_environment 子卡 |
| [Trial._start_agent_environment](functions/harbor/trial/trial.py/Trial._start_agent_environment.md) | 已讨论 start 调用、传参与超时；用户概括沙箱构建用途，后续按 K8s 目标核对接口和适配，Docker start 不列为必读 |
| [BaseEnvironment.start](functions/harbor/environments/base.py/BaseEnvironment.start.md) | 用户已认清这是接口而无具体启动实现；具体 K8s 实现尚未定位 |
| [BaseEnvironment.run_healthcheck](functions/harbor/environments/base.py/BaseEnvironment.run_healthcheck.md) | 用户已理解 HTTP 示例用于就绪检查；循环细节按需回查；与 Trial._prepare 双向链接 |
| [Trial._upload_injected_skills](functions/harbor/trial/trial.py/Trial._upload_injected_skills.md) | 用户已概括把 skills 放到对应目录；后端传输与 Agent 使用机制仍未展开 |
| [BaseEnvironment.exec](functions/harbor/environments/base.py/BaseEnvironment.exec.md) | 2026-11-13 按确认范围建卡；包含 ExecResult 和健康检查消费场景，尚待逐项讨论 |
| [BaseEnvironment.upload_file](functions/harbor/environments/base.py/BaseEnvironment.upload_file.md) | 按确认范围建卡：本地单文件 → 环境；借 Agent 配置上传认接口，待讨论 |
| [BaseEnvironment.upload_dir](functions/harbor/environments/base.py/BaseEnvironment.upload_dir.md) | 按确认范围建卡：本地目录 → 环境；接 _prepare 的 skills 上传，待讨论 |
| [BaseEnvironment.download_file](functions/harbor/environments/base.py/BaseEnvironment.download_file.md) | 按确认范围建卡：环境单文件 → 本地；借真实辅助调用认接口，待讨论 |
| [BaseEnvironment.download_dir](functions/harbor/environments/base.py/BaseEnvironment.download_dir.md) | 按确认范围建卡：环境目录 → 本地；接执行后的日志收集，待讨论 |
| [BaseEnvironment.stop](functions/harbor/environments/base.py/BaseEnvironment.stop.md) | 按确认范围建卡：停止与可选删除；接 Trial 收尾，待讨论 |

[前序累计：86 份函数/类记录](../03-long-term-memory/overview.md)。当前未读的具体后端 start、工厂内部与适配器只保留 scope/源码定位，不提前建卡。
