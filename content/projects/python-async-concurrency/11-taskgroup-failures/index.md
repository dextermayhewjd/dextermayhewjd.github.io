---
title: "11.1 · TaskGroup：一个任务失败，取消其余未完成任务并等待收尾"
description: "保持同一份 generate，只改变管理方式：一个任务失败后，TaskGroup 会请求取消其余未完成任务，即使它们没有出错；等它们收尾后，再向外报告整组失败。"
weight: 110
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. TaskGroup：一个任务失败，其余未完成任务也会被取消

上一节用 `gather(..., return_exceptions=True)` 等所有任务继续运行，再收齐结果与异常。现在换一个要求：**任务 11 失败后，不再需要任务 10 的结果；要取消它，等它完成清理，最后再报告整组失败。**

之前学过 `cancel()` 后再 `await`，可以手动组织这件事。本课把这项管理责任交给第 05 单元用过的 `TaskGroup`，观察它在失败时如何退出。

<span id="taskgroup-failure"></span>

## 2. TaskGroup.create_task：同一份 generate，改用任务组管理

`generate` 与前两节逐字相同：任务 11 立即抛出 `ValueError`，任务 10 在 `sleep` 处等待；本例的任务进入 `try` 后，无论正常返回、出错还是处理取消，都会执行 `finally`。

```python
import asyncio


async def generate(rollout_id, fail=False):
    print("start", rollout_id)
    try:
        if fail:
            raise ValueError(f"generation {rollout_id} failed")
        await asyncio.sleep(0.1)
        print("finished", rollout_id)
        return rollout_id
    finally:
        print("cleanup", rollout_id)


async def main():
    try:
        async with asyncio.TaskGroup() as group:
            group.create_task(generate(10))
            group.create_task(generate(11, fail=True))
        print("group finished")
    except Exception:
        print("group failed")


if __name__ == "__main__":
    asyncio.run(main())
```

[下载 example.py](example.py) · 运行：`python3 example.py`。本机 CPython 3.12.3 默认调度下的实际输出：

```text
start 10
start 11
cleanup 11
cleanup 10
group failed
```

<span id="taskgroup-cleanup"></span>

## 3. TaskGroup：从失败到退出，依次发生什么？

1. **任务 11 先失败并清理。** 它抛出 `ValueError`，离开函数前执行 `finally`，打印 `cleanup 11`。
2. **TaskGroup 对尚未结束的任务 10 请求取消。** 即使任务 10 本身没有出错，也会收到取消请求；发出请求时，它还没有完成收尾。
3. **任务 10 的 `await` 以抛出 `CancelledError` 的方式结束。** 本例中，它正在 `await asyncio.sleep(0.1)` 处等待。取消生效后，这次等待抛出 `asyncio.CancelledError`，不会沿正常路径继续向下执行。
4. **任务 10 离开 `try`，执行 `finally`。** 本例没有捕获 `CancelledError`，所以跳过 `print("finished", rollout_id)` 和 `return rollout_id`，进入 `finally`，打印 `cleanup 10`。这里执行清理，是因为异常使执行流程离开了已经进入的 `try`。
5. **清理结束，任务 10 才以取消状态结束。** `finally` 执行完后，`CancelledError` 继续向外传播；任务 10 没有正常返回结果。
6. **组内任务都结束后，TaskGroup 才向外报告整组失败。** TaskGroup 会等任务 10 完成上面的取消与清理过程。`async with` 没有正常退出，后面的 `group finished` 被跳过；外层 `except` 打印 `group failed`。

所以，`cleanup 10` 出现在 `group failed` 前面；`cleanup` 证明执行了收尾，不表示任务成功。这里取消任务 10 的是 TaskGroup 的失败处理，发生在 `main` 返回之前。

**取消需要事件循环获得执行机会。** 上面展示的是协程正在 `await` 等待时的过程；如果协程连续执行一段没有让出控制权的普通代码，就不会在任意一行被立即打断。`cancel()` 是请求取消，不能把“请求已发出”理解成“协程已经退出”。

外层收到的是**代表整组失败的异常对象**，不是直接把原始 `ValueError` 原样抛出来。这里的 `except Exception` 只用于这个最小实验打印失败；下一节再读取这个异常对象的具体结构。

## 4. TaskGroup：带走两条结论

1. 组内任务出现本例这样的普通错误时，TaskGroup 会取消尚未结束的其他任务。
2. TaskGroup 会等这些任务退出、执行清理后，再向外报告整组失败。

自查：为什么没有 `finished 10`，却有 `cleanup 10`？为什么 `group failed` 必须等在 `cleanup 10` 后面？

下一节保持任务与失败条件不变，只看外层究竟收到了什么：[11.2 · ExceptionGroup / except*：读取任务组的错误](../11-exception-groups/)。

{{< python-async-slime title="按需阅读：CPython 实现与源码位置" >}}

## 从实验回查 TaskGroup 的实现

主例子是独立标准库实验，不是 Slime、AReaL 或 verl 的业务源码裁剪。下面是 CPython `v3.12.3` 的连续原文摘录，已与本机 Python 3.12.3 标准库逐字核对。

`_abort` 对未结束的任务调用 `cancel()`；`_on_task_done` 移除已经结束的任务，并记录普通失败。两者对应上面“取消剩余任务”和“等待任务结束”的管理过程。

{{< source-reference id="source-1" >}}

<section id="source-usage-locations">

## 本节对应的源码位置

- [TaskGroup._on_task_done：记录错误并触发取消](https://github.com/python/cpython/blob/v3.12.3/Lib/asyncio/taskgroups.py#L197-L240)。
- [TaskGroup._abort：取消尚未结束的任务](https://github.com/python/cpython/blob/v3.12.3/Lib/asyncio/taskgroups.py#L183-L188)。
- [TaskGroup.__aexit__：等待组内任务全部结束](https://github.com/python/cpython/blob/v3.12.3/Lib/asyncio/taskgroups.py#L101-L126)。

</section>

语义核对：[Python 3.12 TaskGroup](https://docs.python.org/3.12/library/asyncio-task.html#task-groups)、[Task cancellation](https://docs.python.org/3.12/library/asyncio-task.html#task-cancellation)。这里聚焦普通错误触发的退出过程，异常组的结构留到下一节。

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节：10.2 · return_exceptions=True：收齐结果与异常](../15-gather-exceptions/) · [下一节：11.2 · ExceptionGroup / except*：读取任务组的错误](../11-exception-groups/) · [完整学习路线](../learning-route/)
