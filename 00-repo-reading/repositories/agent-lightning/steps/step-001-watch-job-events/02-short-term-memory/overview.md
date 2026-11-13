# 02 · 本步使用的函数记录

[本步入口](../README.md) · [阅读范围](../01-scope.md) · [累计快照](../03-long-term-memory/overview.md)

本步从 watch 进入用户已选择的 `_handle_job_event`，调取其使用的 `_patch_status`，并按本轮问题调取 `_reconcile_once` 比较职责。其余旧函数继续保留在 `03`。

| 源码文件 | 函数记录 | 首次接触 | 本步状态 |
| --- | --- | --- | --- |
| `agentlightning/controller/k8s_reconciler.py` | [K8sReconciler._watch_jobs_loop](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._watch_jobs_loop.md) | Step 000，2026-11-03 | 已联系 namespace/标签筛选与此前列表查询；watcher、事件/对象及更新目标的明确疑问已保存，校准待反馈 |
| `agentlightning/controller/k8s_reconciler.py` | [K8sReconciler._handle_job_event](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._handle_job_event.md) | Step 000 定位边界；Step 001，2026-11-03 独立建卡 | 首轮主流程讲解已覆盖，可返回 watch；用户理解与深入分支不据此标为完成 |
| `agentlightning/controller/k8s_reconciler.py` | [K8sReconciler._patch_status](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._patch_status.md) | Step 000，2026-11-03 | 从本步 03 完整调取，补充成功事件的调用场景；调取不算个人认识更新 |
| `agentlightning/controller/k8s_reconciler.py` | [K8sReconciler._reconcile_once](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md) | Step 000，2026-11-03 | 为比较两条回写路径从本步 03 调取；原有理解、未知和来源保留 |

[本次独立建步的依据](../../step-001-watch-job-events/04-flow.md#step-001-created) · [最初开始 watch 阅读](../../step-000-k8s-controller-entry/04-flow.md#watch-jobs-loop-reading)。
