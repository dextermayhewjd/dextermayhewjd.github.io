---
title: "17 · 线程池 Future 的结果与退出"
description: "沿提交、排队、完成和关闭理解线程池，区分同步 Future 与 asyncio 的等待。"
weight: 170
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 线程池已经收到工作，调用方怎样知道它结束了

第 08 节从事件循环一侧进入线程池：`await asyncio.to_thread(...)`，或者 await `loop.run_in_executor(...)`。这一节站在线程池调用方一侧：直接提交同步函数，保存它的结果句柄，决定按什么顺序收取，最后收回线程资源。

先分清三件东西：线程池管理工作线程，提交的函数在某个工作线程中执行，`concurrent.futures.Future` 表示这次提交的状态及结果。函数抛出的异常也保存在 Future 中，由收取结果的一方处理。

<span id="executor-submit-map"></span>

## submit 返回句柄，map 返回结果迭代器

```python
with ThreadPoolExecutor(max_workers=2) as executor:
    future = executor.submit(read_file, rel_path)
    result = future.result()
```

`submit(read_file, rel_path)` 安排调用 `read_file(rel_path)`，立即返回 Future；这时工作可能排队、已开始，甚至已经结束。`max_workers` 控制同时执行的工作线程数，不等于只接受这么多次提交。

若每次提交后立刻 result，调用线程会先等完这一份才提交下一份。需要并发时，应先提交多份，再收结果。提交过多又会积压参数和结果；Slime 的 delta 压缩用有限的 inflight 队列及时收取最早提交的工作。

<details><summary>源码入口：压缩工作先提交，限制在途量，finally 关闭池</summary>

{{< source-reference id="source-1" >}}

</details>

