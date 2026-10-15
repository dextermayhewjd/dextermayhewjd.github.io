---
title: "32 · Future.cancel / Executor.shutdown：结束线程池并处理未执行工作"
description: "线程池已收到的工作，哪些还能取消，关闭池时又会等待什么？"
weight: 320
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
hideInProjectNav: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 09 课](../09-task-cancellation/)学过 Task 的取消请求；[31.1](../31-threadpool-submit/)建立了线程池与执行器 Future。
>
> **本课新增的问题：** 线程池已收到的工作，哪些还能取消，关闭池时又会等待什么？

## 1. Future.cancel：分清正在运行与尚未开始

本例池里只有一个工作线程。先用 Event 确认第一份调用正在运行，让它等 release；此时再提交的第二份只能排队。

## 2. cancel / shutdown：取消排队工作，再等运行中工作结束

[下载 example.py](example.py)，运行 `python3 example.py`。

<div class="async-coordination-code">

```python
from concurrent.futures import CancelledError, ThreadPoolExecutor
import threading


def get_samples(num_samples, entered, release):
    entered.set()
    release.wait()
    return list(range(num_samples))


def main():
    entered = threading.Event()
    release = threading.Event()
    executor = ThreadPoolExecutor(max_workers=1)
    try:
        running = executor.submit(get_samples, 3, entered, release)
        entered.wait()
        queued = executor.submit(get_samples, 2, entered, release)
        print("cancel running", running.cancel())
        print("cancel queued", queued.cancel())
        try:
            queued.result()
        except CancelledError:
            print("queued result cancelled")
    finally:
        release.set()
        executor.shutdown(wait=True)
    print("running result", running.result())
    print("pool closed")


if __name__ == "__main__":
    main()
```

</div>

实际输出：

```text
cancel running False
cancel queued True
queued result cancelled
running result [0, 1, 2]
pool closed
```

## 3. cancel：为什么一次 False，一次 True？

1. running 已开始，`running.cancel()` 返回 False，不会把它的线程强制停止。
2. queued 尚未开始，`queued.cancel()` 返回 True；随后 result 抛 `concurrent.futures.CancelledError`，它不会返回样本。
3. finally 设置 release，让运行中的函数自己返回，再调用 `shutdown(wait=True)` 等待线程池收尾。
4. shutdown 返回后，仍可从 running 读取保存好的结果。

这与 `asyncio.Task.cancel()` 的请求机制不同：执行器 Future 的 cancel 主要阻止尚未开始的调用；已经执行中的同步函数不会收到 asyncio 的 CancelledError。

## 4. shutdown：是否等待，与是否取消排队工作，是两个选项

[运行 cancel_pending.py](cancel_pending.py)：

```text
running done False
queued result cancelled
running result [0, 1, 2]
cleanup finished
```

| 选项 | 本例中的含义 |
| --- | --- |
| `wait=False` | 此次 shutdown 不等运行中工作结束，running 仍是未完成 |
| `cancel_futures=True` | 取消尚未开始的 queued；不强停正在运行的 running |
| 后续 `shutdown(wait=True)` | release 已设置，再等待正在运行的工作与线程资源真正收尾 |

关闭以后不能继续 submit。`wait=False` 也不保证整个 Python 程序立刻退出；运行中的线程工作仍需要结束。常规使用可优先用 with 自动等待退出；需要控制排队取消时，再显式安排 shutdown。

## 5. cancel / shutdown：带走两条结论

1. Future.cancel 成功，说明这次尚未开始的调用被取消；失败不能解释为工作已经结束。
2. shutdown 的 wait 管等待，cancel_futures 管未开始的工作；运行中工作仍要自行结束。

自查：为什么 `shutdown(wait=True)` 之前必须先让本例的 release 变真？

<details><summary>查看解释</summary>

工作线程正在等 release；若主线程一直等它退出，却不给它继续的条件，两边会一直等待。

</details>

<details><summary>按需阅读：项目对照与标准库依据</summary>

主例子是独立标准库实验。[旧版 Future 取消与线程池退出对照](../17-executor-results/#future-cancel-callback)保留已核对的项目材料；这里先学原生机制，再按需回看调用位置。

语义按 [Python 3.12 官方文档](https://docs.python.org/3.12/library/concurrent.futures.html#concurrent.futures.Executor.shutdown)和本机 Python 3.12.3 标准库核对，示例使用 Python 3.11 及以上版本。

</details>

---

[上一节：31.2 · ThreadPoolExecutor.map：批量提交并按输入顺序取结果](../31-threadpool-map/) · [下一节：33–36 · 线程与事件循环交接规划](../learning-route/#curriculum-stage-bridges) · [返回学习路线](../learning-route/)
