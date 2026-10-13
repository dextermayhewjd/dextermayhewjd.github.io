---
title: "13 · Future、回调与跨线程事件循环"
description: "从待完成结果走到事件循环的启动、跨线程提交与收尾。"
weight: 130
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

<span id="future-basics"></span>
## await future 到底在等谁

前面已经用 Task 管理协程；这一节向下一层看 Future。Future 保存一个尚未完成的结果，回调或其他生产者把结果写进去，等待者才能继续。它本身不会启动一个 worker。

保留这个最小实验：

```python
import asyncio

async def wait():
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    loop.call_soon(future.set_result, 7)
    return await future

async def exercise():
    print("value", await wait())

if __name__ == "__main__":
    asyncio.run(exercise())
```

[下载 example.py](example.py)，执行 `python3 -W error example.py`，输出仍是 `value 7`。本章使用 Python 标准库；推荐 Python 3.12，最低 Python 3.11。

这里先取当前线程正在运行的 loop，再由 `loop.create_future()` 创建属于它的 Future。`call_soon` 登记普通回调；当当前执行让出控制权，loop 才有机会调用 `future.set_result(7)`，随后等待者从 `await future` 取到 `7`。

<span id="pacer-callbacks"></span>
## 回到 Slime：分批完成 Future

阅读主线是“请求进入 `AsyncPacer.wait()` → 排队等待 → `_release()` 完成结果 → 请求继续”。这里第一次完整展开 `AsyncPacer`，不依赖第 2 节存在它的示例。

`wait()` 把 Future 加入 `pending`；第一次入队时用 `loop.call_soon(self._release)` 安排释放。`_release()` 最多取出 64 个，检查 `future.done()`，对尚未结束的 Future 调用 `set_result(None)`。剩余队列通过 `loop.call_later(0.001, self._release)` 等下一批；这个延迟给 socket 和其他计时回调留下运行机会。它没有等待上一批业务结束，因此控制的是唤醒节奏，并非第 6 节 Semaphore 的在途任务上限。

| 操作 | 输入、结果与约束 |
| --- | --- |
| `loop.call_soon(callback, *args)` | 在后续一轮执行普通回调；当前 loop 线程内使用，不接收一个需要自动 await 的协程函数 |
| `loop.call_later(delay, callback, *args)` | 延迟至少接近指定秒数再安排回调；依赖单调时钟，不承诺精确执行时间 |
| `Future.done()` | 成功、失败或取消都算完成，不能据此断言成功 |
| `Future.set_result(value)` | 成功完成；已完成的 Future 再写会抛 `asyncio.InvalidStateError` |
| `Future.set_exception(error)` | 失败完成；等待者在 `await` 处收到异常，需要读取和处理 |
| `Future.cancel()` | 把尚未完成的 Future 标成取消，唤醒等待者；已结束时不能重新取消 |
| `Future.add_done_callback(fn)` | 完成后由 loop 调用 `fn(future)`；已完成也会排入回调，不在注册语句中直接内联执行 |

`_flush_rebuffers()` 给出失败分支：后台 `add_samples` 成功就 `future.set_result(None)`，异常就 `future.set_exception(error)`。Future 连接了“批处理生产者”与“各请求等待者”；它没有替生产者执行写入。

<details><summary>展开固定源码：排队、分批唤醒与失败完成</summary>

{{< source-reference id="source-1" >}}

{{< source-reference id="source-6" >}}

</details>

<span id="event-loop-lifecycle"></span>
## 谁创建 loop，谁让它运行

现在沿 `get_async_loop() → AsyncLoopThread → _start_loop() → run(coro)` 进入后台线程。输入是调用方要执行的协程，输出是它的结果或异常。

1. 构造函数用 `asyncio.new_event_loop()` **创建对象**，此时 loop 尚未运行。
2. 新线程中的 `asyncio.set_event_loop(self.loop)` 把它登记为该线程的当前 loop；登记也不等于启动。
3. `loop.run_forever()` 驱动 Task、I/O 和回调，持续运行到收到 `loop.stop()`。
4. 调用方用 `asyncio.run_coroutine_threadsafe(coro, loop)` 提交，得到 `concurrent.futures.Future`。这里的同步 `.result()` 阻塞调用方线程；目标 loop 必须还能运行。

`run_app_in_thread._run()` 是另一种真实顺序：先两次 `loop.run_until_complete(...)` 完成 runner setup 和监听启动，再进入 `run_forever()`。前者运行到指定等待对象完成并返回结果，后者没有预定业务完成点。不能在已经运行的同一个 loop 中嵌套调用这些运行入口。

`_GenerationActor.start()` 已经在异步调用方内，于是用 `await asyncio.wrap_future(future)` 等待跨线程提交结果。不要在目标 loop 的线程里同步 `.result()`；目标线程一旦被堵住，要等待的工作也失去推进机会。

