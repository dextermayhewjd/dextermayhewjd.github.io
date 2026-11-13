# 04 · 实际阅读过程

<a id="update-status-first-card"></a>

## 2026-11-05 · 确认进入状态写回

前一步已收束状态汇总与 Ready 普通路径。用户在讨论下一步建议后确认：

> 好的那么就按照这样子看一下这里的这个update sandbox吧

沿用前一轮明确的入口 SandboxReconciler.updateStatus，没有另造名为 update sandbox 的函数。选旧 Ready=False、本轮新 Ready=True 的同一 Sandbox，先看正常持久化，再看版本冲突的代表性分支。

本轮建立 scope 与函数卡，代码默认展开，详细解释折叠。重点是 oldStatus/oldResourceVersion 组成旧依据，而 sandbox 保持待写的新状态；Patch 才向 API 发起写入。冲突时放弃这份过期补丁，依赖后续资源事件重新协调，不能把所有 nil 返回解释成已写入。

按本主题规则合并继承前一步 03 + 02，共五张卡；当前从 03 调取直接调用方 Reconcile。旧卡、原话、未知和版本保留。尚无用户对本函数内部机制的独立表述，没有真实 API 写入或集群实验。

## 2026-11-05 · 调整当前 Reconcile 卡的展示

按用户要求展开当前 Reconcile 卡里的代码，并突出 3.1–3.4 阶段标题。正文与代码保留，只调整展示；原话、具体改动与边界见[格式记录](../../../../../../../backlog/repo-reading/2026-10-20-task-driven-cognitive-architecture/discussion.md#step003-reconcile-code-visible)。当前仍阅读 updateStatus，没有因排版调整推进学习状态。
