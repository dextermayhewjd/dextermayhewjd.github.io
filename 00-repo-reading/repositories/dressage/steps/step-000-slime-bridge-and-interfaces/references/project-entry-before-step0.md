# 项目入口历史快照

保存于 2026-10-23。以下为本轮重写前的项目入口原文，仅保存此前路线表述；其中步骤链接在保存时已失效，不作为当前进度。当前入口见 [Dressage README](../../../README.md)。

---

# Dressage：按目标逐步建立整体模型

[通用方法](../../README.md) · [工作流](../../workflow.md) · [认知心理学阅读心法](cognitive-reading-guide.md) · [腾讯混元岗位对照：Slime vs Dressage 区别与必读模块清单](job-and-repo-comparison.md)

用户的阅读目标是优先对齐腾讯混元 Agent 强化学习框架工程师岗位（`postId=2061654749727600640`），理清 **Slime 与 Dressage 两个仓库的本质区别**，并明确**面向该岗位到底应该重点读哪些模块（P0 必看 6 模块 / P1 选读 3 模块 / P2 暂缓模块）**。详见独立文档：[腾讯混元 Agent 强化学习框架工程师：Slime vs Dressage 仓库区别与核心必读模块指南](job-and-repo-comparison.md)。

本轮按既定标准与官方文档主线推进：
- **Step 0** 对齐官方文档 [`docs/rollout.md:86–94`](file:///Users/dextermayhew/projects/Dressage/docs/rollout.md#L86-L94)，确立单条黑盒 Rollout 指挥官函数 `generate` 的 7 步核心骨架，两层 memory 不收录函数卡片；
- **Step 1** 继承 Step 0 的 7 步核心骨架，从其中的第 1–4、7 项（`paddock.*`）下钻到 [`BlackboxAgentPaddock`](file:///Users/dextermayhew/projects/Dressage/dressage/paddock/blackbox/paddock.py#L32-L319)（及底层 [`Paddock`](file:///Users/dextermayhew/projects/Dressage/dressage/paddock/interface.py) / [`SandboxProvider`](file:///Users/dextermayhew/projects/Dressage/dressage/sandbox/provider.py) 契约），看清它如何一端借还沙箱、一端通过 HTTP 调度沙箱内 `BlackboxServer`。

## 源码与唯一记录入口

- 已确认的本地源码：[`/Users/dextermayhew/projects/Dressage`](file:///Users/dextermayhew/projects/Dressage)；分支 `main`，固定提交 `3e3142fe8ea07e4504c3b20a936a4c201a3de44c`（工作区干净）。
- 当前进度与接续位置：本页步骤索引及 [Step 1 · 01-scope.md](steps/step-001-contracts-and-executors/01-scope.md)。

## 步骤索引

| 步骤 | 本步核心问题 | 记录 |
| --- | --- | --- |
| 001 · 当前 | `generate` 中的五项 `paddock.*` 调用怎样通过 `BlackboxAgentPaddock` 连接 `SandboxProvider`（借还沙箱）与 `BlackboxServer`（调度 Agent）？ | [步骤入口](steps/step-001-contracts-and-executors/README.md) |
| 000 · 前序 | Dressage 黑盒 Agent Rollout 的指挥官函数 `generate` 与官方 7 步核心骨架是什么？ | [步骤入口](steps/step-000-slime-bridge-and-interfaces/README.md) |

Step 0 的三项 scope 见[整体阅读范围](steps/step-000-slime-bridge-and-interfaces/01-scope.md)，两层 memory 暂无函数卡片。

Step 1 的[当前阅读范围](steps/step-001-contracts-and-executors/01-scope.md)原样继承 Step 0 的 7 步核心骨架，展开 `BlackboxAgentPaddock` 的四段阅读导航；[`02-short-term-memory/`](steps/step-001-contracts-and-executors/02-short-term-memory/overview.md) 主读 [`BlackboxAgentPaddock`](steps/step-001-contracts-and-executors/02-short-term-memory/classes/dressage/paddock/blackbox/paddock.py/BlackboxAgentPaddock.md) 并保留 [`Paddock` 契约](steps/step-001-contracts-and-executors/02-short-term-memory/classes/dressage/paddock/interface.py/Paddock.md)与 [`SandboxProvider` 协议](steps/step-001-contracts-and-executors/02-short-term-memory/classes/dressage/sandbox/provider.py/SandboxProvider.md)回查；[`03-long-term-memory/`](steps/step-001-contracts-and-executors/03-long-term-memory/overview.md) 暂无前序函数可继承。
