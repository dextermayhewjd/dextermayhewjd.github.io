---
title: "Lock 与 RLock：关系摘要"
linkTitle: "Lock ↔ RLock"
description: "两者都保护线程共享状态；RLock 允许拥有锁的同一线程重复获取。"
weight: 30
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

**共同点：都可保护线程共享状态。关键差别：RLock 允许拥有锁的同一线程重复获取。**

| 关系 | threading.Lock | threading.RLock |
| --- | --- | --- |
| 已锁定时，同一线程再次获取 | 默认等待；不支持重入 | 可以再次取得，记录配对次数 |
| 释放要求 | 每次成功获取配对释放；原语允许由其他线程释放 | 由拥有锁的线程逐次配对释放 |
| 其他线程何时能取得 | 锁被释放后 | 最后一次配对释放后 |
| 常见选择 | 持锁路径不需要嵌套获取同一把锁 | 外层持锁，调用的内层也要获取同一把锁 |
| 同一事件循环中的 Task 互斥 | 使用 asyncio.Lock | 使用 asyncio.Lock；RLock 按线程识别拥有者 |

关系句：

- Lock / RLock → 线程同步 → 保护共享状态。
- RLock → 同一拥有线程重入 → 成功获取次数与释放次数配对。
- 内层释放 RLock → 外层仍持锁 → 其他线程继续等待。

[28.1 · Lock 完整教学](../../28-thread-lock/) · [28.2 · RLock 完整教学与 Slime 用法](../../28-thread-rlock/) · [返回关系摘要目录](../)
