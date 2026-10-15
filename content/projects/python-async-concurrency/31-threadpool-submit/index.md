---
title: "31.1 · ThreadPoolExecutor / submit：把工作提交到线程池"
description: "不为每次工作手动创建线程，怎样提交多份调用并取得各自的结果？"
weight: 311
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 27 课](../27-thread-lifecycle/)用 `Thread` 启动工作、用 `join()` 等线程结束；[第 08 课](../07-task-results/)区分任务完成、返回值与异常。补充实验会复用[第 29 课](../29-thread-event/)的通知标志。
>
> **本课新增的问题：** 不为每次工作手动创建线程，怎样提交多份调用并取得各自的结果？

## 1. ThreadPoolExecutor：管理工作线程，Future 保存每次调用

本课要完成的事：**把 `get_samples(3)` 和 `get_samples(2)` 两次调用交给工作线程，再在主线程拿到两份列表。**

第 27 课已经能通过 `Thread` 安排工作。这次希望把线程的创建、复用和退出交给统一的管理者，并让每次提交的工作都有一个地方保存结果；`join()` 本身只等待线程结束，不会返回工作函数的值。

本课从标准库模块 `concurrent.futures` 导入 `ThreadPoolExecutor`。它使用的仍然是工作线程。先分清三个角色：

<div class="async-api-reference">

| 名字 | 在本课负责什么 |
| --- | --- |
| `get_samples` | 真正干活的普通函数：生成并返回样本列表 |
| `executor` | 线程池对象：接收工作，并安排池中的线程执行 |
| `first`、`second` | 两个 Future 对象：各自代表一次调用，保存完成状态、返回值或异常 |

</div>

**线程池管理线程，Future 对应每次提交的工作。** 两次提交产生两个 Future，不代表必然创建两个不同的线程；池可以复用空闲线程。

`first` 本身不是样本列表；调用 `first.result()`，才取得第一份工作的 `[0, 1, 2]`。

## 2. submit / result：先提交，再收结果

[下载 example.py](example.py)，运行 `python3 example.py`。

<div class="async-coordination-code">

```python
from concurrent.futures import ThreadPoolExecutor


def get_samples(num_samples):
    # 工作线程执行这里，返回一份样本列表。
    return list(range(num_samples))


def main():
    # 主线程创建线程池；最多使用两个工作线程，按需创建或复用。
    with ThreadPoolExecutor(max_workers=2) as executor:
        # 提交两次函数调用；first、second 各自保存一份 Future。
        first = executor.submit(get_samples, 3)
        second = executor.submit(get_samples, 2)
        # 主线程取第一份结果；未完成就阻塞等待，完成后返回列表。
        print("first", first.result())
        # 再取第二份结果；这时它可能已经完成，无需再等。
        print("second", second.result())
        # 第一份结果已经取到，因此 done() 为 True。
        print("done", first.done())
        # 第一份工作正常完成，没有保存的异常，因此返回 None。
        print("exception", first.exception())
    # 离开 with 前，线程池已等完工作并完成关闭。
    print("pool closed")


if __name__ == "__main__":
    main()
```

</div>

实际输出：

```text
first [0, 1, 2]
second [0, 1]
done True
exception None
pool closed
```

## 3. Future：完成、结果与异常怎样对应？

### 3.1. 主线程：提交工作，再等待结果

1. 创建 `executor`，`max_workers=2` 表示最多使用两个工作线程，不表示已经有两个函数在运行。
2. 两次 `submit()` 分别提交函数和参数，返回 `first`、`second`。提交时不等待函数执行完。
3. `first.result()` 等第一份调用完成并拿到列表；`second.result()` 再取得第二份列表。等待尚未完成的结果时，会阻塞这里的主线程。
4. 第一份结果已经成功取得，所以 `first.done()` 为 True，`first.exception()` 为 None。

### 3.2. 工作线程：执行函数，把结果交给对应的 Future

池中的工作线程执行 `get_samples(3)` 或 `get_samples(2)`。函数返回后，结果保存到对应的 Future，主线程才能通过 `result()` 取得它。

