---
title: "19 · asyncio.Lock：保护跨 await 的共享状态"
description: "从两次加一却只得到 1 开始，理解同一把 Lock 怎样保护完整修改、在 await 时保持占用，并在正常、异常和取消退出时释放。"
weight: 190
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. await / 共享状态：为什么加了两次，结果却只有 1？

第 18 课用 Queue 让生产者与消费者交接数据。现在换一个要求：**两份任务都要修改同一个计数，每份各加一，最后应该得到 2。**

Queue 能交接数据，但不会自动保护取出数据以后对其他共享变量的修改。先用已经学过的 TaskGroup 安排两份任务，看看直接读写同一个字典会怎样。

这是独立标准库实验，不是 Slime 源码的裁剪。`state` 是两份任务共用的字典；每次调用里的 `current` 是该次调用自己的局部变量。这里的 `sleep(0)` **专门让出本轮执行，以便看到修改中途发生切换**，没有需要等待的业务耗时。

[下载 without_lock.py](without_lock.py)，使用 Python 3.11 及以上运行 `python3 without_lock.py`。本课实际在 Python 3.12.3、默认任务调度方式下验证。

```python
import asyncio


async def increment(name, state):
    current = state["count"]
    print(name, "read", current)
    await asyncio.sleep(0)
    state["count"] = current + 1
    print(name, "wrote", state["count"])


async def exercise():
    state = {"count": 0}
    async with asyncio.TaskGroup() as group:
        group.create_task(increment("A", state))
        group.create_task(increment("B", state))
    print("total", state["count"])


if __name__ == "__main__":
    asyncio.run(exercise())
```

实际输出：

```text
A read 0
B read 0
A wrote 1
B wrote 1
total 1
```

沿这一次输出理解：

1. A 读到 0，保存到自己的 `current`，随后挂起。
2. B 此时也读到 0，保存到 B 自己的 `current`，随后挂起。
3. A 恢复，按自己的旧值计算 `0 + 1`，写回 1。
4. B 恢复，也按自己的旧值计算 `0 + 1`，再次写回 1。

两份任务都正常结束了，TaskGroup 也等完了它们；问题出在**“读取旧值 → 中途等待 → 根据旧值写回”被另一份任务插了进来**。TaskGroup 管任务的等待与收尾，没有让这一整段修改互斥执行。

<span id="async-lock"></span>

## 2. asyncio.Lock / async with：让同一时刻只有一份任务进入修改区

### 2.1 Lock：创建同一个对象，传给两份任务

新增的要求是：A 从读取到写回期间，B 先不要进入同一段修改。

`lock = asyncio.Lock()` 创建一把初始未被取得的异步锁。把**同一个 `lock` 和同一个 `state`** 传给 A、B，再用 `async with lock` 包住完整操作。

| 位置 | 做什么 |
| --- | --- |
| `asyncio.Lock()` | 创建锁；这一步没有运行任务，也没有取得锁 |
| `async with lock:` 进入时 | 尝试取得锁；需要等待时挂起当前任务，取得后才能进入代码块 |
| 代码块内部 | 执行需要互斥的操作；中途 `await` 挂起时仍然占用锁 |
| 离开代码块时 | 释放锁，让下一份等待同一把锁的任务有机会进入 |

[下载 example.py](example.py)，运行 `python3 example.py`。下面左侧数字是文件真实行号，不属于复制和下载的代码。

<div class="async-coordination-code">

```python
import asyncio


async def increment(name, state, lock):
    print(name, "waiting")
    async with lock:
        current = state["count"]
        print(name, "read", current)
        await asyncio.sleep(0)
        state["count"] = current + 1
        print(name, "wrote", state["count"])
    print(name, "released")


async def exercise():
    state = {"count": 0}
    lock = asyncio.Lock()
    async with asyncio.TaskGroup() as group:
        group.create_task(increment("A", state, lock))
        group.create_task(increment("B", state, lock))
    print("total", state["count"])


if __name__ == "__main__":
    asyncio.run(exercise())
```

</div>

