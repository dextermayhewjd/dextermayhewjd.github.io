---
title: "create_task 与 call_soon：关系摘要"
linkTitle: "create_task ↔ call_soon"
description: "回忆普通回调和协程任务的共同调度入口，以及输入、返回对象和结果交付的区别。"
weight: 10
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

**共同点：都把工作交给事件循环。区别：call_soon 登记一次普通函数调用；create_task 创建并安排驱动协程的 Task。**

| 关系 | call_soon | create_task |
| --- | --- | --- |
| 接收 | 普通函数及其参数 | 协程对象 |
| 返回 | Handle：管理这次登记 | Task：管理协程的执行和结果 |
| 等待结果 | Handle 不可 await，不收集回调返回值 | 可以 await Task，取得结果或异常 |
| 执行关系 | 循环调用普通函数 | 协程可以在等待处暂停，之后恢复 |
| 取消边界 | 取消尚未执行的登记 | 请求取消协程，仍需等待其处理与收尾 |

## 用于思维导图的关系

- 事件循环 → 调度 → 普通回调 / Task。
- call_soon → 登记普通回调 → 返回 Handle。
- create_task → 安排协程 → 返回 Task → 保存完成结果。

选择：短小的同步动作需要稍后调用时用 call_soon；需要安排协程并跟踪完成结果时用 create_task。两者都不自动创建工作线程。

[完整教学与可运行例子](../../loop-call-soon/) · [返回关系摘要目录](../)
