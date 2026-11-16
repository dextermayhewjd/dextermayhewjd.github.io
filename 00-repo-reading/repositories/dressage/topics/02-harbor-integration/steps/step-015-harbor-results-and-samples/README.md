# Step 015 · Agent 结束后的日志、产物与评测

[项目唯一进度](../../../../README.md) · [scope](01-scope.md) · [本步函数](02-short-term-memory/overview.md) · [前序累计](03-long-term-memory/overview.md) · [理解过程](04-flow.md)

2026-11-16 用户确认开始本步，首先追问上传日志与此前 Proxy 采集有何不同。当前进入 [Trial._upload_agent_logs](02-short-term-memory/functions/harbor/trial/trial.py/Trial._upload_agent_logs.md)，接清日志内容、产生位置和传输方向；后续再到 _collect_artifacts、_run_verifier。当前没有展开后两者或预建卡片。

前一步已经补清 Agent 执行期间的模型请求链；[Step 006 公共 Proxy 补读](../../../01-native-agent-rollout/steps/step-006-agent-execution/01-scope.md#model-request-route)保留原记录。本步关心执行结束后如何交付结果，不重读模型请求。日志、产物、评分与最终 bundle 尚需逐段建立关系；真实运行和跨版本兼容未验证。
