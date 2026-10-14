---
title: "10 · 线程池：把阻塞工作移出事件循环"
description: "理解 to_thread、run_in_executor 与两类 Future 的边界。"
weight: 100
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

<span id="thread-offload"></span>

## 异步函数里调用同步函数，会发生什么

如果这个同步函数正在读磁盘、等待同步网络请求或做耗时处理，事件循环的线程会被它占住。把外层函数写成 `async def`，不会自动改变内部同步调用的执行位置。

先用下面的实验比较两种交接方式。为了专注接口，`get_samples()` 只生成列表；真实 Slime 在同一位置进行阻塞式读取。

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

def get_samples(num_samples):
    return list(range(num_samples))

async def get_samples_async(reader, num_samples):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(reader, get_samples, num_samples)

async def exercise(reader):
    print("to_thread", await asyncio.to_thread(get_samples, 3))
    print("reader", await get_samples_async(reader, 3))

if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=1) as reader:
        asyncio.run(exercise(reader))
```

[下载并运行本节 example.py](example.py)。只使用 Python 标准库；推荐 Python 3.12，最低 Python 3.11。

运行结果：

```text
to_thread [0, 1, 2]
reader [0, 1, 2]
```

`to_thread()` 使用默认线程池执行同步函数。`run_in_executor(reader, ...)` 把工作交给明确传入的执行器。等待者都可以用 `await` 拿结果。

## 不要把取消理解成“杀掉线程”

取消等待者，不会强行停止已经开始的线程函数。

线程适合哪些工作，还取决于函数是否等待 I/O、是否释放 GIL，以及运行的 Python 实现。不要只凭“用了线程”就断言纯 Python 计算会多核加速。

<details><summary>复述检查</summary>

事件循环线程负责安排和等待；reader 的工作线程执行同步函数。`await` 挂起的是等待者，执行位置由 `to_thread` 或 executor 交接决定。

</details>

语义核对：[to_thread](https://docs.python.org/3.12/library/asyncio-task.html#running-in-threads)、[concurrent.futures](https://docs.python.org/3.12/library/concurrent.futures.html)。

{{< python-async-slime >}}

## Slime 为什么需要专用 reader

`QueueReader` 创建只有一个工作线程的 reader，再由 `get_samples_async()` 把同步 `get_samples()` 交给它。这样可以保持读取顺序，也不让读取直接占据事件循环线程。

<details>
<summary>展开 Slime 源码：QueueReader.__init__</summary>

{{< source-reference id="source-1" >}}

</details>

<details>
<summary>展开 Slime 源码：QueueReader.get_samples_async</summary>

{{< source-reference id="source-2" >}}

</details>

<details>
<summary>展开 Slime 源码：run_rollout_io</summary>

{{< source-reference id="source-3" >}}

</details>

Slime 的 `run_rollout_io()` 会继续等待已经接受的写入完成，再传播取消或写入异常。这是结果所有权和文件完整性问题，不能靠多加一个 `await` 解决。

{{< python-async-coverage lesson="08-executors" >}}

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节](../07-queues/) · [下一节：11 · Lock、Event 与线程退出](../09-thread-synchronization/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
