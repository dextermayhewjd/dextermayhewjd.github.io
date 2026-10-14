---
title: "17 · Event 通知与异步互斥"
description: "从已知任务等待通知开始，理解 Event 的布尔标志，以及 Lock 保护共享状态的边界。"
weight: 170
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 已经有一个任务，为什么还要 Event

前面已经会用 `create_task()` 启动任务，用 `await task` 等它结束。现在多一个要求：**任务已经开始，但必须等控制方允许，才能继续下一步**。例如取样任务已经进入 `fetch()`，测试需要先执行暂停操作，再允许取样返回。

这里有两个不同的等待：控制方等“已经进入 fetch”，fetch 等“允许返回”。用两个 Event 能明确表达这两次交接，不需要猜测 `sleep(0.01)` 是否足够。

<span id="event-notification"></span>

## 第一步：把通知看作一个布尔标志

`asyncio.Event()` 初始保存 `False`。`await event.wait()` 在标志为假时挂起当前任务，让事件循环运行其他任务；标志为真时立即返回 `True`。`event.set()` 把标志设为真，并唤醒正在等待的任务；`event.is_set()` 只读取当前标志。它们中的 `set()` 和 `is_set()` 不需要 `await`。[Python 3.12 Event 文档](https://docs.python.org/3.12/library/asyncio-sync.html#event)

先只看这一小段。`group` 是我们最终要返回的一组样本；`count` 和返回的“样本组列表”保持源码接口。

```python
entered, release = asyncio.Event(), asyncio.Event()
group = ["sample"]

async def fetch(count):
    entered.set()              # 告诉控制方：我已经进入取样
    await release.wait()       # 等控制方允许我返回
    return [group][:count]

task = asyncio.create_task(fetch(1))
await entered.wait()
# 到这里，fetch 已经运行到 release.wait()，但还没有返回。
release.set()
result = await task
```

此段位于异步函数内。`entered.set()` 后，fetch 接着执行到尚未设置的 `release.wait()` 才挂起，因此控制方从 `entered.wait()` 恢复时，能检查一个已知的等待位置。

| 顺序 | fetch 任务 | 控制方 | release 标志 |
| --- | --- | --- | --- |
| 1 | 尚未运行 | 创建任务，然后等 entered | False |
| 2 | entered.set，进入 release.wait | 可以恢复执行 | False |
| 3 | 仍在等待 | 执行 release.set | True |
| 4 | 被安排继续，返回样本组 | await task 收到返回值 | True |

`set()` 使等待者能够恢复；它不会直接代替事件循环执行等待者后面的所有代码。要确认任务已经结束，仍然要 `await task`。

## 第二步：理解 clear 为什么不是“扣掉一次通知”

`release.set()` 两次后，标志仍然只是 `True`。这时连续执行两次 `await release.wait()`，两次都能立即返回。`wait()` 不消耗通知，也不自动清零。

`release.clear()` 把标志重新设成 `False`，使**随后开始的等待**需要下一次 `set()`；它不会把已经结束的任务退回去，也不能收回已经唤醒的等待者。因此要像本节示例一样，先等上一轮任务结束，再 clear，才开始下一轮。[Event.clear 语义](https://docs.python.org/3.12/library/asyncio-sync.html#asyncio.Event.clear)

Event 不保存“来了三份数据”这种数量，也不携带样本。样本仍在 `group` 中。如果每次通知都必须消费一份独立工作，应回到第 09 节的 Queue；Event 适合表达“已就绪”“允许继续”这样的状态。

<span id="async-lock"></span>

## 有通知还不够：共享状态需要一起修改

Event 可以放行多个任务。若两个请求都准备更新同一份状态，还需要 `asyncio.Lock()`：`await lock.acquire()` 等到锁可用并取得它；`lock.release()` 释放锁；`lock.locked()` 查询当前是否已被取得。查询结果不是取得锁的保证，不要用“先查 locked 再修改状态”替代 acquire。[Python 3.12 Lock 文档](https://docs.python.org/3.12/library/asyncio-sync.html#lock)

通常直接写 `async with lock`，让异常或取消退出代码块时也能释放。它对应下面的控制结构：

```python
await update_lock.acquire()
try:
    # 读取并修改需要保持一致的共享状态
    ...
finally:
    update_lock.release()
```

同一把异步锁已有多个等待者时，先开始等待 acquire 的任务先获得锁。对未锁定的锁调用 `release()` 会抛出 `RuntimeError`。`asyncio.Lock` 也不提供同一任务重入的承诺：持有它时再次 acquire 会把自己挡住；下一节的 `threading.RLock` 是不同的机制。


即使事件循环通常只有一个线程，也需要检查 await 边界：一次逻辑操作如果跨越挂起点，别的任务可能观察或改变共享状态。反过来，也不要把耗时同步函数放到锁内，以为加锁能让它变成异步。

## 运行一个固定顺序的实验

[下载 example.py](example.py)，运行 `python3 -W error example.py`。只使用标准库，推荐 Python 3.12，最低 Python 3.11。

前半段沿用 Slime 测试的 `entered/release` 和 `fetch(count)`，把实际取样替换成内存样本。后半段是独立的 Lock 语义实验：保留 `update_from_disk`、`model_path` 与 `updating_model_path` 这些对应关系，但输入改为字典，省略 HTTP、合并请求和磁盘更新，不能当作原实现。

```text
initial False
waiting True
set True
received [['sample']]
wait again True
cleared False
waiting again True
lock held True
update waiting True
updated checkpoint-2
lock released False
```

<details><summary>展开完整可运行示例</summary>

```python
"""Event notifications and task mutual exclusion; Python 3.11+."""

import asyncio


async def main():
    # Keep the entered/release handshake and fetch(count) from Slime's test.
    entered, release = asyncio.Event(), asyncio.Event()
    group = ["sample"]

    async def fetch(count):
        entered.set()
        await release.wait()
        return [group][:count]

    print("initial", release.is_set())
    task = asyncio.create_task(fetch(1))
    await entered.wait()
    print("waiting", not task.done())
    release.set()
    release.set()  # Two notifications still leave only one True flag.
    print("set", release.is_set())
    print("received", await task)
    print("wait again", await release.wait())

    release.clear()
    entered.clear()
    print("cleared", release.is_set())
    task = asyncio.create_task(fetch(1))
    await entered.wait()
    print("waiting again", not task.done())
    release.set()
    await task

    # A separate API experiment: hold a lock while a known task requests it.
    update_lock = asyncio.Lock()
    requested = asyncio.Event()
    update_state = {"updating_model_path": None}

    async def update_from_disk(request):
        requested.set()
        async with update_lock:
            update_state["updating_model_path"] = request["model_path"]
        return update_state["updating_model_path"]

    await update_lock.acquire()
    try:
        task = asyncio.create_task(update_from_disk({"model_path": "checkpoint-2"}))
        await requested.wait()
        print("lock held", update_lock.locked())
        print("update waiting", not task.done())
    finally:
        update_lock.release()
    print("updated", await task)
    print("lock released", update_lock.locked())


if __name__ == "__main__":
    asyncio.run(main())
```

</details>

这里的顺序由 Event 握手和显式持锁确定，没有依赖机器速度。Event 与异步 Lock 都用于同一事件循环中的任务，不是 OS 线程间同步对象。

<details><summary>复述检查</summary>

1. release.set 两次，再 wait 两次，第二次会等待吗？不会，标志没有被消费。
2. clear 能撤回已经返回的 fetch 吗？不能，它改变的是后续等待条件。
3. set 之后怎样确认工作完成？await 对应任务。
4. locked 返回 False 后能直接写共享状态吗？应先 acquire；观察状态不等于占有锁。

</details>

<details><summary>书籍核对与本节判断</summary>

**书上怎么说：** 无直接对应条目。本地《Fluent Python 第 2 版》标识符索引及中英全文检索 `asyncio.Event`、`asyncio.Lock`、`Condition`、`RLock`，没有覆盖本节这组异步同步原语的说明；不能把第 19 章的 threading.Event 直接当作 asyncio.Event。

**我的判断：** 上面的教学顺序来自实际 Slime 测试和本节实验；方法语义按 Python 3.12 官方文档核对。书籍基于 Python 3.10，运行验证环境为 Python 3.12.3。

</details>

{{< python-async-slime >}}

## 回到 Slime：先暂停，再让取样返回

这次沿测试中的 `_GenerationActor._generate_group()` 进入异步取样。测试先等 entered，确认取样确实在途，再调用 `worker._pause()`，最后 release.set，让取样结果回来。随后检查：结果被放回缓冲，没有新启动生成请求。Event 的作用是把暂停与返回的相对顺序固定下来。

<details><summary>源码入口：取样与暂停的双向通知</summary>

{{< source-reference id="source-1" >}}

</details>

同一版本其他 Event 用法也围绕“把测试停在一个明确位置”展开：

| 源码场景 | 谁设置，谁等待 | 读完要确认什么 |
| --- | --- | --- |
| 慢生成组与其他组并发 | 测试设置 release，第一组生成等待 | 慢组仍被挡住时，其他组能返回；is_set 检查挡板状态 |
| 流式取消 | 流发出首块后设置 first_chunk_seen；服务器任务设置 server_started | 测试等两个条件，再取消；request_closed.is_set 检查清理回调发生 |
| 节奏控制 | 指定数量任务启动后设置 first_batch / all_started，生成任务等 finish | 检查在途数量与取消，再统一放行 |
| 中途恢复 | `await asyncio.Event().wait()` 没有设置者 | 有意保持在途，等待外部取消或进程终止，不是业务中会自行结束的等待 |
| 样本存储顺序 | 存储后通过 `loop.call_soon_threadsafe(second.set)` 通知 | Event 由事件循环线程设置；线程间交接不能直接当作 Event 线程安全 |

<details><summary>上述场景的固定版本位置</summary>

- [慢生成组](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_distributed_rollout.py#L970-L1036)
- [流式取消与清理](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_streaming_rollout.py#L351-L440)
- [节奏控制及等待中止](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_streaming_rollout.py#L532-L624)
- [保持恢复测试在途](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_straw_fully_async_recovery.py#L45-L52)
- [先存储后通知](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tests/test_rollout_straw_transport.py#L375-L392)

索引中 18 处 `asyncio.Event()` 构造均在测试文件。该版本没有直接调用 `asyncio.Event.clear()`；本节补充它，是为了完整说明复用状态的语义。测试还在学习包摘录之外使用了 `wait_for(event.wait(), timeout)`：Event 本身不接受 timeout，超时管理交给前面学过的异步等待工具。

</details>

Slime 的 HTTP 更新请求先进入 `update_from_disk()`，在锁内检查 `in_progress`、模型路径与已有 Future：同路径请求共用 Future，不同路径请求返回冲突；新更新则预留状态。之后离开锁再做耗时更新，最后重新取得锁，设置结果并清理状态。这把锁保护的是短暂的状态交接，没有覆盖整个磁盘更新过程。

<details><summary>源码入口：检查状态、预留更新与最终清理</summary>

{{< source-reference id="source-2" >}}

{{< source-reference id="source-3" >}}

</details>

{{< python-async-coverage lesson="15-async-notification" >}}

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节](../14-slime-walkthrough/) · [下一节：Condition、RLock 与 Timer](../16-thread-coordination/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
