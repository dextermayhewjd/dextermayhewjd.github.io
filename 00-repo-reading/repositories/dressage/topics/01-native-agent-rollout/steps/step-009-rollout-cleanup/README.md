# Step 009 · generate 退出时的清理责任

[项目唯一进度](../../../../README.md) · [本步 scope](01-scope.md) · [前一步 task flow](../step-008-segments-to-samples/05-task-flow.md)

前一步已取得 Sample 列表。本轮已从 generate 的正常 return 接到 finally，读清后台任务的创建、登记、释放等待与完成回调；完整失败/取消路径保留回查。

- [当前 generate 卡](02-short-term-memory/functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#normal-return)
- [02 本步函数](02-short-term-memory/overview.md)
- [03 前序累计](03-long-term-memory/overview.md)
- [04 形成过程](04-flow.md)

2026-11-09 本轮正常主线首轮收束，见 [05-task-flow](05-task-flow.md)。真实资源回收不因源码出现调度调用而被视为已验证；具体后端和其他未读路径继续保留。