### 2.2 async with / await：谁在等锁，谁只是暂时让出执行？

泳道图从上往下读，一行只记录一份任务正在执行的动作。`T` 是本次运行顺序，`L` 对应上面文件行号；空白列的等待一直持续到它自己的 `RESUME`。`LOCK` 是这一步结束时的占用者，`COUNT` 是共享字典里的值。

<div class="async-lock-lanes" id="lock-swimlanes">

```text
# T = 本次运行的执行顺序；L = example.py 的真实行号。
# 每行只有一个任务在执行；空白列的等待持续到它自己的 RESUME。
# LOCK 记录这一行结束时谁已取得锁；- 表示没有任务持有锁。
# +------+------------------------+----------------------------+------------------------------+------+-------+
# | STEP | MAIN                   | A                          | B                            | LOCK | COUNT |
# +------+------------------------+----------------------------+------------------------------+------+-------+
# | T01  | L16-20 setup           |                            |                              | -    | 0     |
# | T02  | L18 WAIT: A+B END      |                            |                              | -    | 0     |
# | T03  |                        | L5-8 acquire; read 0       |                              | A    | 0     |
# | T04  |                        | L9 WAIT: next loop turn    |                              | A    | 0     |
# | T05  |                        |                            | L5-6 WAIT: release at T06    | A    | 0     |
# | T06  |                        | L9-12 RESUME; write 1; END |                              | -    | 1     |
# | T07  |                        |                            | L6-8 RESUME; acquire; read 1 | B    | 1     |
# | T08  |                        |                            | L9 WAIT: next loop turn      | B    | 1     |
# | T09  |                        |                            | L9-12 RESUME; write 2; END   | -    | 2     |
# | T10  | L18,21 RESUME; total 2 |                            |                              | -    | 2     |
# +------+------------------------+----------------------------+------------------------------+------+-------+
# T02: MAIN 在 L18 退出 TaskGroup 时等 A、B 结束，到 T10 才继续 L21。
# T04: A 在 L9 的 sleep(0) 让出本轮执行；没有离开 async with，锁仍由 A 持有。
# T05: B 在 L6 等同一把锁；等 A 在 T06 离开代码块时释放，到 T07 才取得锁。
# T06: A 从 L9 恢复，L10 写回 1；离开 L6 的代码块时释放锁，L12 输出 released。
# T08: B 在 L9 让出本轮执行；锁仍由 B 持有，到 T09 恢复并写回 2。
# 释放锁只使等待者有机会继续，不会直接在 release 里面运行等待者的函数体。
```

</div>

[下载注释泳道图 execution-flow.py](execution-flow.py)。图是这一份实验的运行记录；正确性依赖同一把锁保护完整修改，不要求所有程序都以 A 先、B 后的顺序执行。

重点区分两处等待：

1. **A 在 L9 等待重新调度，仍占着锁。** 事件循环可以运行 B，但 B 到 L6 后会等锁，尚未读到 `count`。
2. **B 在 L6 等待 A 释放锁。** A 写回 1 并退出后，B 才取得锁、读到 1，最后写回 2。

