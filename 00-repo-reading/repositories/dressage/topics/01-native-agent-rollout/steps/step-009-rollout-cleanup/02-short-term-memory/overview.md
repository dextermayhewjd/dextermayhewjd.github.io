# Step 009 · 本步短期记录

| 函数 | 本步范围 |
| --- | --- |
| [blackbox_dispatch.generate](functions/dressage/rollout/generate/blackbox_dispatch.py/generate.md#normal-return) | 前序调取；正常 return 接到 finally 的责任判断 |
| [schedule_terminate_paddock](functions/dressage/paddock/lifecycle.py/schedule_terminate_paddock.md) | 正常路径：组装回收协程，交给调度器创建并跟踪任务 |
| [schedule_lifecycle_task](functions/dressage/paddock/lifecycle.py/schedule_lifecycle_task.md) | 创建回收 Task，再交给跟踪函数登记 |
| [track_lifecycle_task](functions/dressage/paddock/lifecycle.py/track_lifecycle_task.md) | 按事件循环登记 Task、返回原 Task；含完成回调移除登记的简读 |
| [terminate_paddock_best_effort](functions/dressage/paddock/lifecycle.py/terminate_paddock_best_effort.md) | 内层释放 Task、限时等待及超时/取消后的跟踪交接 |

实际 Paddock 释放和会话取消 helper 尚未逐段展开。
