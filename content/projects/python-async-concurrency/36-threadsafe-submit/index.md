---
title: "36.2 · asyncio.run_coroutine_threadsafe：从另一个线程提交协程"
description: "工作线程提交协程，事件循环执行，再把结果交回工作线程。"
weight: 362
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 26 课](../26-to-thread/)用 to_thread 把普通函数交给工作线程；[第 31 课](../31-threadpool-submit/)用 Future.result() 等待线程工作的结果；[36.1](../36-manual-event-loop/)分清循环的创建与运行。
>
> **本节新增的需求：** 现在普通函数已经在工作线程里，却需要让一个协程在原来的事件循环中执行，并取回结果。
>
> **本节的解决方式：** 用 run_coroutine_threadsafe 把协程对象提交给指定循环，再通过返回的 Future 取得结果。

## 1. run_coroutine_threadsafe：把协程交给指定的循环

先看清两个方向：

<div class="async-api-reference">

| 本例的操作 | 工作交给谁 |
| --- | --- |
| await asyncio.to_thread(submit, loop) | 主线程把普通函数 submit 交给工作线程 |
| asyncio.run_coroutine_threadsafe(generate(), loop) | 工作线程把协程交回主线程的 loop |

</div>

**提交的方向相反，但使用的是同一个 loop。** 新接口不会创建事件循环；它负责把协程安全地交给另一个线程中的循环。

## 2. to_thread / run_coroutine_threadsafe：用一个例子走完往返

这是独立的标准库实验。循环由 asyncio.run 管理，只增加一次跨线程提交。

[下载 example.py](example.py)，运行 `python3 -W error example.py`。

<div class="async-coordination-code">

```python
import asyncio


async def generate():
    print("loop: generate")  # 在主线程的事件循环中执行。
    return 7


def submit(loop):
    # 在工作线程创建协程对象，再交给主线程的循环运行。
    future = asyncio.run_coroutine_threadsafe(generate(), loop)
    value = future.result()  # 未完成时，当前工作线程在这里等待结果。
    print("worker: received", value)
    return value


async def exercise():
    loop = asyncio.get_running_loop()  # 取得主线程已经运行的循环。
    print("main: wait worker")
    value = await asyncio.to_thread(submit, loop)  # exercise 等待；循环仍能运行 generate。
    print("main: received", value)


if __name__ == "__main__":
    asyncio.run(exercise())
```

</div>

实际输出：

```text
main: wait worker
loop: generate
worker: received 7
main: received 7
```

generate() 在工作线程中**创建协程对象**，函数体随后由主线程的循环执行。调用的位置和函数体运行的位置，在这里分开了。

## 3. await / result：谁在等待，谁还能继续？

<span id="threadsafe-flow"></span>

从上往下读，L 对应主例子的行号。每行只记录一边的动作：

```text
# 步骤 | MAIN：主线程的循环           | WORKER：工作线程
# -----|------------------------------|---------------------------
# T01  | L18-20 交出 submit，等待返回  |
# T02  |                              | L11 提交 generate()
# T03  | L5-6 执行 generate，返回 7    |
# T04  |                              | L12 result() 取得 7
# T05  |                              | L13-14 打印，再返回 7
# T06  | L20-21 await 结束，打印结果   |
```

两处等待分别是：

1. **主线程的 exercise 在 L20 等 submit 返回。** 挂起的是这份协程，循环仍在运行，因此能接到并执行 generate。
2. **工作线程在 L12 等 generate 的结果。** 如果结果尚未准备好，result() 就阻塞当前工作线程；结果已经准备好时，它直接返回。

L12 开始等待与 L5 开始执行的先后不固定，所以图中只标出 result() **取得结果**的位置。固定的关系是：generate 先返回 7，result() 才能取得 7；submit 返回后，exercise 才能继续。

**这里没有互相卡住：工作线程等结果时，负责产生结果的主线程循环还能推进。** 如果在运行这个 loop 的线程里调用 result() 等它自己的未完成工作，循环就会被阻塞，无法执行那份工作。

## 4. Future：返回给提交方的是哪一种对象？

<span id="threadsafe-submit"></span>

run_coroutine_threadsafe 的两个参数是 **协程对象 generate()** 和 **目标循环 loop**。它返回 **concurrent.futures.Future**，也就是第 31 课认识的那一类 Future；虽然工作内容是协程，返回对象仍采用同步线程的等待方式。

循环内会把协程安排为 Task。提交方拿到的 future 用来取得这份工作的结果，**不是那个 Task 本身**。本例中的 7 沿这条路径交回：generate → future.result() → submit → await to_thread。

如果 generate 抛出异常，future.result() 会重新抛出该异常；它继续离开 submit 时，exercise 的 await 也会收到异常。当前先理解正常的结果交接，不额外加入取消流程。

## 5. call_soon_threadsafe：跨线程安排一个普通回调

读 Slime 的停止流程时，还会遇到这个配套接口：

<div class="async-api-reference">

| 要交给循环的东西 | 使用的接口 |
| --- | --- |
| 协程对象，例如 generate() | asyncio.run_coroutine_threadsafe(coro, loop) |
| 普通函数，例如 loop.stop | loop.call_soon_threadsafe(callback) |

</div>

例如 `loop.call_soon_threadsafe(loop.stop)`，意思是**通知该循环稍后执行 stop**。传入的是函数 loop.stop，没有括号；它不会在提交线程里立即调用 stop，也不返回用于读取协程结果的 Future。

## 6. run_coroutine_threadsafe：带走三条结论

1. 它从另一个线程，把协程对象交给指定循环执行；不会另建一个循环。
2. 返回 concurrent.futures.Future，result() 等待时阻塞调用它的线程。
3. 等待结果的线程可以停下来，但负责执行协程的循环线程必须能继续运行。

自查：generate 的函数体在哪个线程执行？如果把 submit(loop) 改成在 exercise 中直接调用，为什么会卡住？

<details><summary>查看解释</summary>

generate 在主线程的 loop 中执行。直接调用 submit 会让主线程走到 result() 并等待，而 generate 也要靠这个主线程的循环执行，因此双方无法继续。

</details>

{{< python-async-slime title="按需阅读：Slime 中的后台循环与停止通知" >}}

以下来自 Slime 固定教学快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f`，不是实时工作区。主例子只用标准库演示交接，没有复现后台服务。

{{< source-reference id="source-1" >}}

这里的 AsyncLoopThread 在后台线程中运行 loop，调用 run 的线程通过 result() 等待。因此交接方向取决于循环在哪里：**主例子是工作线程 → 主线程循环；这段源码是调用线程 → 后台线程循环。** 接口的职责相同。

{{< source-reference id="source-2" >}}

这里先提交异步清理 _shutdown()，再用 call_soon_threadsafe 安排普通方法 loop.stop，最后 join 等待后台线程退出。result(timeout=10) 的超时只限制这次同步等待，不会自动取消协程；源码中的 except 是该项目的处理，不能据此推导出所有清理异常都应该忽略。

{{< python-async-coverage lesson="36-threadsafe-submit" >}}

依据：[Python 3.12：从其他线程提交协程](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.run_coroutine_threadsafe)、[跨线程安排回调](https://docs.python.org/3.12/library/asyncio-eventloop.html#asyncio.loop.call_soon_threadsafe)。主例子在 Python 3.12.3 下运行，适用本教程 Python 3.11 及以上版本。

{{< /python-async-slime >}}

---

[上一节：36.1 · 手动管理事件循环](../36-manual-event-loop/) · [后续：沿源码短补回调调度](../learning-route/#priority-reading) · [API 调用统计](../api-frequency/)