因此，**挂起当前任务不等于释放当前任务取得的锁**。没有使用这把锁的其他任务仍然可以运行；Lock 只协调遵守同一把锁的代码。[Python 3.12 Lock 文档](https://docs.python.org/3.12/library/asyncio-sync.html#lock)

<details>
<summary>按需核对：原始输出与泳道步骤</summary>

| 输出 | 对应步骤 |
| --- | --- |
| `A waiting`、`A read 0` | T03：A 取得锁并读取 |
| `B waiting` | T05：B 即将尝试取得锁，随后挂起 |
| `A wrote 1`、`A released` | T06：A 写回、退出并释放 |
| `B read 1` | T07：B 恢复并取得锁 |
| `B wrote 2`、`B released` | T09：B 写回、退出并释放 |
| `total 2` | T10：TaskGroup 等完两份任务 |

</details>

<span id="lock-acquire-release"></span>

## 3. acquire / release：与 async with 等价，选择一种写法即可

和第 17 课的 Semaphore 一样，这里不是要在 `async with` 外面再加一遍取得、释放。通常使用 `async with lock`；展开它，是为了看懂进入与退出各发生什么。

```python
await lock.acquire()
try:
    current = state["count"]
    await asyncio.sleep(0)
    state["count"] = current + 1
finally:
    lock.release()
```

这是 `increment` 内部的结构片段。完整手动版本见 [manual.py](manual.py)，保留了主例子的打印，运行输出与 `example.py` 一致。

1. **`await lock.acquire()`：等到可以取得锁，取得后返回 `True`。** 锁可用时可以直接完成，已有占用者时会等待。它不返回计数，也不会替你修改字典。
2. **`try`：执行这一整段需要保护的操作。** 要从读取旧值开始包住；只在最后写回时加锁，前面读到的旧值仍可能已经过时。
3. **`finally` 中的 `lock.release()`：释放锁，返回 `None`。** 它是普通方法，不需要 `await`；正常结束、报错或取消导致离开时，都经过这一段释放。[取得与释放的官方说明](https://docs.python.org/3.12/library/asyncio-sync.html#asyncio.Lock.acquire)

这里特意把 `acquire()` 放在 `try` **前面**：如果还没取得锁就被取消，就不应执行配对的 `release()`。对未被取得的锁调用 `release()` 会报 `RuntimeError`；也不要替仍在使用锁的另一份任务释放它。

从限制进入数量的角度，Lock 与 `Semaphore(1)` 接近；这里使用 Lock，直接表达“这份共享状态一次只由一份任务进入修改”。不需要再叠加一层 Semaphore。

<span id="lock-exit"></span>

## 4. Task.cancel / async with：取消之后，锁什么时候释放？

锁内的业务仍然可能报错，任务也可能被取消。沿用第 09 课的结论：`task.cancel()` 提出取消请求，之后还要等待任务处理取消和清理。

下面让任务先取得锁，再在一个长等待中被取消。[下载 cancellation.py](cancellation.py)，实际运行不会等待一小时。

```python
import asyncio


async def hold(lock):
    async with lock:
        print("holder acquired")
        try:
            await asyncio.sleep(3600)
        finally:
            print("holder cleanup")


async def exercise():
    lock = asyncio.Lock()
    task = asyncio.create_task(hold(lock))
    await asyncio.sleep(0)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("holder cancelled")
    async with lock:
        print("lock acquired again")


if __name__ == "__main__":
    asyncio.run(exercise())
```

本例主程序的 `sleep(0)` 先让 `hold` 运行到长等待；随后才发出取消请求。输出旁边对应的退出过程如下：

| 实际输出 | 正在执行什么 |
| --- | --- |
| `holder acquired` | `hold` 已取得锁，接下来进入长等待 |
| `holder cleanup` | 长等待处收到取消，先执行代码块内部的 `finally`；这时还没有离开 `async with` |
| `holder cancelled` | `hold` 已离开代码块，锁已释放；等待它的主程序收到 `CancelledError` |
| `lock acquired again` | 主程序可以再次取得同一把锁 |

把两种取消位置分开理解：

| 取消时的位置 | 是否已经取得锁 | 谁处理释放 |
| --- | --- | --- |
| 等待进入 `async with lock` | 尚未取得 | 这份任务不用释放；原占用者仍负责自己的退出 |
| 已进入代码块，停在内部的 `await` | 已取得 | 先完成内部清理，离开代码块时由 `async with` 释放 |

普通异常也是离开代码块后释放锁。短实验 [failure.py](failure.py) 会先抛出 `ValueError`，由调用方接住，再成功取得同一把锁。

**自动释放不等于自动恢复数据。** 如果报错前已经改了一半字典，Lock 不会把这些修改撤销；仍要由业务决定如何保持或恢复一致的状态。本课的锁负责互斥与配对释放。

<span id="lock-takeaways"></span>

## 5. Lock：带走三条结论，以及写的时候怎么检查

1. **共用同一把锁，才能协调同一份状态。** 每份任务各建一把 Lock，或者某份任务绕开锁直接修改，都不能形成这份保护。
2. **保护范围覆盖完整的读取与修改。** 锁内 `await` 只挂起当前任务，锁仍保留；若一段操作能连续完成，就不必为了示范而人为加 `sleep(0)`。同一事件循环中的任务不会在普通连续同步代码的任意一行之间抢占切换。
3. **取得之后要配对释放，通常交给 `async with`。** 等锁时被取消和持锁后被取消是不同情况；释放锁也不等于回滚数据。

写的时候先圈出“哪些状态必须一起保持正确”，再决定锁覆盖哪几行。只保护必要范围；不需要一致性保护的慢操作尽量放在外面。若必须跨 `await` 保持这项约定，就保留锁，同时确认等待的工作不需要回来取得同一把锁，否则双方可能互等。

本课处理同一事件循环中的异步任务；跨操作系统线程的锁在第 28 课单独学习。

试着回答：

1. 只把 L10 的写回放进锁里，把 L7 的读取留在外面，还能保证总数为 2 吗？
2. A 在 L9 挂起后，B 能运行到哪里？能不能读到 `count`？
3. 一份还在等锁的任务被取消了，应不应该替占用者释放锁？

<details>
<summary>查看自查解释</summary>

1. 不能。两份任务仍可能都在加锁前读到 0，之后即使依次写回，也会都写成 1。
2. B 可以运行到 L6，尝试进入同一把锁的保护区；A 尚未释放时，B 在这里等待，还不会执行 L7。
3. 不应该。它还没有取得锁；占用者仍在使用自己的保护区。

</details>

下一课增加的问题是：**没有数据要传，也没有共享修改要互斥，只想通知其他任务“现在可以继续了”，应该用什么？** 见[第 20 课：asyncio.Event](../20-async-event/)。

{{< python-async-slime title="按需阅读：Slime 的共享更新状态与 Lock 源码" >}}

## _build_http_app / update_from_disk：同一把锁怎样交给多个请求

以下摘录固定在 Slime `2f2318653f6f794dddd321eff7c9d4b7b174643f`。已确认的本地 Slime 路径本次不可用，因此从 GitHub 的这个固定提交重新核对；文件 SHA-256 与已有快照一致。

主例子的计数是独立语义实验。真实接口 `update_from_disk(request)` 接收更新请求，使用 `model_path` 和 `update_state`，不是本课的 `increment`，也不采用人为的 `sleep(0)`。

1. **从共享对象进入。** `_build_http_app` 创建一次 `update_state` 和 `update_lock`，后续请求使用同一组对象。
2. **在锁内检查并预留状态。** `update_from_disk` 判断是否已有更新、路径是否相同，并登记本次更新。读完这一段，回到“完整的检查与修改需要哪些行一起保护”。

{{< source-reference id="source-1" >}}

3. **离开这次保护区，再处理耗时工作。** 原函数没有把整个磁盘更新都包在同一次持锁中。这里的锁内状态修改没有显式 `await`；不能把本课故意跨等待的计数实验当作原函数的逐行还原。
4. **完成后重新取得同一把锁收尾。** 原函数回到 `update_state`，登记结果并清理更新标志。这里展示职责与锁的范围；其中 Future 的具体操作留到后续课程。

{{< source-reference id="source-2" >}}

## Lock.acquire / release：本次核对的版本边界

API 语义按 [Python 3.12 官方文档](https://docs.python.org/3.12/library/asyncio-sync.html#lock)核对，示例在 Python 3.12.3 执行；也核对了本机 `asyncio/locks.py`：上下文进入等待 `acquire()`，退出调用 `release()`。锁本身不会强制识别是哪一份任务调用了释放，因此使用者必须遵守同一把锁与配对释放的约定。

## Lock：全部已统计的 Slime 使用位置

{{< python-async-coverage lesson="19-async-lock" >}}

{{< /python-async-slime >}}

---

[上一课：18 · asyncio.Queue](../07-queues/) · [返回学习路线](../learning-route/)
