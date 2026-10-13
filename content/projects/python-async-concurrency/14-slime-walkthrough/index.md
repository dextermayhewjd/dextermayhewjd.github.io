---
title: "14 · 回到 Slime：串起创建、等待与清理"
description: "用一条完整任务主线检查前面学过的原生机制。"
weight: 140
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 这次从一份工作走到结果

不先阅读全仓文件清单。先跟随 `_GenerationActor` 的一条主线，把每个原生机制放回它承担的职责中。

| 顺序 | 到这里做什么 | Python 机制 | 读完返回哪里 |
| --- | --- | --- | --- |
| 1 | 调用方要求开始生产 | 跨线程提交、wrap_future | `_start()` |
| 2 | 建立结果缓冲并启动生产者 | Queue、create_task | `_produce()` |
| 3 | 获取样本、安排生成任务 | await、Task、gather | 各生成槽位 |
| 4 | 发布结果并等待消费 | Queue.put 的异步等待 | 消费者 `_next()` |
| 5 | 同时观察结果和生产者状态 | wait、FIRST_COMPLETED、result | 调用方 |
| 6 | 关闭时处理剩余任务 | cancel、gather、关闭执行器 | 退出生产流程 |

<span id="slime-lifecycle"></span>

## 先走正常路径

`_start` 接收 rollout 编号，建立有界队列，再安排 `_produce`。生产者创建多个生成槽位；每个槽位取得结果后放入输出队列。如果消费者慢，put 的等待会把压力传回生产者。

调用方通过 `_next` 取结果。它不是简单地永远等待 Queue.get，还同时观察生产者：生产者失败时，消费者需要得知失败，而不是卡在一个不会再被填入的队列上。

<details>
<summary>展开 Slime 源码：_GenerationActor.start / _start / _next</summary>

{{< source-reference id="source-1" >}}

</details>

<details>
<summary>展开 Slime 源码：_GenerationActor._produce</summary>

{{< source-reference id="source-2" >}}

</details>

<details>
<summary>展开 Slime 源码：_GenerationActor.close / _close</summary>

{{< source-reference id="source-3" >}}

</details>

## 再补失败与清理

`finally` 取消并等待不再需要的取数任务；生产者的 `finally` 清理自己创建的任务。这里要逐层追踪所有权：一个函数创建了哪些后台任务，就要找到这些任务在退出时由谁收回。

遇到 `to_thread` 再去读数据读取或发布逻辑；遇到生成器再进入模型请求。完成一个职责后返回这里，继续跟踪结果，而不是同时展开所有业务模块。

## 用五个问题检查理解

1. 去掉 Queue 的容量限制，慢消费者会给生产者带来什么影响？
2. 如果只等 `outputs.get()`，生产者先异常退出会发生什么？
3. `take.cancel()` 之后为什么还有 `gather(take, return_exceptions=True)`？
4. 把阻塞读取直接放进 `_produce()`，其他任务会受什么影响？
5. `shield` 保护写入时，调用方取消和工作线程退出分别由谁处理？

<details><summary>对照思路</summary>

分别检查积压结果、永远等待、取消收尾、事件循环阻塞和线程工作所有权。不要用“这是异步函数”替代对具体调用位置的分析。

</details>

下一步可到[全部用法索引](../usage-index/)按 API 回查；那里保留固定版本的全量位置，本页只负责把任务流程读连贯。

{{< python-async-coverage lesson="14-slime-walkthrough" >}}

---

[专题首页](../) · [上一节](../13-event-loop/) · [下一节：Event 通知与异步互斥](../15-async-notification/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
