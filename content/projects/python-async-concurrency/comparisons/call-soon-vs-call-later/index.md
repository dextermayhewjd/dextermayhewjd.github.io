---
title: "call_soon 与 call_later：关系摘要"
linkTitle: "call_soon ↔ call_later"
description: "回忆就绪回调与定时回调的关系，以及登记时间、到期和实际执行的区别。"
weight: 20
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

**共同点：现在登记普通回调。区别：call_soon 进入就绪队列；call_later 先登记到期时间，到期后再等待循环执行。**

| 关系 | call_soon | call_later |
| --- | --- | --- |
| 登记时间 | 现在 | 现在 |
| 执行条件 | 循环处理到这份就绪回调 | 到期后，循环处理到这份回调 |
| 返回对象 | Handle | TimerHandle，是 Handle 的一种 |
| 取消 | 执行前可以取消 | 执行前可以取消 |

## 用于思维导图的关系

- call_soon → 就绪队列 → 普通回调。
- call_later → 定时登记 → 到期进入就绪队列 → 普通回调。
- TimerHandle → 属于 → Handle。

选择：尽快安排用 call_soon；需要延迟条件用 call_later。call_soon 不插队，call_later 不保证精确准点；两者都不会打断正在执行的代码。

[完整教学、运行输出与 Slime 例子](../../loop-call-later/) · [返回关系摘要目录](../)
