---
title: "函数对比：关系摘要"
linkTitle: "函数对比（关系摘要）"
description: "用简短的对比和关系句复习接口，为后续整理思维导图提供关系。"
weight: 600
ShowToc: false
hideMeta: true
---

这里保存**接口之间的关系摘要**，用于复习、辨认差别和整理思维导图，不编课号。

第一次学习机制时，先看对应教学页中的例子和执行过程；需要回忆“两个接口有什么共同点、哪里不同、应该选哪个”时，再看这里。

## 已有关系摘要

| 摘要 | 核心关系 | 完整教学 |
| --- | --- | --- |
| [create_task 与 call_soon](call-soon-vs-create-task/) | 共同交给循环调度；一边管理协程，一边登记普通回调 | [call_soon 教学](../loop-call-soon/) |
| [call_soon 与 call_later](call-soon-vs-call-later/) | 都登记普通回调；区别在何时具备执行条件 | [call_later 教学](../loop-call-later/) |
| [Lock 与 RLock](lock-vs-rlock/) | RLock 允许拥有锁的同一线程重复获取，逐次配对释放 | [28.1 · Lock](../28-thread-lock/) / [28.2 · RLock](../28-thread-rlock/) |

每份摘要只保留共同点、关键差别、选择条件和可用于思维导图的关系句。完整程序、运行输出与逐步讲解放在教学页。

[返回学习路线](../learning-route/#function-comparisons) · [Python 异步与并发](../)
