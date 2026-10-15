---
title: "27 · threading.Thread：创建、启动并等待线程"
description: "如果自己创建一个工作线程，何时开始执行，又怎样确认它已经退出？"
weight: 270
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 26 课](../26-to-thread/)用 `to_thread()` 把同步函数交给工作线程执行，再用 `await` 等待结果。
>
> **本课新增的问题：** 如果自己创建一个工作线程，何时开始执行，又怎样确认它已经退出？

<span id="1-thread先创建对象再启动"></span>

## 1. Thread / worker：先分清线程对象和要做的工作

本例要做的事很具体：**让另一个线程执行 `worker(10)`，打印 `worker 10`，然后主线程确认它已经结束。** 这里先用打印代表工作内容，重点观察这份工作怎样被启动、怎样结束。

在第 26 课中，`to_thread()` 帮我们安排线程。本课直接创建一个代表工作线程的对象，通过它启动线程、等待结束、查看状态。先分清下面三个名字：

| 写法 | 它是什么，在本例中做什么 |
| --- | --- |
| `worker` | 一个普通函数，函数体规定要执行的工作：打印传入的编号 |
| `worker(10)` | 一次具体的函数调用；执行后打印 `worker 10` |
| `thread` | 一个变量，保存代表工作线程的 `Thread` 对象；通过这个对象调用 `start()`、`join()` 和 `is_alive()` |

**`worker` 决定做什么；`thread` 这个对象让我们启动那条工作线程，并等待它结束。** `thread` 是本例选择的变量名，不是 Python 关键字。

主例子中的这一行：

```python
thread = threading.Thread(target=worker, args=(10,))
```

意思是：创建一个线程对象，并记住“启动以后要执行 `worker(10)`”。`target=worker` 提供函数本身；`args=(10,)` 提供一个参数 `10`。**运行这一行时，`worker` 的函数体还没有执行；后面的 `thread.start()` 才启动工作线程。**

## 2. start / join / is_alive：观察线程的一生

[下载 example.py](example.py)，运行 `python3 example.py`。

<div class="async-coordination-code">

```python
import threading


def worker(rollout_id):
    # 工作线程启动后，实际执行的是这里的函数体。
    print("worker", rollout_id)


def main():
    # 1. 创建线程对象，记住要执行 worker(10)，此时还没启动。
    thread = threading.Thread(target=worker, args=(10,))

    # False 表示尚未启动，不是 thread 对象不能使用。
    print("before start", thread.is_alive())

    # 2. 启动工作线程，让它执行 worker(10)。
    thread.start()

    # 3. 等工作线程结束；未结束时，主线程会阻塞在这里。
    # 如果工作线程已经结束，join() 就直接返回。
    thread.join()

    # False 表示工作线程已结束；thread 对象仍然存在。
    print("after join", thread.is_alive())


if __name__ == "__main__":
    main()
```

</div>

实际输出：

```text
before start False
worker 10
after join False
```

## 3. Thread：按创建、执行、退出读

下面的 `Thread(...)`、`start()` 和 `join()` 都由主线程调用；工作线程负责执行 `worker(10)` 中的打印。

| 位置 | 发生什么 |
| --- | --- |
| `Thread(...)` | 创建对象，目标函数还没运行，第一次 `is_alive()` 为 False |
| `thread.start()` | 让新线程开始调用 `worker(10)`；主线程与它可以独立推进 |
| `thread.join()` | 阻塞调用它的主线程，等这个工作线程结束 |
| join 返回以后 | `worker` 已退出，`is_alive()` 为 False |

`join()` 等待的是“这个工作线程结束”。如果调用时它已经结束，就直接返回；如果还没结束，主线程就停在这里等待。这与第 26 课的 `await` 不同：**`join()` 等待期间会阻塞调用它的线程，不会替主线程运行其他协程。**

本例没有在 `start()` 后立刻打印存活状态：短函数可能已经执行完，不能保证那时读到 True。`start()` 也不是“等目标函数运行完”。

## 4. join：等待退出，不负责请求停止

`join()` 不会替线程发送停止请求。工作函数如果一直不返回，主线程也会一直等；第 29 课再用通知让线程合作退出。

`join(timeout=...)` 只限制这一轮等待，它返回 `None`。需要判断超时以后是否仍在运行，要再调用 `is_alive()`。同一线程对象只能启动一次；再次执行一轮工作，应另建对象。

线程函数的普通返回值不会通过 `join()` 返回。第 30 课用队列交接数据，第 31 课再用 Future 收集返回值。

<span id="5-thread带走两条结论"></span>

## 5. Thread：带走三条结论

1. `worker` 规定工作内容；`thread` 保存代表工作线程的对象，用来启动线程、等待结束和查看状态。
2. 创建对象、启动线程、目标函数结束，是三个阶段；创建对象时不会执行目标函数。
3. `join()` 等结束，`is_alive()` 看状态；两者都不是取消操作。

自查：把 `target=worker` 改成 `target=worker(10)` 会怎样？

<details><summary>查看解释</summary>

会先在当前线程调用 `worker(10)`，把它的返回值交给 target；没有把这次函数调用安排到新线程。

</details>

<details><summary>按需阅读：项目对照与标准库依据</summary>

主例子是独立标准库实验。[旧版线程与健康检查对照](../09-thread-synchronization/#thread-basics)保留已核对的项目材料；这里先学原生机制，再按需回看调用位置。

语义按 [Python 3.12 官方文档](https://docs.python.org/3.12/library/threading.html#thread-objects)和本机 Python 3.12.3 标准库核对，示例使用 Python 3.11 及以上版本。

</details>

---

[上一节：26 · asyncio.to_thread：把阻塞函数交给线程](../26-to-thread/) · [下一节：28 · threading.Lock：保护线程共享状态](../28-thread-lock/) · [返回学习路线](../learning-route/)
