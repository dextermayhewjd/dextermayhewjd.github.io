---
title: "09 · Lock、Event 与线程退出"
description: "线程共享状态怎样保护，后台线程怎样收到停止信号。"
weight: 90
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

<span id="thread-basics"></span>

## 工作移到线程后，多了什么责任

线程共享同一个进程中的对象。一个操作由“读、计算、写”几步组成时，多个线程交错执行可能破坏它的整体含义。锁保护的是这段需要一起完成的操作。

```python
import threading

lock = threading.Lock()
ready = threading.Event()
state = {"count": 0}

def worker():
    ready.wait()
    for _ in range(1000):
        with lock:
            state["count"] += 1

if __name__ == "__main__":
    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    ready.set()
    for thread in threads:
        thread.join()
    print("count", state["count"])
```

[下载并运行本节 example.py](example.py)。只使用 Python 标准库；推荐 Python 3.12，最低 Python 3.11。

运行结果：

```text
count 2000
```

实验把累加操作放在 `with lock` 中；`Event` 负责通知两个线程开始；`join()` 负责等它们结束。三者分别解决互斥、通知、等待退出，不能互相替代。

## 回到 Slime 的健康检查线程

`RolloutHealthMonitor` 使用 Event 表示停止、暂停，使用 Lock 协调检查中的工作。`stop()` 发出停止信号，调用带超时的 `join()`，再用 `is_alive()` 检查是否真的退出。

<details>
<summary>展开 Slime 源码：RolloutHealthMonitor.stop</summary>

{{< source-reference id="source-1" >}}

</details>

<details>
<summary>展开 Slime 源码：QueueReader._heartbeat_loop</summary>

{{< source-reference id="source-2" >}}

</details>

单独执行 `join(timeout=...)`，只能说明等待时间结束；线程可能仍然活着。把线程设成 daemon，也不能替代正常关闭流程。

### 停止通知怎样保存在 Event 中

| 方法 | 这里表达的意思 |
| --- | --- |
| `event.set()` | 把标记设为真，通知等待这个标记的线程 |
| `event.clear()` | 把标记恢复为假，供下一轮使用 |
| `event.is_set()` | 只查看标记，不等待，也不消耗通知 |
| `event.wait(timeout)` | 等标记变真；返回值说明标记是否在等待结束时为真 |

例如 `_stop.wait(interval)` 既可等待检查间隔，也可在停止标记设置后提前返回。`Event` 保存一个布尔标记，多次 `set()` 不会积累成多份消息；需要逐项保存结果时仍用 Queue。

`threading.Thread(target=...).start()` 启动线程，直接调用目标函数仍在当前线程执行。`threading.get_ident()` 取得当前线程标识，可用于 Slime 判断是否在同一线程重复进入某个区域；它不是进程编号，线程退出后标识也可能被复用。

要给共享状态加锁，可使用 `with lock` 自动配对获取和释放；显式 `acquire(timeout=...)` 则要检查返回值，只有获取成功后才可 `release()`。后面的第 16 节再展开 RLock、Condition 与 Timer。

## 两种 Lock 分别属于哪里

- `threading.Lock` 协调 OS 线程；等待会阻塞调用它的线程。
- `asyncio.Lock` 协调一个事件循环中的任务；等待通过异步方式进行，不用于跨线程互斥。
- `RLock` 允许同一线程重入同一把锁，但不会自动防止多把锁互相等待。

<details><summary>复述检查</summary>

停止 Event 是通知；线程自身必须检查这个通知并返回。`join` 等待它退出，`is_alive` 才能检查超时后是否仍在运行。

</details>

语义核对：[threading](https://docs.python.org/3.12/library/threading.html)。

{{< python-async-coverage lesson="09-thread-synchronization" >}}

---

[专题首页](../) · [上一节](../08-executors/) · [下一节：10 · async with、async for 与异步生成器](../10-async-protocols/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
