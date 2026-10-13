---
title: "版本与参考"
description: "区分语言实验、Slime 原始源码与书籍依据。"
weight: 1000
ShowToc: true
hideMeta: true
hideSummary: true
ShowPostNavLinks: false
---

## 示例与源码的边界

当前共有 21 节，其中 20 节提供主要标准库实验，第 14 节串联真实任务主线；另有 6 份对比或补充实验。实验用来观察语言行为；涉及 Slime 时，优先保留原函数名，并说明删去的业务内容。折叠区域展示的是实际源码连续摘录，不把实验代码冒充原实现。

本专题固定 Slime 提交为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。示例在 Python 3.12 上校验，因使用 `asyncio.timeout`，统一要求 Python 3.11 及以上。它不是对 Slime 所有部署环境版本的推断。

## 书上怎么说

网络请求应限制并发数量，避免同一时间向服务端发送过多请求。[依据 A]

## 我的判断（本书未覆盖）

本专题按“调用 → 等待 → 调度 → 收尾”组织 Slime 源码。这是结合实际代码选择的学习顺序，不是书籍对 Slime 的评价。线程池、结果队列和任务上下文承担不同职责，需要分别检查。

书籍基于 Python 3.10。`asyncio.timeout` 等后续 API 以当前官方文档为准；任务引用与取消也按官方说明核对，不直接照搬书中所有建议。

## 依据 A

第 21 章《异步编程》：Throttling Requests with a Semaphore。

- 英文：`corpus/en/ch21.md:483–606`，锚点 `throttling-requests-with-a-semaphore`。
- 中文：`corpus/zh/ch21.md:445–571`，同一锚点，“21.7.2 使用信号量限制请求”。
- 版本：Fluent Python, 2nd Edition（2022），基于 Python 3.10；本专题实验环境为 Python 3.12。

原文：

> Network clients like the ones we are studying should be throttled (i.e., limited) to avoid pounding the server with too many concurrent requests.

对照：

> 像我们分析的这种网络客户端应该限流，以免对服务器发起过多并发请求。

已核对本地中英文镜像的小节行号和逐字引文。

## 官方文档

- [协程、Task、结果、取消、超时与跨线程提交](https://docs.python.org/3.12/library/asyncio-task.html)
- [事件循环和回调](https://docs.python.org/3.12/library/asyncio-eventloop.html)
- [异步同步原语](https://docs.python.org/3.12/library/asyncio-sync.html)与[异步队列](https://docs.python.org/3.12/library/asyncio-queue.html)
- [线程](https://docs.python.org/3.12/library/threading.html)与[执行器](https://docs.python.org/3.12/library/concurrent.futures.html)
- [多进程](https://docs.python.org/3.12/library/multiprocessing.html)与[外部命令](https://docs.python.org/3.12/library/subprocess.html)
- [上下文变量](https://docs.python.org/3.12/library/contextvars.html)与[异步上下文管理器](https://docs.python.org/3.12/library/contextlib.html#contextlib.asynccontextmanager)


## 完整源码与讲解的对应关系

[源码用法与教程对照](../coverage/)将 83 个直接 API 名称、747 个语法位置及全部扫描记录连接到讲解。每节末尾保留该类用法的原代码行、固定源码链接和完整文件快照；29 段文档示例单列。对象方法的接收者推断与未确认候选保留各自标记，不与直接 API 混计。

[返回专题首页](../)