<details><summary>展开固定源码：创建、启动和跨线程等待</summary>

{{< source-reference id="source-2" >}}

{{< source-reference id="source-5" >}}

{{< source-reference id="source-3" >}}

</details>

<span id="loop-shutdown"></span>
## 先完成业务收尾，再 stop 和 close

`AppHandle.stop()` 先提交 `runner.cleanup()` 并等待，再用 `loop.call_soon_threadsafe(loop.stop)` 让目标线程执行停止。`call_soon_threadsafe` 接收普通回调，供其他线程安全入队；不要用非线程安全的 `call_soon` 代替。已关闭的 loop 不能继续接受提交。

| 操作 | 负责什么 | 不负责什么 |
| --- | --- | --- |
| `loop.is_running()` | 观察 loop 是否正在运行 | 不证明任意业务已完成，也不是跨线程关闭协议 |
| `loop.stop()` | 当前批次回调跑完后退出运行入口 | 不取消所有 Task、不关闭业务连接；当前回调新增的回调可能留待再次运行 |
| `await loop.shutdown_default_executor()` | 等默认 executor 的线程工作结束 | 不等于关闭整个 loop；关闭后不能继续使用它的默认 executor |
| `loop.close()` | 释放 loop 持有的资源，丢弃剩余回调 | 必须先停止运行；不能代替等待任务完成，关闭不可逆 |

`_GenerationActor._close()` 先取消并等待 producer，再等 `_rebuffer_task`，最后 `await ...shutdown_default_executor()`，随后才关闭 `data_source`。理由就在源码注释：第 8 节见过，取消 `to_thread` 的等待者不代表同步写入线程已经结束；先关闭文件可能撞上仍在执行的写入。Python 3.12 给 `shutdown_default_executor` 增加了 `timeout` 参数；示例不依赖此参数，因此仍能在 3.11 运行。`asyncio.run()` 自己管理的 loop 会自动关闭默认 executor，不应重复调用这段手动流程。

原版 `AsyncLoopThread` 只有创建和运行，`AppHandle.stop()` 也没有 `loop.close()`；不能把下面教学版的完整关闭写成 Slime 已实现的行为。

<details><summary>展开固定源码：跨线程停止和关闭前的 executor 排空</summary>

{{< source-reference id="source-4" >}}

{{< source-reference id="source-7" >}}

</details>

<span id="task-inspection"></span>
## 任务身份、所属 loop 与完成后的读取

再回到业务主线：`BaseAdapter._run_turn()` 通过 `asyncio.current_task()` 取得承载本次请求的 Task，并登记进 session 的在途集合。清理 session 时先筛掉 `done()` 的任务，再从 `tasks[0].get_loop()` 取回它们实际所属的 loop，把 `_drain()` 提交过去。这是执行归属问题，不是全局寻找“任意可用 loop”。

`asyncio.current_task()` 默认查询当前运行 loop；普通 loop 回调未必处于 Task 内，因此可能返回 `None`。`asyncio.all_tasks()` 默认返回当前 loop 的**尚未完成**任务集合，包含调用它的当前任务；它不是全进程、全线程任务清单。Slime 的 `_log_timeout_diagnostic()` 使用它输出超时现场，没有用诊断操作来取消所有任务。源码再筛 `not t.done()` 是防御式检查。

| `asyncio.Task` 方法 | 何时用、会发生什么 |
| --- | --- |
| `done()` | 判断协程已返回、抛错或结束取消；它本身不会等待 |
| `result()` | 仅在完成后读取；成功返回值，失败重抛异常，已取消抛 `CancelledError`，未完成抛 `InvalidStateError` |
| `exception()` | 完成后读取失败对象；成功为 `None`，已取消仍抛 `CancelledError`，未完成仍抛 `InvalidStateError` |
| `cancel()` | 请求在协程下一次恢复时注入取消；返回并不保证任务已结束，随后仍须等待清理 |
| `cancelled()` | 判断 Task 是否最终以取消结束；协程若抑制取消可能为假 |
| `get_loop()` | 取所属 loop；不能借此把 Task 任意移动到另一个 loop |
| `add_done_callback(fn)` | 注册 `fn(task)`；供框架完成收集和记账，回调内可安全读取完成结果，也仍须处理失败与取消 |

Task 从 Future 继承许多读取接口，但不允许外部 `set_result` / `set_exception` 改写它的执行结果。与 `concurrent.futures.Future.result(timeout=...)` 不同，`asyncio.Task.result()` 和 `asyncio.Future.result()` 不会阻塞等到完成。

