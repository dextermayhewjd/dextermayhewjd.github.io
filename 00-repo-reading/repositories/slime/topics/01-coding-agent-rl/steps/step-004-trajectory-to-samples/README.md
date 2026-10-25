# Step 4 · 会话轨迹与奖励怎样交成训练样本

**目录编号调整**：本目录由原 Step 003 顺延而来；历史过程、函数来源和固定样例里的原编号保留当时语境，见[新旧编号对照](../../../../step-numbering-2026-10-23.md)。本次不改写原源码版本或学习结论。

[前一步：独立评测与奖励](../step-003-swe-evaluation/README.md) · [当前阅读进度](../../../../../../../slime_photo/code-reading/repo-reading-route.md#当前接续)

**2026-10-24 新版 scope 校准**：当前从 [generate.py:326](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/examples/coding_agent_rl/generate.py#L326-L336) 进入 [BaseAdapter.finish_session:314–345](https://github.com/THUDM/slime/blob/18868a79b0b083a093798a94ed0f8cb4f71b9c14/slime/agent/adapters/common.py#L314-L345)。scope 的入口、整体骨架、输入衔接与局部导航已按 `18868a79` 核对，[旧版 scope](references/scope-at-2f231865.md)完整保留。三张主流程卡片及 task flow 已按 `18868a79` 对齐，本轮沿“收尾、取配置、导出、补文本、返回”走到样本列表；跨循环与内层组装细节留作后续，旧数值例子继续保留历史依据。[scope 核对](04-flow.md#scope-core-refresh-18868a79)、[shutdown_session 核对](04-flow.md#shutdown-session-version-refresh)分别保存范围，[此前入口核对](04-flow.md#step-four-reentry-18868a79)保留原讨论。

2026-10-21，用户确认接着阅读 `BaseAdapter.finish_session`，围绕“会话轨迹 + reward + base_sample → Sample 列表”建立函数记录。[范围确认](04-flow.md#scope-confirmed)

Step 1 已跟随 `_run_turn` 看过逐轮记录；Step 3 的评测链已接到 `generate` 取得奖励。现在沿 `evaluation=False` 路径进入样本导出：用同一个 `sid` 找到已有轨迹，把评测结果和任务基础字段交给 manager，再由 Adapter 补上样本文本。这承接[岗位对照中的训练数据交接](../../../../../../../slime_photo/code-reading/job-alignment.md#需求到阅读单元)，先建立数据合同，暂不展开训练器与损失计算。

## 从这里开始读

1. [scope：定位整体骨架的第 7 项](01-scope.md)，接清[三项输入](01-scope.md#input-bridge)，再沿[新版源码导航](01-scope.md#reading-path)阅读；各卡片的源码版本见其开头。
2. [BaseAdapter.finish_session](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.finish_session.md)：先看一组输入输出，再顺着“收尾与取配置 → 委托导出 → 补文本并返回”读代码。
3. [BaseAdapter.shutdown_session](02-short-term-memory/functions/slime/agent/adapters/common.py/BaseAdapter.shutdown_session.md)：本轮先按“导出前收尾”的职责使用，返回父卡的 `store.pop`；跨循环细节后续回访。
4. [TrajectoryManager.get_trajectory](02-short-term-memory/functions/slime/agent/trajectory.py/TrajectoryManager.get_trajectory.md)：从父卡的实际调用处进入，读消息路径怎样交给组装函数，结果怎样汇总、赋奖励并返回。

理解轨迹对象时，先回查 [TrajectoryManager 类卡](02-short-term-memory/classes/slime/agent/trajectory.py/TrajectoryManager.md)与 [MessageNode 类卡](02-short-term-memory/classes/slime/agent/trajectory.py/MessageNode.md#tree-example)，再返回 `get_trajectory` 的路径遍历。

首轮从 `finish_session` 建立入口卡片，随后按用户要求进入 `get_trajectory`；之后用户指出前置缺口，回补 `shutdown_session` 与父函数中的配置取出。上方导航按调用关系组织，实际讨论顺序保存在 flow。更内层的 `_chain_to_samples`、分叉和 mask 规则留在实际交接处作为后续问题；已有 `record_turn`、`decode` 从累计记忆回查。

## 本步材料与记忆继承

- [02 · 本步函数与类记录](02-short-term-memory/overview.md)：`finish_session`、`shutdown_session` 与 `get_trajectory` 各自的场景和局部交接；[BaseAdapter 类卡片](02-short-term-memory/classes/slime/agent/adapters/common.py/BaseAdapter.md)保存全字段浅层总览与已展开的用法关系。
- [03 · 前序函数记忆](03-long-term-memory/overview.md)：合并 Step 3 的 `03 + 02`，共 24 份；保留原话、来源、认识时间与未知。
- [04 · 问题与解释](04-flow.md)：范围确认、首轮观察与验证证据。
- [05 · 阅读后的任务总结](05-task-flow.md)：把前序轨迹与奖励接到会话收尾、样本导出和文本补全；明确尚未展开的算法与外层清理边界。

scope、三张主流程卡片与 task flow 已对齐 `18868a79`；旧版卡片、总结和导出样例的历史证据继续保留，具体边界见[文末版本说明](01-scope.md#版本说明)。首个例子用构造的单轮记录和本地 tokenizer 核对导出结果；没有调用模型、运行沙箱或训练。阅读后的整体反馈与本次总结依据见 [04-flow](04-flow.md#sample-export-flow-closure)，当前理解状态与下一处入口仍只由唯一路线维护。
