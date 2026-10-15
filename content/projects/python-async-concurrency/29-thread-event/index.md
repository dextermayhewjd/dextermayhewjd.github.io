---
title: "29 · threading.Event：通知线程合作退出"
description: "主线程已经不需要工作继续，怎样通知工作线程，并等它完成收尾？"
weight: 290
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 27 课](../27-thread-lifecycle/)用 `Thread` 启动工作线程，用 `join()` 等它结束；[第 20 课](../20-async-event/)用通知标志协调等待者。
>
> **本课新增的问题：** 工作线程还没有结束，主线程怎样告诉它“可以收尾退出了”，再确认它已经结束？

## 1. Event：通知与等退出各做一件事

### 1.1. Thread.join：已经能等结束，还缺什么？

例如，主程序使用一条后台监控线程。主程序准备结束时，希望后台线程先收尾，再退出。本课把监控业务省略，只保留“待命 → 收到通知 → 收尾退出”，看清这个过程。

第 27 课的 `worker` 打印完就自行结束；本课的 `worker` 要等到主线程允许退出。如果主线程直接 `join()`，它只是在等，不会告诉 `worker` 该退出了。

**本课要完成的事：主线程发出退出通知，工作线程收到后自己结束，主线程再确认结束。**

### 1.2. threading.Thread / threading.Event：一个管理线程，一个传递通知

`threading` 是 Python 标准库中的一个**模块名**，提供管理线程、传递通知等工具。先分清这些名字：

| 名字 | 怎么创建，在本例中负责什么 |
| --- | --- |
| `thread` | 由 `threading.Thread(...)` 创建的线程对象，用来启动线程、等待结束 |
| `stop` | 由 `threading.Event()` 创建的通知对象；主线程发通知，工作线程等通知 |
| `worker` | 工作线程实际运行的函数；收到 `stop` 的通知后收尾并返回 |

`Thread` 和 `Event` 都由 `threading` 模块提供，但负责不同的事。**通知对象不会自动绑定某条线程。** 我们通过 `args=(stop,)` 把它交给 `worker`，让主线程和工作线程使用同一个通知对象。

## 2. Thread / Event：把退出通知交给工作线程

本例只观察退出过程，所以主线程启动工作线程后就立即请求退出。实际程序可以在需要结束后台工作时，再执行 `stop.set()`。

[下载 example.py](example.py)，运行 `python3 example.py`。

<div class="async-coordination-code">

```python
import threading


def worker(stop):
    # 工作线程：等待主线程发出退出通知。
    # 如果通知已经发出，这里会直接继续。
    stop.wait()
    # 收到通知后收尾；函数返回，这条工作线程就结束。
    print("worker cleanup")


def main():
    # 主线程执行这里：启动工作线程、通知退出，再等它结束。
    # 1. 创建通知对象；此时标志为 False，还没有退出通知。
    stop = threading.Event()
    # 2. 创建线程对象，把同一个 stop 交给 worker 使用。
    thread = threading.Thread(
        target=worker,
        args=(stop,),
    )
    thread.start()  # 启动工作线程，执行 worker(stop)。

    # 3. 主线程决定结束后台工作，设置退出通知。
    print("main requests stop")
    stop.set()  # 标志变为 True，允许 stop.wait() 返回。

    # 4. 等工作线程收尾并结束，主线程才继续往下走。
    thread.join()
    print("joined", thread.is_alive())  # False：工作线程已经结束。


if __name__ == "__main__":
    main()
```

</div>

实际输出：

```text
main requests stop
worker cleanup
joined False
```

<span id="2-set--wait--clear先通知再等待退出"></span>
<span id="3-event沿输出读四个交接"></span>
<span id="3-set--wait--join每一步为什么要做"></span>

## 3. Thread / Event：主线程与工作线程各做什么？

这一节继续解释上面的 **`example.py`**：`main()` 在主线程执行，`worker(stop)` 在工作线程执行。两边共用同一个 `stop`，通过它传递退出通知。

### 3.1. 主线程：start 启动，set 通知，join 等结束

1. `thread.start()`：让工作线程开始执行 `worker(stop)`。
2. `stop.set()`：把共享通知标志改为 True，告诉工作线程“可以收尾退出了”。这一步不等待收尾完成。
3. `thread.join()`：等工作线程真正结束，然后读取 `thread.is_alive()`，打印 `joined False`。

### 3.2. 工作线程：wait 等通知，函数返回后结束

工作线程执行的是 `worker(stop)`：先在 `stop.wait()` 等退出通知，再打印 `worker cleanup`，随后函数返回，工作线程结束。**这里的 `wait()` 是在等主线程发通知，不是为了打印或检查状态。**

如果通知尚未发出，`wait()` 会阻塞工作线程；主线程仍可继续执行 `set()`。如果主线程已经先调用了 `set()`，标志会保留为 True，工作线程之后到达 `wait()` 时直接返回。

`stop` 的“退出通知”含义是本例的约定。Event 保存通知，`worker` 根据通知决定返回；`set()` 不会直接终止线程。这里的线程等待方式也不同于第 20 课的 `await asyncio.Event.wait()`。

**到这里，主例子的线程协作与退出已经讲完。下一节换一个独立实验，只观察通知标志怎样变化。**

<span id="4-eventclear--waittimeout另外观察通知标志的重置"></span>

## 4. Event.clear / wait(timeout=0)：独立实验，修改并观察通知标志

这一节单独运行 **`reset_flag.py`**，不是接着执行前面的 `example.py`。所有操作都由这个脚本的主线程完成，不创建工作线程。

