# Step 007 · Agent 执行后怎样取得 Proxy 轨迹

[项目进度](../../../../README.md) · [本步 scope](01-scope.md) · [前一步总结](../step-006-agent-execution/05-task-flow.md)

本步从 generate 的 after_agent 调用继续，主问题是：Agent 已经交回调用结果，Proxy 如何收尾会话，再把记录的轨迹交回 generate？范围停在 trajectory_payload 取得，Sample 转换与最终回收留给后续步骤。

## 阅读入口

1. [generate 的本步片段](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#after-agent)：先接回已有流程。
2. [阶段命令执行](02-short-term-memory/functions/dressage/paddock/blackbox/execute_hooks.py/execute_blackbox_cmds_for_stage.md)：从前序调取，只回顾 stage=after_agent。
3. [Proxy 收尾与轨迹构建](02-short-term-memory/functions/dressage/proxy/server.py/create_app.finalize_session.md)：回顾数据结构、分段、构建和发布。
4. [轨迹读取](02-short-term-memory/functions/dressage/proxy/server.py/create_app.trajectory_read.md)：按标识返回已有轨迹；存储内部只按接口理解。

## 记录入口

1. [01 scope](01-scope.md)：整体位置、局部顺序和停止点。
2. [02 短期记录](02-short-term-memory/overview.md)：本步实际用到的函数。
3. [03 前序累计](03-long-term-memory/overview.md)：按前一步 03 + 02 合并，保留 42 份函数/类记录。
4. [04 形成过程](04-flow.md)：本步实际问题和说明。

[05 任务链路总结](05-task-flow.md)收拢本步正常主线与保留边界。2026-11-08 首轮收束，不等于掌握全部内部实现；Step 008 尚未展开。实际阅读进度只在项目 README 维护。
