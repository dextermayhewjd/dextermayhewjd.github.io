# Step 000 · 先看 K8sReconciler 的整体骨架

[项目与当前进度](../../README.md#current-reading) · [Kubernetes 基础](../../../kubernetes/README.md) · [范围与源码导航](01-scope.md) · [函数记录](02-short-term-memory/overview.md) · [讨论过程](04-flow.md)

> 先在本地 README 中试读和修改。这里是本步正文，暂不建立 Hugo 网页。

> **后续接续**：事件观察已按用户要求独立为 [Step 001 · 接收 Kubernetes Job 事件](../step-001-watch-job-events/README.md)。本步保留此前的函数卡、首次接触与问答；新步骤完整继承后继续阅读，实时位置仍以项目入口为准。

## 1. 先把阅读层次摆正

这一轮先看整个 Reconciler 怎样工作，再按编号进入局部。用户已认可 scope 3.1、3.2 的整体呈现，本轮补上 **[1]–[5] 的阅读顺序和步骤／函数记录映射**。此前只给 `run()` 的两个调用就进入局部问题的[原稿](references/history/2026-11-03-readme-before-overview.md)保留回查，相关问答不作为已完成的学习记录。

对照 Slime 的 scope，沿用的是以下顺序：

| 参考 | 它先给出什么 | 再怎样进入局部 |
| --- | --- | --- |
| [Step 001](../../../slime/topics/01-coding-agent-rl/steps/step-001-harness-to-adapter/01-scope.md) | 整个 Coding Agent 的七项骨架 | 定位 CLI 运行中的一次模型请求，再进入 `_run_turn` |
| [Step 012](../../../slime/topics/02-rollout-reward/steps/step-012-async-rollout-worker-loop/01-scope.md) | 后台生产与上层消费的位置，以及完整循环 | 再选择补充任务、回收、状态发布等局部 |
| [Step 017](../../../slime/topics/04-training-data-updates/steps/step-017-generation-training-loop/01-scope.md) | 一轮生成、训练、完成通知与权重交接 | 再标出要看的接口与返回位置 |

## 2. Reconciler 整体在做什么

它连接两边：**Gateway 中的 rollout 任务及状态**，以及 **Kubernetes 中实际运行任务的 Job**。先记住“查两边 → 做对应 → 创建或更新状态”这条主线。

下面是简明总览；完整调用、分支与源码位置统一放在 [scope 第 3 部分](01-scope.md#core-skeleton)。

```text
K8sReconciler.run()
|-- [A] _periodic_reconcile_loop()
|   `-- [1] _reconcile_once()
|       |-- _query_rollouts(...) + Job.async_list(...)
|       |-- match rollout <-> Job
|       |-- [2] _create_job(...) -> [3] build_job_spec(...) -> job.async_create()
|       `-- [5] _patch_status(...) when a state update is needed
`-- [B] [4] _watch_jobs_loop()
    `-- Job event -> _handle_job_event(...) -> [5] _patch_status(...)
```

- **A 周期协调**：读取任务和 Job，逐条匹配。排队任务没有 Job 时创建；已有 Job 时检查状态；已运行任务的 Job 消失时记录失败。
- **B 事件观察**：持续接收 Job 的变化，用关联标记找到 rollout，并回写完成或失败状态。
- **共同出口**：两条路径都可能通过 `_patch_status` 更新 Gateway。Job 真正运行 Agent，由 Kubernetes 承接。

A 与 B 并发运行；[1]–[5] 表示我们的阅读顺序。`build_job_spec` 是同模块的独立函数；它构造 Job 配置，实际提交发生在 `_create_job`。[5] 是两条路径共用的函数，只对应一份函数记录。

<a id="first-observation"></a>

## 3. 从 [1] 开始，沿实际问题返回骨架

**最初入口：[1] `_reconcile_once`。** 用户澄清函数名输入有误后明确选择它，从[短期函数卡的“两份数据来源”](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#two-data-sources)进入，再逐步阅读匹配。外层 `_periodic_reconcile_loop` 按调用背景理解，[2]–[5] 保持原编号；实时位置由[项目入口](../../README.md#current-reading)维护。

函数卡现保留[完整连续骨架](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#parent-skeleton)，顶部提供调用链面包屑。需要了解其中某个调用时，从[下钻与返回表](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#call-query-rollouts)打开一个函数，读完带着返回项回到原调用点。已读函数链接卡片，尚未接触的调用只链接源码；对应样例见 [reference 核对](04-flow.md#breadcrumb-reference-confirmation)。

本轮具体代码和观察问题保存在函数卡，scope 只维护[编号导航](01-scope.md#read-1)。此前入口讨论与本次纠正分别保留在 [历史核对](04-flow.md#reading-order-audit)和[明确选择](04-flow.md#reconcile-once-start)中。

从 [Job.async_list 查询](02-short-term-memory/functions/kr8s/_objects.py/APIObject.async_list.md)返回后，父函数的 [jobs_by_name 名称索引](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#index-jobs-by-name)把取得的 Job 列表整理为按名称查找的字典。

此前已沿缺失 Job 分支查看 [_create_job](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._create_job.md) 的创建职责，以及运行中任务找不到 Job 时通过 [_patch_status](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._patch_status.md) 登记失败的用途。已有 Job 的后半段接续见[父卡的三个阅读段](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#existing-job-reading-map)；实时位置以[项目入口](../../README.md#current-reading)为准。

用户随后选择 [4] [_watch_jobs_loop](02-short-term-memory/functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._watch_jobs_loop.md)，从整体骨架的 B 路径进入事件接收。本轮到交出 Job 数据给 `_handle_job_event` 为止，后者尚未建立卡片。

| 阅读编号 | 代码与问题 | 步骤归属 |
| --- | --- | --- |
| [1](01-scope.md#read-1) | `_reconcile_once`：读取两边、匹配任务与 Job、选择动作 | 当前 Step 000，已开始从数据来源读起 |
| [2](01-scope.md#read-2) | `_create_job`：提交一份 Job | 拟 Step 001 |
| [3](01-scope.md#read-3) | `build_job_spec`：任务和模板成为 manifest，读完回 [2] | 同一拟 Step 001 |
| [4](01-scope.md#read-4) | `_watch_jobs_loop` → `_handle_job_event`：观察和识别状态 | Step 000 已进入 watch；处理函数尚未独立展开 |
| [5](01-scope.md#read-5) | `_patch_status`：写回 Gateway，读完回调用方 | 同一拟 Step 002，A/B 共用 |

图、表与 [scope 的记录落点](01-scope.md#memory-map)使用同一组编号。scope 保留整体骨架与导航；当前实际接触的函数见 [短期函数索引](02-short-term-memory/overview.md)。Step 001、002 仍是后续精读建议，尚未开始；未读函数的提前卡片已按用户要求撤下。

用户反馈与安排依据见 [编号与记录映射](04-flow.md#numbered-reading-map)及 [函数说明迁移](04-flow.md#function-notes-out-of-scope)。

<details>
<summary>本步来源与记录边界</summary>

- 固定源码：`0029dbb35c467799d35fee81d15d80264b0d1bd3`，2026-11-03 静态核对。
- 调用方：[`_run_controller` 的对象创建](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/__main__.py#L28)与 [等待 run](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/__main__.py#L43)。
- 本步入口：[`K8sReconciler.run`](https://github.com/dextermayhewjd/agent-lightning/blob/0029dbb35c467799d35fee81d15d80264b0d1bd3/agentlightning/controller/k8s_reconciler.py#L126)。
- 这是本项目的第一步，`03` 暂无前序继承；Slime 的已有记录作为带来源的外部参考，不改写成 Agent Lightning 的函数记忆。
- 未运行 Controller、Kubernetes Job 或模型训练；没有将材料准备视为用户已经理解。

</details>
