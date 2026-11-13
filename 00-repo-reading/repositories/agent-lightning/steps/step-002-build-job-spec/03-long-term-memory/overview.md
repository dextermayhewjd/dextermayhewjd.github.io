# 03 · 进入 Step 002 时的累计函数记录

[本步入口](../README.md) · [本步使用的函数](../02-short-term-memory/overview.md) · [前一步](../../step-001-watch-job-events/README.md)

合并 Step 001 的 `03 + 02`，按源码路径与符号归并为 **8 份完整记录**。同名函数采用前一步完整的 02 版本，其原始来源与此前快照仍可回查；其余记录继续继承。没有因进入长期记忆而改变个人理解、首次接触或未知。

| 函数记录 | 首次接触 | 本次继承来源 |
| --- | --- | --- |
| [K8sReconciler._create_job](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._create_job.md) | Step 000，2026-11-03。本次用户明确选择进入；此前同名未读备稿已撤回，不作已读依据。 | Step 001 / 03；理解与未知完整保留在卡内 |
| [K8sReconciler._get_k8s_api](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._get_k8s_api.md) | Step 000，2026-11-03；本轮独立查看两个客户端的区别。 | Step 001 / 03；理解与未知完整保留在卡内 |
| [K8sReconciler._handle_job_event](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._handle_job_event.md) | Step 000 先定位调用边界，Step 001 先解释更新目标；2026-11-03 用户明确选择独立阅读并建卡。 | Step 001 / 02；理解与未知完整保留在卡内 |
| [K8sReconciler._patch_status](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._patch_status.md) | Step 000 中先按接口定位；2026-11-03 用户明确要求独立建卡并阅读。 | Step 001 / 02；理解与未知完整保留在卡内 |
| [K8sReconciler._query_rollouts](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._query_rollouts.md) | Step 000 的数据来源讨论；2026-11-03 首次独立建卡并开始阅读。 | Step 001 / 03；理解与未知完整保留在卡内 |
| [K8sReconciler._reconcile_once](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._reconcile_once.md) | Step 000，2026-11-03。 | Step 001 / 02；理解与未知完整保留在卡内 |
| [K8sReconciler._watch_jobs_loop](functions/agentlightning/controller/k8s_reconciler.py/K8sReconciler._watch_jobs_loop.md) | Step 000，2026-11-03；用户明确选择本函数后建卡。 | Step 001 / 02；理解与未知完整保留在卡内 |
| [APIObject.async_list（Job 查询场景）](functions/kr8s/_objects.py/APIObject.async_list.md) | Step 000，2026-11-03，父函数的 Job 查询语句。 | Step 001 / 03；理解与未知完整保留在卡内 |

这是进入本步时的快照。本步 build_job_spec 的新说明与个人反馈写入 02；当前仅调取已确认回顾的 _create_job，不递归复制所有辅助函数到短期目录。
