---
title: "28.1 · threading.Lock：保护线程共享状态"
description: "当两个线程都修改同一个计数，怎样让一次完整更新不与另一次交错？"
weight: 281
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 19 课](../19-async-lock/)把共享状态的读改写放进同一个保护范围；[第 27 课](../27-thread-lifecycle/)建立了工作线程。
>
> **本课新增的问题：** 当两个线程都修改同一个计数，怎样让一次完整更新不与另一次交错？

## 1. Lock：保护完整的读改写

两个线程共享 `state`。一次更新包含“读取旧值、计算、写回”，需要把这整个过程放进同一把锁保护的范围。

## 2. with lock：取得锁后再读，写完后释放

[下载 example.py](example.py)，运行 `python3 example.py`。

<div class="async-coordination-code">

```python
import threading


def worker(lock, state):
    for _ in range(1000):
        with lock:
            current = state["count"]
            state["count"] = current + 1


def main():
    lock = threading.Lock()
    state = {"count": 0}
    threads = [threading.Thread(target=worker, args=(lock, state)) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    print("count", state["count"])


if __name__ == "__main__":
    main()
```

</div>

实际输出：

```text
count 2000
```

## 3. Lock：锁住哪一段才有意义？

1. 两个 worker 拿到的是同一把 lock 和同一个 state。
2. 进入 `with lock` 前先取得锁；另一线程如果暂时取不到，会阻塞在获取处。
3. 持锁线程读取 count，再把新值写回；离开代码块后释放，另一线程才可进入。
4. 主线程等两个 worker 都结束，最终读取 count，得到 2000。

不能在锁外先读取旧值，再只锁住赋值；那样拿到的旧值可能已经过期。其他线程若绕过这把锁修改同一状态，锁也无法替它提供保护。

## 4. acquire / release：展开同一段 with

下面是主例子持锁区域的等价写法，不需要再获取第二把锁：

```python
lock.acquire()
try:
    current = state["count"]
    state["count"] = current + 1
finally:
    lock.release()
```

默认 `acquire()` 会等到获取成功；成功获取以后才负责 `release()`。`with lock` 自动配对进入和释放，也能覆盖区域内抛出异常的退出路径。

`threading.Lock` 的等待会阻塞当前线程，写普通 `with`；`asyncio.Lock` 的获取使用异步等待，写 `async with`。在事件循环线程里长时间等待线程锁，会影响那个线程上的协程推进。

## 5. Lock：带走两条结论

1. 同一份共享状态要由同一把锁保护完整更新。
2. 锁只允许一个线程进入持锁区域；离开后要释放。

自查：两个 worker 各自在函数里新建一把 Lock，能保护这个共享计数吗？

<details><summary>查看解释</summary>

不能。它们各拿自己的锁，仍可同时修改 state；必须共享同一把锁。

</details>

<details><summary>按需阅读：项目对照与标准库依据</summary>

主例子是独立标准库实验。[旧版共享计数与线程同步对照](../09-thread-synchronization/#thread-basics)保留已核对的项目材料；这里先学原生机制，再按需回看调用位置。

语义按 [Python 3.12 官方文档](https://docs.python.org/3.12/library/threading.html#lock-objects)和本机 Python 3.12.3 标准库核对，示例使用 Python 3.11 及以上版本。

</details>

---

[Lock ↔ RLock：关系摘要](../comparisons/lock-vs-rlock/)

[上一节：27 · threading.Thread：创建、启动并等待线程](../27-thread-lifecycle/) · [下一节：28.2 · threading.RLock：允许同一线程嵌套加锁](../28-thread-rlock/) · [返回学习路线](../learning-route/)