前面已经看到 `set()` 发出通知。现在只回答一个新问题：**怎样把通知标志重新改为 False，并验证它确实变了？**

这里新建的对象叫 `event`，与上个实验的 `stop` 不是同一份对象。[下载 reset_flag.py](reset_flag.py)，核心步骤是：

<div class="async-coordination-code">

```python
# 独立实验：下面全部由主线程执行，不创建工作线程。
event = threading.Event()  # 新建通知对象，初始标志为 False。
event.set()  # 修改标志：设为 True。
# timeout=0 表示不花时间等待；已有通知，立即返回 True。
print("after set", event.wait(timeout=0))
event.clear()  # 修改标志：恢复为 False。
# 现在没有通知，等待时间又为零，立即超时并返回 False。
print("after clear", event.wait(timeout=0))
```

</div>

实际输出：

```text
after set True
after clear False
```

这里要分清两种操作：

- **修改标志：** `event.set()` 改为 True，`event.clear()` 改为 False。
- **用等待结果观察标志：** `event.wait(timeout=0)` 不花时间等待，立即给出 True 或 False。它没有把标志改成这个返回值。

`wait()` 本身仍是等待通知的接口。上个实验中的 `stop.wait()` 可以一直等；这个实验特意设置 `timeout=0`，借立即返回的结果观察标志。超时只结束这一次等待，执行它的线程继续往下走，不会因此被终止。

`clear()` 不会重新启动已结束的线程，也不能把已经继续执行的 `worker` 倒退回等待处。

<span id="5-event带走两条结论"></span>

## 5. Thread / Event：带走三条结论

1. `threading` 是模块；`thread` 是线程对象，`stop` 是单独的通知对象，通过参数交给 `worker` 共用。
2. `stop.set()` 发通知，`stop.wait()` 等通知；工作函数收到通知后自己收尾退出，调用方再用 `join()` 确认结束。
3. `clear()` 只重置通知标志，不会撤回线程已经执行的工作。

自查：为什么不能在 `stop.set()` 后立刻断言清理已完成？

<details><summary>查看解释</summary>

标志已设置不代表 worker 已运行到收尾。还要等 worker 返回，由 join 确认。

</details>

## 6. Thread / Event：本课接口速查

<div class="async-api-reference">

这里汇总本课用到的接口。先看手里是哪种对象，再选择方法：`stop` 和 `event` 都是 **Event 通知对象**，`thread` 是 **Thread 线程对象**。

### 6.1. Event：设置、重置与等待通知

`threading.Event()` 创建并返回一个通知对象，初始标志为 False。下面以变量 `event` 为例；主例子中的 `stop` 也可以调用这些方法。

| 调用 | 做什么、返回什么 |
| --- | --- |
| `event.set()` | 把标志改为 True，通知等待者可以继续。返回 `None`，不等待对方完成工作 |
| `event.clear()` | 把标志改为 False，供后续通知使用。返回 `None`，不会停止或重新启动线程 |
| `event.wait(...)` | 等待通知；因收到通知而返回时得到 True，因等待超时而返回时得到 False。它不会修改通知标志 |

`wait()` 不传超时就一直等到通知；`wait(timeout=0)` 不花时间等待，立即给出结果。本课用后一种写法观察标志，但 `wait` 本身仍是等待接口。

### 6.2. Thread：启动、等待与查看线程状态

`threading.Thread(...)` 创建并返回一个线程对象，保存目标函数和参数，此时还没有启动工作线程。本课复用第 27 课的三个方法：

| 调用 | 做什么、返回什么 |
| --- | --- |
| `thread.start()` | 启动工作线程，让它执行目标函数。返回 `None`，不等待工作完成；同一个线程对象只能启动一次 |
| `thread.join()` | 等目标线程结束；如果它已经结束，就直接返回。返回 `None`，不是工作函数的返回值 |
| `thread.is_alive()` | 查看线程是否已经启动且尚未结束，返回 True 或 False；未启动和已结束时都为 False |

**Event 的通知标志，与 Thread 是否还在运行，是两种不同的状态。** 发出通知用 `set()`；确认线程结束用 `join()`；查看线程是否仍在运行用 `is_alive()`。

</div>

<details><summary>按需阅读：项目对照与标准库依据</summary>

<span id="4-eventwait工作线程怎样合作"></span>

实际有多轮小工作时，可以在工作间隙检查通知：

```python
# 每轮先等通知：收到通知返回 True，超时则返回 False。
while not stop.wait(timeout=0.1):
    # 超时后 not False 为 True，执行一小段工作，再进入下一轮。
    do_one_small_step()
# 收到通知后 not True 为 False，离开循环，接着执行收尾代码。
```

这是结构示意，`do_one_small_step()` 代表一小段工作，不是额外需要学习的 API。标志仍为 False 且等待超时，`wait()` 返回 False，进入下一轮；标志为 True，返回 True 并离开循环。通知不会强制打断已经在执行的那一小段工作，能多快退出取决于何时回到检查位置。

主例子是独立标准库实验。[旧版健康检查线程的停止与等待](../09-thread-synchronization/#thread-basics)保留已核对的项目材料；这里先学原生机制，再按需回看调用位置。

语义按 [Python 3.12 官方文档](https://docs.python.org/3.12/library/threading.html#event-objects)和本机 Python 3.12.3 标准库核对，示例使用 Python 3.11 及以上版本。

</details>

---

[上一节：28 · threading.Lock：保护线程共享状态](../28-thread-lock/) · [下一重点：31.1 · ThreadPoolExecutor / submit](../31-threadpool-submit/) · [本轮优先路线](../learning-route/#priority-reading)