`AsyncRolloutWorker._loop()` 创建任务后注册 `_make_done_cb(gid)`；回调读 `done_task.result()`，分别处理取消、异常和正常结果。主循环另用 `done()` 收割已结束任务。先前第 5 节的“取消后等待”在这里变成了有明确归属和错误分支的收尾代码。

<details><summary>展开固定源码：身份登记、跨 loop 排空、诊断与回调</summary>

{{< source-reference id="source-9" >}}

{{< source-reference id="source-8" >}}

{{< source-reference id="source-10" >}}

{{< source-reference id="source-11" >}}

{{< source-reference id="source-12" >}}

{{< source-reference id="source-13" >}}

</details>

<span id="lifecycle-lab"></span>
## 第二个实验：观察完整生命周期

[下载 lifecycle.py](lifecycle.py)，执行 `python3 -W error lifecycle.py`。它保留真实类名、入口和跨线程提交；教学扩展只增加显式关闭，在 loop 所在线程的 `finally` 中用 `run_until_complete` 排空异步生成器与默认 executor，再 `close`。`shutdown_asyncgens()` 是手动 loop 的兜底收尾；业务仍应自己及时关闭生成器。

<details><summary>展开完整实验：lifecycle.py</summary>

```python
"""Teaching extension of Slime's AsyncLoopThread; stdlib only."""
import asyncio
import threading


class AsyncLoopThread:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._start_loop, daemon=True)
        self._thread.start()

    def _start_loop(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_forever()
        finally:
            # Teaching addition: Slime's original class has no close method.
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.run_until_complete(self.loop.shutdown_default_executor())
            self.loop.close()
            asyncio.set_event_loop(None)

    def run(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result()

    def close(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self._thread.join()


async def exercise():
    loop = asyncio.get_running_loop()
    current = asyncio.current_task()
    print('loop running', loop.is_running())
    print('current registered', current in asyncio.all_tasks())

    completed = []
    future = loop.create_future()
    future.add_done_callback(lambda done: completed.append(done.result()))
    loop.call_soon(future.set_result, 7)
    print('future result', await future)
    print('future callback', completed)

    failed = loop.create_future()
    loop.call_later(0, failed.set_exception, ValueError('bad value'))
    try:
        await failed
    except ValueError as error:
        print('future error', str(error))

    cancelled = loop.create_future()
    cancelled.cancel()
    print('future cancelled', cancelled.cancelled(), cancelled.done())

    task = asyncio.create_task(asyncio.sleep(0, result=9))
    await task
    print('task state', task.done(), task.result(), task.exception())
    print('task loop', task.get_loop() is loop)

    pending = asyncio.create_task(asyncio.sleep(60))
    pending.cancel()
    try:
        await pending
    except asyncio.CancelledError:
        print('task cancelled', pending.cancelled(), pending.done())


if __name__ == '__main__':
    worker = AsyncLoopThread()
    try:
        worker.run(exercise())
    finally:
        worker.close()
    print('thread stopped', not worker._thread.is_alive())
```

</details>

```text
loop running True
current registered True
future result 7
future callback [7]
future error bad value
future cancelled True True
task state True 9 None
task loop True
task cancelled True True
thread stopped True
```

阅读实验时按三段定位：`exercise()` 完成 Future/Task 演示 → 主线程请求 `stop` → 目标线程完成清理并退出。真实服务如果仍有业务任务，必须先取消或等完它们，再走最后两步；这个实验在 `run(exercise())` 返回时已没有遗留业务任务。

<details><summary>语言依据与版本边界</summary>

**书上怎么说**：`await` 的对象必须提供可等待行为；Future 属于低层等待对象。

**我的判断（本书未覆盖）**：这里的生产者/等待者交接与 Slime 对照来自上述固定源码；loop 关闭、Task 方法和 Python 3.12 的细节按官方文档核对。

**依据 A**：《Fluent Python, 2nd Edition》（2022），第 21 章 New Concept: Awaitable。英文 `corpus/en/ch21.md:203–228`，中文 `corpus/zh/ch21.md:166–187`，同一锚点 `new-concept-awaitable`。本书基于 Python 3.10；本次验证解释器 Python 3.12.3。

原文：“The `for` keyword works with iterables. The `await` keyword works with awaitables.”

对照：“`for` 关键字处理可迭代对象，`await` 关键字处理可异步调用对象。”

</details>

语义核对：[事件循环生命周期与回调](https://docs.python.org/3.12/library/asyncio-eventloop.html)、[Future](https://docs.python.org/3.12/library/asyncio-future.html)、[Task 与跨线程提交](https://docs.python.org/3.12/library/asyncio-task.html)。

{{< python-async-coverage lesson="13-event-loop" >}}

---

[专题首页](../) · [上一节](../12-processes/) · [下一节：14 · 回到 Slime：串起创建、等待与清理](../14-slime-walkthrough/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