`result()` **不会重新运行函数**。它等待或读取那次已经提交的工作；即使主线程还没调用 `second.result()`，第二份工作也可以已经完成。本例的打印顺序由两次读取的顺序决定，不用它判断工作完成顺序。

### 3.3. with：离开前等完工作并关闭线程池

`with ThreadPoolExecutor(...)` 的退出会等待已提交工作完成并关闭池，之后才打印 `pool closed`。它沿用[第 04 课](../04-with-async-with/)的进入与退出结构；第 32 课再展开取消和退出选项。

## 4. result(timeout)：等待超时不会停止工作

这是另一个独立实验，[下载带注释的 edge_cases.py](edge_cases.py)。它额外使用两个 Event：`entered` 通知“工作已开始”，`release` 控制“现在可以返回”，从而保证检查时工作还没结束。

### 4.1. result(timeout=0)：结束这次等待，工作仍在继续

主线程等 `entered` 后，先看到 `done before release False`。此时工作线程停在 `release.wait()`；主线程再调用 `future.result(timeout=0)`，因为结果未就绪而收到 TimeoutError。

随后主线程用 `release.set()` 放行，再次调用同一份 `future.result()`，取得 10：

```text
done before release False
wait timed out
result after release 10
```

这里的超时是**抛出异常**，不是像 `Event.wait(timeout=...)` 一样返回 False；也不会停止这份工作。相关调用都在下载脚本旁写有注释。

### 4.2. result / exception：一份失败工作，两种读取方式

后半段重新提交会抛出 `ValueError` 的 `broken_read()`，得到另一个 Future，名为 `failed`：

```text
result raised read failed
stored exception ValueError
```

`failed.result()` 重新抛出工作中的 ValueError；捕获它以后，`failed.exception()` 读取已保存的异常对象。这两个方法都可能等待，不能套用 asyncio Task 未完成时读取就报 InvalidStateError 的规则。

## 5. Future：带走两条结论

1. 线程池管理工作线程；一个 `submit()` 对应一份 Future，Future 保存那次工作的状态与结果。
2. result 会等待并返回或抛错，done 只查状态，exception 取得异常对象。

自查：在协程里直接 `future.result()`，等它完成期间会怎样？

<details><summary>查看解释</summary>

会阻塞当前事件循环线程。这个 Future 不能直接当作 asyncio Task 使用；第 33–34 课再讲异步接入。

</details>

## 6. ThreadPoolExecutor / Future：本课接口速查

<div class="async-api-reference">

`ThreadPoolExecutor(max_workers=2)` 创建线程池对象；本课通过 `with` 在退出时等待工作并关闭池。

| 对象与调用 | 用途与返回 |
| --- | --- |
| `executor.submit(...)` | 提交一次函数调用，返回代表这份工作的 Future |
| `future.result(...)` | 等结果；成功返回值，失败抛出异常。指定的等待时间用完会抛 TimeoutError |
| `future.done()` | 不等待，立即返回是否结束；成功、失败或成功取消都为 True |
| `future.exception(...)` | 等完成；正常结束返回 None，失败返回异常对象；等待超时同样抛 TimeoutError |

</div>

这里的 Future 是 `concurrent.futures.Future`。它的阻塞式读取与 asyncio Task 不同；协程中的接入留给第 33–34 课。

<details><summary>按需阅读：项目对照与标准库依据</summary>

主例子是独立标准库实验。[旧版 Future 与固定源码位置](../17-executor-results/#future-result-state)保留已核对的项目材料；这里先学原生机制，再按需回看调用位置。

语义按 [Python 3.12 官方文档](https://docs.python.org/3.12/library/concurrent.futures.html#future-objects)和本机 Python 3.12.3 标准库核对，示例使用 Python 3.11 及以上版本。

</details>

---

[上一已读课：29 · threading.Event](../29-thread-event/) · [本课配套：31.2 · ThreadPoolExecutor.map](../31-threadpool-map/) · [重点续学路线](../learning-route/#priority-reading)
