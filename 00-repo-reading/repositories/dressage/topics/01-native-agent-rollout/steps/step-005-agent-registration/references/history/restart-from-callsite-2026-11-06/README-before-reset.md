# Step 005 · Agent 注册与执行前准备

> 编号调整：本目录由 Step 002 顺延为 Step 005。正文中的早期编号、原话及记忆快照保留历史语境；现行顺序见[编号与范围对照](../../../../../../../step-numbering-2026-11-05.md)。

[项目目标与当前接续](../../../../../../../README.md) · [前一步：环境准备](../../../../step-004-paddock-environment-preparation/05-task-flow.md)

前一步已经取得环境并交回 state。本步对应 generate 的“注册准备”段，从 Paddock.register_agent 看任务身份、Agent 配置和代理地址如何交给 BlackboxServer，再定位前置命令及 Proxy 会话登记，停止在 call_agent 之前。

## 从这里开始

1. [scope 3.1](../../../01-scope.md#whole-flow)：在 generate 上层流程中定位本步。
2. [scope 3.2](../../../01-scope.md#reading-navigation)：下一处主读 BlackboxServer.register 的首次成功注册路径，在 adapter.initialize 处进入 Claude Code 具体初始化；Paddock/客户端作为已有来路回查。
3. 遇到输入问题，可回查本步已调入的 [SandboxState](02-short-term-memory/classes/dressage/paddock/blackbox/common/state.py/SandboxState.md) 和 [generate](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md)。当前已展开注册函数并建立独立卡；本次调取最新 State/Lease 字段说明。

| 材料 | 职责 |
| --- | --- |
| [01 · scope](../../../01-scope.md) | 上层位置、本步顺序、源码入口和停止点 |
| [02 · 本步记录](02-short-term-memory/overview.md) | 当前包含注册函数卡、上层流程及 State/Lease 输入记录 |
| [03 · 前序记录](../../../03-long-term-memory/overview.md) | 接续已读 Step 001–004 的完整记录，来源和未知保留；原准备快照已归档 |
| [04 · 实际过程](../../../04-flow.md) | 开步依据及之后的真实阅读反馈 |

本步尚未形成新的个人机制复述或真实运行证据。原来 local_bwrap 的完整实现仍在前一步 references 中，仅按需引用；不重新列为当前必读。唯一实时进度仍由项目 README 维护。
