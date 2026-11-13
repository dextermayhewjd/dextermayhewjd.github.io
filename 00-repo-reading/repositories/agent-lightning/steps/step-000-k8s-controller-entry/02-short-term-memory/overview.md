# 02 · 本步函数记录

[本步正文](../README.md) · [阅读范围](../01-scope.md) · [前序累计记录](../03-long-term-memory/overview.md)

本目录只收录已经实际接触并展开的函数；编号沿用 [scope 阅读导航](../01-scope.md#reading-navigation)。用户已撤回提前创建的未读函数卡，骨架中其余调用先链接源码，实际阅读时再建卡。当前记录不因文件存在就标为已掌握。

| 源码文件 | 函数与记录 | 首次接触 | 最近认识更新 |
| --- | --- | --- | --- |
| `agentlightning/controller/k8s_reconciler.py` | [1 · K8sReconciler._reconcile_once](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md#status-data-model) | Step 000，原 scope 说明 | 2026-11-03：已归纳查看 Job 情况、决定是否修改 Gateway 记录的整体用途；缺失分支已复述，条件、计数和回写细节仍待确认 |
| `agentlightning/controller/k8s_reconciler.py` | [1 内部 · K8sReconciler._query_rollouts](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._query_rollouts.md) | Step 000，2026-11-03 独立建卡 | 2026-11-03：已复述查询与对象列表转换；筛选条件和返回记录的区别待校准 |
| `agentlightning/controller/k8s_reconciler.py` | [1 内部 · K8sReconciler._get_k8s_api](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._get_k8s_api.md) | Step 000，2026-11-03 独立查看 | 已表述 Gateway 与 Kubernetes 两类服务的区别；缓存机制未复述 |
| `agentlightning/controller/k8s_reconciler.py` | [2 · K8sReconciler._create_job](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._create_job.md) | Step 000，2026-11-03 本轮明确选择后建卡 | 已初步概括按 manifest 创建 Job；限速、异常等内部实现留白 |
| `agentlightning/controller/k8s_reconciler.py` | [4 · K8sReconciler._watch_jobs_loop](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._watch_jobs_loop.md) | Step 000，2026-11-03 用户明确选择后建卡 | 已开始事件接收与交接的阅读，尚无个人复述 |
| `agentlightning/controller/k8s_reconciler.py` | [5 · K8sReconciler._patch_status](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._patch_status.md) | Step 000，2026-11-03 用户选择独立建卡 | 已复述 RUNNING 缺失 Job 时通过此函数报告异常；状态登记的精确含义由助手补准，内部仍留白 |
| `kr8s/_objects.py`（依赖库） | [1 内部 · APIObject.async_list，Job 查询场景](functions/kr8s/_objects.py/APIObject.async_list.md) | Step 000，2026-11-03 | 已复述通过 K8s API 按 namespace 和标签查询 Job；具体对象形态未单独复述 |

`build_job_spec` 仍只定位接口，未建立独立卡片；后续步骤与记录继承见 scope 的记录映射。

用户此前关于两个项目分工的表述作为本步背景保留，未代填成 `run` 的个人理解。[本步开始与原观察点](../../step-000-k8s-controller-entry/04-flow.md#first-observation) · [先看整体骨架的修正](../../step-000-k8s-controller-entry/04-flow.md#scope-first-revision)。

[编号与步骤／记录映射的本轮讨论](../../step-000-k8s-controller-entry/04-flow.md#numbered-reading-map)。

[函数说明移出 scope 的本轮讨论](../../step-000-k8s-controller-entry/04-flow.md#function-notes-out-of-scope)。