`executor.map(fn, inputs)` 适合对一组输入调用同一个函数，迭代时直接拿结果，不必自己管理每个 Future。它按**输入顺序**给出结果，后一个先完成也可能等前一个；函数异常在迭代到对应结果时重新抛出。Python 3.12 会立即收集输入并提交工作，不能把它当成自动限制在途数量的流式接口。[Executor.submit / map 文档](https://docs.python.org/3.12/library/concurrent.futures.html#executor-objects)

Slime 的探针测试用 `list(pool.map(..., _probes))` 并发检查各探针，然后收齐列表。转储工具则需要一完成就更新进度，使用后面介绍的 as_completed。

<details><summary>源码入口：并发验证各探针，收齐结果</summary>

{{< source-reference id="source-2" >}}

</details>

<span id="future-result-state"></span>

## 先理解 result，再区分“完成”和“成功”

`future.result(timeout=...)` 在线程中同步等待：成功返回值，工作抛错则重新抛出该异常，等待超时抛出 `TimeoutError`，已取消则抛出 `concurrent.futures.CancelledError`。超时只结束本次等待，工作仍可能继续。

`future.exception(timeout=...)` 同样可以等待，但返回的是异常对象；成功时返回 `None`。它也会因等待超时或取消抛出对应异常。`future.done()` 只是非阻塞查询；成功、失败、成功取消都算 done，不能把 True 读成“结果成功”。[Future 文档](https://docs.python.org/3.12/library/concurrent.futures.html#future-objects)

在 Slime 中，微批次先 `executor.submit(self._load_and_prepare)` 预取，真正需要张量时 `_get_cpu_tensor()` 才调用 `future.result()`。它先短暂取得对象自己的锁以读取指针，然后离开锁再等待，避免等待期间一直占住共享状态的锁。

<details><summary>源码入口：预取句柄，在实际消费位置收取结果</summary>

{{< source-reference id="source-3" >}}

</details>

<span id="future-cancel-callback"></span>

## 排队可以取消，开始执行后不能靠 cancel 强停

`future.cancel()` 尝试阻止尚未开始的调用，成功返回 True；正在执行或已经完成时返回 False。`running()` 表示工作已进入执行，`cancelled()` 表示成功取消。不要写“调用了 cancel，所以线程已停止”。需要停止长工作时，必须让工作函数自己检查停止信号并返回，或为 I/O 设置合理超时。

| 时刻 | Future 状态 | cancel 结果 | 谁决定工作结束 |
| --- | --- | --- | --- |
| 提交后仍排队 | 尚未运行 | 可以成功 | 执行器不再启动该调用 |
| 函数已开始 | running 为真 | False | 工作函数自己返回或抛错 |
| 函数返回或抛错 | done 为真 | False | 已结束，可取结果或异常 |
| 排队时成功取消 | cancelled 与 done 为真 | 已取消 | result 会抛 CancelledError |

Slime 的微批次 `release()` 清掉自身指针后，对尚未 done 的 Future 尝试 cancel；这只是尽力取消预取。如果预取已经运行，cancel 无法打断它。

<details><summary>源码入口：释放微批次时的尽力取消</summary>

{{< source-reference id="source-4" >}}

</details>

不想反复轮询 done，可以 `future.add_done_callback(callback)`：完成或成功取消时，回调收到这个 Future。若注册时已完成，回调会立即执行。它不会自动切到 asyncio 事件循环；回调要短小，不要假定固定线程，也不要在里面等同一线程池的其他未完成工作。`result()` 返回并不保证回调所有副作用也已完成；本节示例另用 Event 确认回调结束。

这一节补充 exception、running、cancelled 和同步 Future 的回调，帮助完整解释状态；固定版本中上述预取主线直接使用的是 submit、result、done、cancel 与 shutdown。不要把 `asyncio.Task.add_done_callback` 的出现自动计到这个 Future 类型上。

<span id="executor-wait-completed"></span>

## wait 返回集合，FIRST_COMPLETED 不保证只有一份结果

```python
done, pending = wait(futures, return_when=FIRST_COMPLETED)
```

这里的函数与常量来自 `concurrent.futures`。调用线程同步等到至少一项完成，再拿到两个集合。返回时可能已经多项完成；done 没有提交顺序，集合中的 Future 还要调用 result 才得到值。等待超时可以返回空 done，pending 中的工作也不会自动取消。

Slime 的测试把远程调用替换成 `run_coroutine_threadsafe()` 返回的同步 Future，再用 `concurrent.futures.wait(..., FIRST_COMPLETED)` 模拟 `ray.wait`。同一个对象来自跨线程协程提交，也仍然要按同步 Future 的规则收取结果。

<details><summary>源码入口：测试替身怎样模拟 ray.wait / get / cancel</summary>

{{< source-reference id="source-5" >}}

</details>

<span id="executor-as-completed"></span>

## as_completed 让调用方一份一份处理完成的 Future

`concurrent.futures.as_completed(futures)` 返回普通迭代器，每次给出一份已经结束或取消的**原 Future**；调用方用 `future.result()` 取值、处理异常，再更新进度。若开始迭代前多项已经完成，不应依赖它们之间的细微先后次序。

Slime 的并行转换工具先提交文件读取、参数转换或文件保存，再遍历 as_completed。读取先完成哪份就缓存哪份，保存先完成哪份就报告哪份，不必等待输入列表中排在前面的慢工作。

<details><summary>源码入口：并行读文件，按完成顺序进入缓存</summary>

{{< source-reference id="source-6" >}}

同一文件还在[参数转换与文件保存](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tools/convert_torch_dist_to_hf_parallel.py#L295-L340)使用同一模式。另两个 [FP8](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tools/convert_hf_to_fp8.py#L178-L188) / [INT4](https://github.com/THUDM/slime/blob/2f2318653f6f794dddd321eff7c9d4b7b174643f/tools/convert_hf_to_int4_direct.py#L224-L242) 转换入口保存提交列表后逐个 result，顺序与 as_completed 不同，但调用方都负责取异常。

</details>

<span id="executor-shutdown"></span>

## 最后关闭线程池，并等待它负责的工作

`shutdown(wait=True)` 停止接受新提交，等待已提交工作结束并释放资源。`cancel_futures=True` 额外取消还没开始的工作，正在执行的仍要结束。`wait=False` 让当前调用尽快返回，不会杀死工作线程，整个 Python 程序仍须等待这些工作退出。退出 `with ThreadPoolExecutor(...)` 相当于等待式关闭。

Slime 的微批次预取器先设 `_closed`，防止再取得它的执行器，然后 shutdown(wait=True, cancel_futures=True)，最后释放各份数据。`QueueReader.close()` 则先等专用 reader 的同步读取结束，再归还租约、停止心跳线程。两处顺序都表达资源所有权：线程还在用的资源，不能先当成空闲资源清理。

<details><summary>源码入口：预取器与 QueueReader 的关闭顺序</summary>

{{< source-reference id="source-7" >}}

{{< source-reference id="source-8" >}}

</details>

<span id="future-test-double"></span>

## 为什么测试里还会直接 Future()

业务提交通常由 executor 创建 Future。Slime 的测试也直接构造 `Future()` 模拟一个没有完成的远程请求，在清理时用 `set_result(None)` 解除它；这属于测试替身，不是在启动一条工作线程。直接构造后如果没人设置结果、设置异常或取消，它就会一直未完成。

`set_result(value)` 和 `set_exception(error)` 是执行器实现与测试设置完成状态的接口；不要对 submit 返回、正在由线程池管理的 Future 再手动设置结果。[测试专用方法说明](https://docs.python.org/3.12/library/concurrent.futures.html#concurrent.futures.Future.set_result)

<details><summary>源码入口：未完成的测试请求与 finally 清理</summary>

{{< source-reference id="source-9" >}}

</details>

## 与 asyncio 同名接口对照

| 问题 | concurrent.futures | asyncio（Python 3.12） |
| --- | --- | --- |
| 等一个结果 | Future.result 会阻塞调用线程 | await Future/Task 挂起当前任务；未完成时直接 result 会抛 InvalidStateError |
| 等一组 | wait 是同步函数，返回 Future 集合 | await asyncio.wait，返回 Task/Future 集合 |
| 按完成次序消费 | as_completed 产出原 Future，再 result | 普通迭代 asyncio.as_completed 产出要 await 的协程，不能把它当成原 Task |
| 接入事件循环 | 不能直接 await 同步 Future | 用 asyncio.wrap_future 适配，或从 run_in_executor 取得异步 Future |
| 取消 | 阻止尚未开始的函数调用 | 向任务传递取消请求，协程还要在挂起点处理并清理 |

在 `async def` 内直接调用同步 Future.result 或 concurrent.futures.wait，会阻塞事件循环线程。选择哪一套，要看自己拿到的对象以及当前运行位置，不能只看方法名。[异步 Future 对照](https://docs.python.org/3.12/library/asyncio-future.html#asyncio.Future.result)

## 运行一个不靠睡眠排序的实验

[下载 example.py](example.py)，运行 `python3 -W error example.py`。只使用标准库，推荐 Python 3.12，最低 Python 3.11。

`read_file` 沿用转换工具中的名称，但把真实磁盘读取换成 Event 挡板；这是语义实验。第一组只有一个工作线程，先确认 first 已运行，再提交 queued，所以能确定哪个无法取消、哪个还在排队。第二组有两个线程，显式先放行 fast，收取后再放行 slow。

```text
running True done False
cancel running False
cancel queued True done True
queued result CancelledError
result timeout; work still running True
result first
callback ['first']
success exception None
raised cannot read broken
stored exception ValueError
map [3, 1, 2]
first completed ['fast']
pending 1
as_completed fast
as_completed slow
shutdown finished
```

<details><summary>展开完整可运行示例</summary>

```python
"""Observe executor futures without depending on sleep or worker speed."""

import threading
from concurrent.futures import (
    FIRST_COMPLETED,
    CancelledError,
    ThreadPoolExecutor,
    as_completed,
    wait,
)


def read_file(rel_path, started, release):
    # API experiment: replace disk I/O with an explicitly controlled boundary.
    started.set()
    release.wait()
    if rel_path == "broken":
        raise ValueError("cannot read broken")
    return rel_path


def main():
    started, release, callback_done = (threading.Event() for _ in range(3))
    callback_results = []

    def on_done(future):
        callback_results.append(future.result())
        callback_done.set()

    with ThreadPoolExecutor(max_workers=1) as executor:
        running = executor.submit(read_file, "first", started, release)
        started.wait()
        queued = executor.submit(read_file, "queued", started, release)
        print("running", running.running(), "done", running.done())
        print("cancel running", running.cancel())
        print("cancel queued", queued.cancel(), "done", queued.done())
        try:
            queued.result()
        except CancelledError:
            print("queued result CancelledError")
        try:
            running.result(timeout=0)
        except TimeoutError:
            print("result timeout; work still running", running.running())

        running.add_done_callback(on_done)
        release.set()
        print("result", running.result())
        callback_done.wait()  # result() alone does not promise callback completion.
        print("callback", callback_results)
        print("success exception", running.exception())

        failed = executor.submit(read_file, "broken", started, release)
        try:
            failed.result()
        except ValueError as error:
            print("raised", str(error))
        print("stored exception", type(failed.exception()).__name__)
        print("map", list(executor.map(abs, [-3, -1, -2])))

    executor = ThreadPoolExecutor(max_workers=2)
    slow_started, fast_started = threading.Event(), threading.Event()
    slow_release, fast_release = threading.Event(), threading.Event()
    try:
        slow = executor.submit(read_file, "slow", slow_started, slow_release)
        fast = executor.submit(read_file, "fast", fast_started, fast_release)
        slow_started.wait()
        fast_started.wait()
        fast_release.set()
        done, pending = wait([slow, fast], return_when=FIRST_COMPLETED)
        print("first completed", [future.result() for future in done])
        print("pending", len(pending))

        completed = as_completed([slow, fast])
        print("as_completed", next(completed).result())
        slow_release.set()
        print("as_completed", next(completed).result())
    finally:
        # Also unblock workers if an assertion or print fails during the demo.
        slow_release.set()
        fast_release.set()
        executor.shutdown(wait=True, cancel_futures=True)
    print("shutdown finished")


if __name__ == "__main__":
    main()
```

</details>

<details><summary>复述检查</summary>

done 为真仍可能失败或已取消；result 才给出结果或重新抛错。map 保留输入顺序，as_completed 便于先处理完成项。result 的超时和 shutdown(wait=False) 都不能强停线程。在线程池工作函数内部等待同一池的后续工作，可能用尽所有工作线程而死锁。

</details>

<details><summary>书籍核对与本节判断</summary>

**书上怎么说：** as_completed 在工作完成后产出 Future。[依据 A]

**我的判断：** 本节用 Event 建立确定顺序，取消边界、回调和 shutdown 语义按 Python 3.12 文档核对；书中关于回调执行线程的描述不作为“总在原工作线程中运行”的保证。

**依据 A** · 第 20 章《并发执行器》› Where Are the Futures?，锚点 `where-are-the-futures`。英文 `corpus/en/ch20.md:246–338`，中文 `corpus/zh/ch20.md:236–323`。书籍基于 Python 3.10；本节验证环境 Python 3.12.3。

原文：“`as_completed` yields futures as they are completed.”

对照：“`as_completed` 函数在 future 对象运行结束后产出 future 对象。”

</details>

{{< python-async-coverage lesson="17-executor-results" >}}

---

[专题首页](../) · [上一节](../16-thread-coordination/) · [下一节：18 · 进程生命周期：从队列工作到超时回收](../18-process-lifecycle/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
