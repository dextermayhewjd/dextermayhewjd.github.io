---
title: "33.1 · get_running_loop：取出正在使用的事件循环"
description: "接回第 03 课的事件循环：loop 是什么，怎样在协程中取得它？"
weight: 331
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 01–02 课](../02-await/)用 `asyncio.run()` 从脚本运行协程；[第 03 课](../03-tasks/#4-用事件循环解释等待与结果读取)用事件循环解释任务怎样轮流执行。
>
> **本节新增的问题：** 已经在协程里面，后面想调用这个事件循环的方法，怎样先取得它？

<span id="running-loop"></span>

## 1. loop：接回第 03 课，先认清它是什么

回想第 03 课：`main` 等待未完成的 Task 时，事件循环可以推进其他已经就绪的任务。**这里的 loop 就是那一个负责调度的对象。**

先分清三个名字所处的位置：

<div class="async-api-reference">

| 名字 | 本例中是什么 |
| --- | --- |
| 主线程 | 执行代码的线程；本例的事件循环在这里运行 |
| `exercise` | 一个协程函数；调用后由 `asyncio.run()` 运行它的协程对象 |
| `loop` | 保存当前事件循环对象的变量；这个对象负责安排协程执行和恢复 |

</div>

主线程是执行位置，协程是要运行的代码，事件循环是安排这些协程的对象。**取得 loop 对象这一步不会创建线程，也不会安排新的工作。**

下一节要向指定线程池提交工作，需要调用当前循环的 `run_in_executor` 方法；这一节先学会取得当前循环。

## 2. get_running_loop：在协程里面，取得已经运行的循环

[下载 example.py](example.py)，运行 `python3 -W error example.py`。

<div class="async-coordination-code">

```python
import asyncio


async def exercise():
    print("inside coroutine")
    # 取出当前正在运行这个协程的事件循环。
    loop = asyncio.get_running_loop()
    # 再取一次，仍然是当前这一个循环，不会新建循环。
    same_loop = asyncio.get_running_loop()
    print("same loop", loop is same_loop)  # True：两个变量指向同一个对象。


if __name__ == "__main__":
    print("before run")
    asyncio.run(exercise())  # 沿用第 01 课的入口，运行协程并等它结束。
    print("after run")
```

</div>

实际输出：

```text
before run
inside coroutine
same loop True
after run
```

`loop is same_loop` 检查两个变量是否指向同一个对象。True 表示：取了两次，得到的仍是同一个事件循环。

## 3. run / get_running_loop：按同一次调用分清职责

1. 脚本先打印 `before run`。
2. `asyncio.run(exercise())` 建立并运行事件循环，开始执行 `exercise`，所以打印 `inside coroutine`。
3. 协程内部两次调用 `get_running_loop()`，都取得正在运行自己的循环对象。
4. `exercise` 结束，`asyncio.run()` 返回，脚本才打印 `after run`。

`asyncio.run()` 是已学的运行入口；`get_running_loop()` 是这次新增的取对象接口。后者不负责启动、等待或提交任务。

## 4. get_running_loop：带走两条结论

1. 事件循环早已在第 03 课承担调度工作；本节只是把当前这个对象取出来，保存到 `loop`。
2. 本例在正在运行的协程内部取循环。在没有运行中循环的普通脚本位置调用，会抛出 `RuntimeError`。

自查：第二次调用 `get_running_loop()` 会新建循环吗？`loop` 是一条新线程吗？

<details><summary>查看解释</summary>

都不是。两次得到同一个事件循环对象；本例的事件循环仍在主线程中运行。

</details>

<details><summary>按需阅读：标准库依据</summary>

依据 [Python 3.12：asyncio.get_running_loop](https://docs.python.org/3.12/library/asyncio-eventloop.html#asyncio.get_running_loop)。示例在 Python 3.12.3 运行，最低 Python 3.11。

</details>

---

[上一节：31.2 · ThreadPoolExecutor.map](../31-threadpool-map/) · [下一节：33.2 · run_in_executor / await](../33-run-in-executor/) · [重点续学路线](../learning-route/#priority-reading)
