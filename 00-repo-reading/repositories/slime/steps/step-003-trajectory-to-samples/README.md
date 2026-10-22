# Step 3 · 会话轨迹与奖励怎样交成训练样本

[前一步：独立评测与奖励](../step-002-swe-evaluation/README.md) · [当前阅读进度](../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

2026-10-21，用户确认接着阅读 `BaseAdapter.finish_session`，围绕“会话轨迹 + reward + base_sample → Sample 列表”建立函数记录。[范围确认](04-flow.md#scope-confirmed)

Step 1 已跟随 `_run_turn` 看过逐轮记录；Step 2 的评测链已接到 `generate` 取得奖励。现在沿 `evaluation=False` 路径进入样本导出：用同一个 `sid` 找到已有轨迹，把评测结果和任务基础字段交给 manager，再由 Adapter 补上样本文本。这承接[岗位对照中的训练数据交接](../../../../../slime_photo/code-reading/job-alignment.md#需求到阅读单元)，先建立数据合同，暂不展开训练器与损失计算。

## 从这里开始读

1. [scope：定位整体骨架的第 7 项](01-scope.md)。
2. [BaseAdapter.finish_session](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md)：先看一组输入输出，再顺着“收尾与取配置 → 委托导出 → 补文本并返回”读代码。
3. [BaseAdapter.shutdown_session](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md)：在导出前关闭会话入口，等待并处理未结束的请求；读完返回父卡的 `store.pop`。
4. [TrajectoryManager.get_trajectory](02-short-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.get_trajectory.md)：从父卡的实际调用处进入，读消息路径怎样交给组装函数，结果怎样汇总、赋奖励并返回。

首轮从 `finish_session` 建立入口卡片，随后按用户要求进入 `get_trajectory`；之后用户指出前置缺口，回补 `shutdown_session` 与父函数中的配置取出。上方导航按调用关系组织，实际讨论顺序保存在 flow。更内层的 `_chain_to_samples`、分叉和 mask 规则留在实际交接处作为后续问题；已有 `record_turn`、`decode` 从累计记忆回查。

## 本步材料与记忆继承

- [02 · 本步函数记录](02-short-term-memory/overview.md)：`finish_session`、`shutdown_session` 与 `get_trajectory` 各自的场景、输入输出和局部交接。
- [03 · 前序函数记忆](03-long-term-memory/overview.md)：合并 Step 2 的 `03 + 02`，共 24 份；保留原话、来源、认识时间与未知。
- [04 · 问题与解释](04-flow.md)：范围确认、首轮观察与验证证据。
- [05 · 阅读后的任务总结](05-task-flow.md)：把前序轨迹与奖励接到会话收尾、样本导出和文本补全；明确尚未展开的算法与外层清理边界。

源码继续绑定 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。首个例子用构造的单轮记录和本地 tokenizer 核对导出结果；没有调用模型、运行沙箱或训练。阅读后的整体反馈与本次总结依据见 [04-flow](04-flow.md#sample-export-flow-closure)，当前理解状态与下一处入口仍只由唯一路线维护。
