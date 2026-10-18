---
title: "20.2 · get_running_loop：取得正在运行的事件循环"
description: "区分 asyncio.run 建立并运行循环，与 get_running_loop 取得已有对象。"
weight: 202
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 03 课](../03-tasks/)已经用事件循环解释：一份任务挂起时，其他就绪任务可以继续。[20.1](../20-async-event/)又观察了通知与恢复的先后。
>
> **本课新增的问题：** 下一节要创建属于当前循环的等待结果对象。在调用循环的方法之前，怎样取得这个循环？

## 1. 事件循环：一直在使用，现在把对象取出来

前面的脚本都用 `asyncio.run(exercise())` 进入异步执行。它建立并运行事件循环，驱动 `exercise`，并在返回前完成相应收尾、关闭循环。

**事件循环是管理任务调度、就绪回调和等待事件的对象。** 本课先只用已有的经验理解它：当前任务等住时，循环可以安排其他已经就绪的任务；等待条件满足后，任务才有机会继续。

之前不必把循环存进变量。现在要调用这个对象的方法，使用 `loop = asyncio.get_running_loop()` 取得它。这里的 `loop` 是变量名，指向已有对象。

## 2. get_running_loop：两次取得的是同一个对象

[下载 example.py](example.py)，运行 `python3 -W error example.py`。

```python
import asyncio


async def exercise():
    loop = asyncio.get_running_loop()  # 取得正在运行本协程的循环，不创建新循环。
    same_loop = asyncio.get_running_loop()  # 同一线程、同一次运行，取得同一个对象。
    print("same loop", loop is same_loop)


if __name__ == "__main__":
    asyncio.run(exercise())  # 建立并运行循环；协程结束后完成收尾并关闭它。
    try:
        asyncio.get_running_loop()  # run 已返回，当前线程没有正在运行的循环。
    except RuntimeError:
        print("outside run: no running loop")
```

实际输出：

```text
same loop True
outside run: no running loop
```

`is` 比较是否为同一个对象。第一行的 `True` 说明两次查询没有分别创建两个循环。

## 3. run 与 get：职责分开

1. 脚本调用 `asyncio.run(exercise())`，建立并运行循环。
2. 循环驱动 `exercise`，函数体才开始执行。
3. 两次 `get_running_loop()` 查询当前线程正在运行的循环，取得同一个对象。
4. `exercise` 结束，`run` 收尾并返回；随后再查询，就会抛出 `RuntimeError`。

`get_running_loop()` 是普通函数，直接返回循环对象，不需要 `await`。它本身不提交工作、不启动线程，也不使当前任务挂起。

查询范围是**当前线程**；别的线程中即使有循环在运行，也不会被这次查询取到。手动创建循环和跨线程提交放在后续课程，本节不需要它们。

## 4. 带走两条结论

1. `asyncio.run()` 负责本例的运行入口；`get_running_loop()` 取得已经在运行的循环对象。
2. 当前线程没有正在运行的循环时，查询会报 `RuntimeError`，不会自动创建一个。

自查：删除 `loop = asyncio.get_running_loop()`，但保留脚本的 `asyncio.run(exercise())`，事件循环还会建立吗？会。查询只是取得对象，并非创建它的步骤。

本节为独立标准库实验，按 Python 3.12.3 验证，最低 Python 3.11。依据：[运行入口](https://docs.python.org/3.12/library/asyncio-runner.html#asyncio.run)、[get_running_loop](https://docs.python.org/3.12/library/asyncio-eventloop.html#asyncio.get_running_loop)。

---

[上一节：20.1 · Event](../20-async-event/) · [下一节：20.3 · Future 保存结果](../20-future-result/) · [学习路线](../learning-route/)
