---
title: "18 · Condition、RLock 与 Timer"
description: "线程怎样等待共享状态变化，为什么醒来后还要检查，重入锁和计时线程分别解决什么问题。"
weight: 180
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 从第 11 节继续：线程要等的可能是一条条件

第 11 节的 Lock 保护共享状态，Event 表示开始或停止。现在消费者要等待的是“缓冲里有数据，或者生产者失败了”。这条条件由几个共享字段共同决定，而且消费者醒来后还要安全地取走数据。

`threading.Condition` 把一把锁与等待通知组合起来。使用它时，先说清楚**要等哪个谓词为真**，再安排修改状态、通知和消费的顺序。

<span id="condition-predicate"></span>

## wait 期间释放锁，返回前重新取得锁

先看一个语义骨架。`items` 是共享缓冲；所有检查和修改都使用同一个 condition 的锁。

```python
with condition:
    while not items:
        condition.wait()
    item = items.pop(0)
```

进入 `with condition` 时取得底层锁。`condition.wait()` 先释放它，再让当前线程等待；收到通知后，线程还要重新取得这把锁，wait 才能返回。如果 wait 一直占着锁，生产者就无法进入临界区放入数据。[Python 3.12 Condition 文档](https://docs.python.org/3.12/library/threading.html#condition-objects)

生产者的对应工作是：

```python
with condition:
    items.append("sample")
    condition.notify_all()
```

`notify_all()` 唤醒当前等在此 Condition 上的所有线程，但**不释放锁**。生产者继续持锁，直到退出 `with`；消费者随后竞争同一把锁，逐个重新检查自己的条件。调用 wait、notify_all 时必须已经持有底层锁。

| 时刻 | 消费者 | 生产者 | 底层锁 |
| --- | --- | --- | --- |
| 1 | 检查 items 为空 | 尚未进入 | 消费者持有 |
| 2 | 调用 wait，开始等待 | 可以进入 | wait 已释放 |
| 3 | 被通知，等待重新取得锁 | 放入数据，notify_all | 生产者仍持有 |
| 4 | wait 返回，重新检查并取数据 | 退出 with | 消费者重新持有 |

通知只意味着“值得再检查一次”。多个消费者竞争时，别人可能先取走唯一的数据；通知也可能只表示失败或关闭。因此必须使用 `while`，不能醒来一次就假定一定有数据。

## wait_for 把谓词循环写在一处

下面的写法把“反复检查，必要时 wait”交给 Condition：

```python
with condition:
    ready = condition.wait_for(lambda: bool(items), timeout=5)
    if not ready:
        raise TimeoutError("no data")
    item = items.pop(0)
```

`Condition.wait_for(predicate, timeout)` 在持锁时调用谓词；谓词为假才释放锁等待，醒来重新取得锁后再检查。它返回最后一次谓词的值，超时后可能仍为假。谓词应快速读取共享状态，不要在里面做耗时 I/O。不要将它与 `asyncio.wait_for(awaitable, timeout)` 混淆：一个等线程共享状态，一个管理异步操作的超时。

<span id="rlock-reentrancy"></span>

## RLock 处理同一线程的嵌套加锁

首次学习请先读[28.1 · Lock](../28-thread-lock/)与[28.2 · RLock](../28-thread-rlock/)。本页保留 Condition、RLock、Timer 的旧版综合实验与原下载。

普通 Lock 已由当前线程占有时，再去 acquire 同一把 Lock 也会等待。`threading.RLock()` 记录拥有它的线程和重入层数；同一线程可以再次取得，但每取得一次都必须释放一次。最外层释放之前，其他线程仍然进不来。通常写嵌套 `with lock`，由上下文管理器配对 acquire/release。[RLock 文档](https://docs.python.org/3.12/library/threading.html#rlock-objects)


RLock 只解决同一线程重入同一把锁；多把锁取得顺序相反，仍可能死锁。Condition 默认建立 RLock；显式传入 RLock 时，wait 会完全释放其重入占有，返回前恢复相应状态，而不是只做一次普通 release。

<span id="timer-lifecycle"></span>

## Timer 是延迟执行一次回调的线程

`threading.Timer(interval, function)` 创建一个 Thread 子类实例；`start()` 才开始计时，到期在该线程中执行回调。`join()` 等待这个计时线程结束；`cancel()` 只在回调开始前阻止它运行，不能打断已经进入回调的代码。间隔不是精密时钟，也不要凭“立刻 cancel”推断没有竞态。[Timer 文档](https://docs.python.org/3.12/library/threading.html#timer-objects)


## 运行：一次无数据通知、一份数据、两种 Timer 结局

[下载 example.py](example.py)，运行 `python3 -W error example.py`。只使用标准库，推荐 Python 3.12，最低 Python 3.11。

这是同步原语的语义实验，不是给 Slime 的 Buffer 增加阻塞行为。消费者用 wait_for；控制方先只通知、不放数据，等它确实重新检查为假后再放数据。RLock 展示同线程嵌套。Timer 分别展示执行后 join，以及先 cancel 再 start 的无竞态取消案例。

```text
notify while holding lock True
predicate still false True
received ['sample']
same thread entered twice
outer lock still held
timer called True
cancelled timer called False
```

<details><summary>展开完整可运行示例</summary>

```python
"""Condition predicate, RLock recursion, and Timer lifecycle; Python 3.11+."""

import threading


def main():
    condition = threading.Condition()
    waiting = threading.Event()
    rechecked = threading.Event()
    notified = threading.Event()
    items = []
    received = []

    def has_data():
        # wait_for evaluates this while holding condition's lock.
        if not items:
            waiting.set()
            if notified.is_set():
                rechecked.set()
        return bool(items)

    def read():
        with condition:
            condition.wait_for(has_data)
            received.append(items.pop(0))

    reader = threading.Thread(target=read)
    reader.start()
    waiting.wait()
    with condition:
        notified.set()
        condition.notify_all()  # No data yet: the predicate stays false.
        print("notify while holding lock", not received)
    rechecked.wait()
    print("predicate still false", not received)
    with condition:
        items.append("sample")
        condition.notify_all()
    reader.join()
    print("received", received)

    lock = threading.RLock()
    lock.acquire()
    try:
        with lock:
            print("same thread entered twice")
        print("outer lock still held")
    finally:
        lock.release()

    called = threading.Event()
    timer = threading.Timer(0, called.set)
    timer.start()
    timer.join()
    print("timer called", called.is_set())

    cancelled_call = threading.Event()
    timer = threading.Timer(0, cancelled_call.set)
    # Cancel before start so this experiment cannot race with the callback.
    timer.cancel()
    timer.start()
    timer.join()
    print("cancelled timer called", cancelled_call.is_set())


if __name__ == "__main__":
    main()
```

</details>

<details><summary>复述检查</summary>

wait 放开锁，让生产者有机会改变状态；notify_all 不放锁；被唤醒的消费者重新加锁并检查谓词。RLock 的最后一次释放才让别的线程进入。Timer.cancel 无法强停已经运行的回调，Timer.join 负责等线程真正结束。

</details>

<details><summary>书籍核对与本节判断</summary>

**书上怎么说：** 第 19 章用线程 Event 说明协作式退出。[依据 A]

**我的判断：** Condition、RLock、Timer 的具体语义以 Python 3.12 官方文档及本节实验为依据。本地术语索引和中英全文检索 `threading.Condition`、`RLock`、`threading.Timer` 没有直接命中，书籍不承担这些方法的语义来源。

**依据 A** · 第 19 章《Python 并发模型》› Spinner with Threads，锚点 `spinner-with-threads`。英文 `corpus/en/ch19.md:145–244`，中文 `corpus/zh/ch19.md:133–232`。书籍基于 Python 3.10；本节验证环境 Python 3.12.3。

原文：“By design, there is no API for terminating a thread in Python.”

对照：“Python 故意没有提供终止线程的 API，如果想终止线程，则必须向线程发送相应的消息。”

</details>

{{< python-async-slime >}}

## 回到 Slime：收集结果、暂停、失败和关闭共用通知

沿训练调用方进入 `RolloutScheduler.generate()`：它设置需求量，通知收集线程，然后循环检查 `ready`。没有结果就 wait；有结果就消费，降低 demand，再通知收集方。收集方更新 ready 后同样 notify_all，因此通知连接的是两个方向的状态变化。

<details><summary>源码入口：generate 在结果为空时等待</summary>

{{< source-reference id="source-1" >}}

</details>

暂停沿同一把锁进入 `pause()`，但谓词换成了“控制请求及在途结果已经平息”。关闭时 `close()` 设置 closed 和 error，再通知所有等待者；等待者重新检查 error 才能抛出异常退出。仅仅通知而不改变退出条件，会让它们醒来后继续等待。

<details><summary>源码入口：暂停等待与关闭唤醒</summary>

{{< source-reference id="source-2" >}}

{{< source-reference id="source-3" >}}

</details>

该版本四处 Condition 构造的职责如下。区别在谓词和状态拥有者，wait 的锁语义相同。

| 使用者 | 等待或通知的真实含义 |
| --- | --- |
| `RolloutScheduler` | generate 等 ready 或 error；pause 等控制请求与在途结果；收集、错误和关闭均通知。`_run` 没有 RPC 可等时用带 0.05 秒超时的 wait，再回到循环检查 |
| `AsyncRolloutWorker` | pause 等 admission_paused，以及 drain 时 active 归零；异步循环更新计数后通知，线程退出也通知。线程锁内只短暂交接状态，不能把阻塞式 Condition.wait 放进事件循环线程 |
| `RolloutBuffer` | 显式让 Condition 复用已有 RLock；write 放数据后 notify_all。但当前 read 为空时立即返回空结果，**没有调用 wait**，不能从名字 not_empty 推断它一定阻塞 |
| `GenerationProbe` | wait_for 等 error、done 或测试传入的事件谓词；醒来后再区分错误、提前结束、目标是否真正达成 |

<details><summary>源码入口：Worker、Buffer 与 Probe</summary>

{{< source-reference id="source-4" >}}

{{< source-reference id="source-5" >}}

{{< source-reference id="source-6" >}}

[Worker 更新 active 并通知](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/fully_async_rollout.py#L220-L225)；[Worker 线程退出时通知](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/rollout/fully_async_rollout.py#L163-L172)。读完这些分支，返回调用方的谓词循环，而不是把一次通知当作任务完成。

</details>

Slime 有一条具体的嵌套调用：`get_accelerator()` 取得 `_SELECTION_LOCK` 后调用 `_register_builtin_backends()`，后者调用 `register_accelerator()`，再次取得同一把锁。RLock 允许这个同线程调用链继续。

<details><summary>源码入口：沿嵌套调用检查同一把 _SELECTION_LOCK</summary>

{{< source-reference id="source-7" >}}

{{< source-reference id="source-8" >}}

{{< source-reference id="source-9" >}}

</details>

另外五处构造分别保护存储写入、归档、训练状态、读者租约和插件缓冲：

| RLock 所在位置 | 保护的共享状态 |
| --- | --- |
| `rollout_store` | 返回给同一存储池写入路径共用的锁，调用方用 with lock 写入 |
| `RolloutArchive.save` | 非共享归档建立自己的存储及锁，写入块与元数据时使用 |
| `RolloutQueueController._training_lock` | 训练批次、游标与恢复状态；如 ready_batch 在持锁时调用同样加锁的 batch |
| `QueueReader._lock` | 读样本、归还与心跳线程共同访问的租约表 |
| `RolloutBuffer.lock` | 缓冲及计数，也作为 not_empty 的底层锁 |

<details><summary>其余 RLock 的固定版本入口</summary>

[存储池](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/data/transport.py#L90-L107) · [归档](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/data/archive.py#L49-L74) · [训练批次的嵌套加锁](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/data/queue_data_source.py#L697-L720)及 [ready_batch 调用方](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/data/queue_data_source.py#L807-L830) · [读者租约与心跳](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/slime/data/queue_data_source.py#L1030-L1060)。插件缓冲见上方 source-5。

</details>

Slime 的存储恢复测试暂时破坏文件头，然后 `Timer(0.05, restore).start()` 延迟恢复，观察读取重试是否成功；finally 中 join，确保恢复线程已结束。这里没有使用 cancel，因为测试需要 restore 实际运行。cancel 是本节补充的清理语义。

<details><summary>源码入口：恢复文件头的计时线程</summary>

{{< source-reference id="source-10" >}}

</details>

{{< python-async-coverage lesson="16-thread-coordination" >}}

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节](../15-async-notification/) · [下一节：线程池 Future 的结果与退出](../17-executor-results/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
