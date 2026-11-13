# 03 · 进入 Step 001 时的累计函数记录

[本步入口](../README.md) · [本步使用的函数](../02-short-term-memory/overview.md) · [前一步](../../step-000-k8s-controller-entry/README.md)

来源为 Step 000 的 `03 + 02`。前一步的 `03` 尚无函数记录，本次完整继承其 `02` 中的 **7 份函数卡片**，保留原话、源码版本、首次接触、最近认识更新、来源和未知。进入累计记忆不代表已掌握；watch 卡在前一步已开始阅读但尚无个人复述，也如实保留。

| 源码文件 | 函数与记录 | 首次接触 | 最近认识更新 |
| --- | --- | --- | --- |
| `agentlightning/controller/k8s_reconciler.py` | [1 · K8sReconciler._reconcile_once](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#status-data-model) | Step 000，原 scope 说明 | 2026-11-03：已归纳查看 Job 情况、决定是否修改 Gateway 记录的整体用途；缺失分支已复述，条件、计数和回写细节仍待确认 |
| `agentlightning/controller/k8s_reconciler.py` | [1 内部 · K8sReconciler._query_rollouts](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._query_rollouts.md) | Step 000，2026-11-03 独立建卡 | 2026-11-03：已复述查询与对象列表转换；筛选条件和返回记录的区别待校准 |
| `agentlightning/controller/k8s_reconciler.py` | [1 内部 · K8sReconciler._get_k8s_api](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._get_k8s_api.md) | Step 000，2026-11-03 独立查看 | 已表述 Gateway 与 Kubernetes 两类服务的区别；缓存机制未复述 |
| `agentlightning/controller/k8s_reconciler.py` | [2 · K8sReconciler._create_job](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._create_job.md) | Step 000，2026-11-03 本轮明确选择后建卡 | 已初步概括按 manifest 创建 Job；限速、异常等内部实现留白 |
| `agentlightning/controller/k8s_reconciler.py` | [4 · K8sReconciler._watch_jobs_loop](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._watch_jobs_loop.md) | Step 000，2026-11-03 用户明确选择后建卡 | 已开始事件接收与交接的阅读，尚无个人复述 |
| `agentlightning/controller/k8s_reconciler.py` | [5 · K8sReconciler._patch_status](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._patch_status.md) | Step 000，2026-11-03 用户选择独立建卡 | 已复述 RUNNING 缺失 Job 时通过此函数报告异常；状态登记的精确含义由助手补准，内部仍留白 |
| `kr8s/_objects.py`（依赖库） | [1 内部 · APIObject.async_list，Job 查询场景](functions/kr8s/_objects.py/APIObject.async_list.md) | Step 000，2026-11-03 | 已复述通过 K8s API 按 namespace 和标签查询 Job；具体对象形态未单独复述 |

每张卡片保留原 Step 000 范围与形成过程的来路；累计索引及卡片之间的函数链接在本快照内可用。本步对 watch 的后续认识只写入 `02`，这里保留入步时的版本。
