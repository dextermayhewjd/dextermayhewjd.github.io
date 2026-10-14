---
title: "13 · ContextVar：让并发任务保留各自的上下文"
description: "区分任务上下文与共享全局变量，并恢复进入前的状态。"
weight: 130
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 两个任务为什么不能共用一个 current_id

如果两个任务都把自己的编号写进同一个普通全局变量，某个任务暂停后再恢复时，读到的可能已经是另一个任务的编号。这里需要的是上下文隔离。

下面保留 Slime 的 `_task_rollout_id`、`rollout_context()` 和 token 恢复结构，删去 hook 和 Sample，只观察任务编号。

```python
import asyncio
from contextlib import contextmanager
from contextvars import ContextVar

_task_rollout_id = ContextVar("rollout_sample_hook_id", default=None)

@contextmanager
def rollout_context(rollout_id):
    token = _task_rollout_id.set(rollout_id)
    try:
        yield
    finally:
        _task_rollout_id.reset(token)

async def generate(rollout_id):
    with rollout_context(rollout_id):
        await asyncio.sleep(0)
        return _task_rollout_id.get()

async def exercise():
    print("task values", await asyncio.gather(generate(10), generate(11)))
    print("outer value", _task_rollout_id.get())

if __name__ == "__main__":
    asyncio.run(exercise())
```

[下载并运行本节 example.py](example.py)。只使用 Python 标准库；推荐 Python 3.12，最低 Python 3.11。

运行结果：

```text
task values [10, 11]
outer value None
```

<span id="task-context"></span>

## set 的返回值为什么还要保留

`ContextVar.set()` 返回 token。`reset(token)` 把变量恢复到设置之前的状态，比一律设成 None 更适合嵌套调用。

实验中的两个任务都在设置编号后暂停一次。它们恢复后仍读到各自的编号；退出上下文以后，外层仍是默认值 None。

ContextVar 隔离的是上下文中的绑定，不会把绑定到的可变对象自动深拷贝。如果多个上下文都持有同一个列表，它们仍可能修改同一份列表；这时还要考虑状态设计和同步。

<details><summary>复述检查</summary>

锁决定谁可以同时操作共享状态；ContextVar 决定这次任务读取哪一个上下文值。两者解决不同问题。

</details>

语义核对：[contextvars](https://docs.python.org/3.12/library/contextvars.html)、[isawaitable](https://docs.python.org/3.12/library/inspect.html#inspect.isawaitable)。

{{< python-async-slime >}}

## Slime 怎样把它交给 hook

`rollout_context` 保存和恢复编号；`apply_rollout_sample_hooks` 读取当前任务编号。hook 的返回值还可能是 awaitable，因此先用 `inspect.isawaitable()` 判断，再决定是否 await。

<details>
<summary>展开 Slime 源码：rollout_context</summary>

{{< source-reference id="source-1" >}}

</details>

<details>
<summary>展开 Slime 源码：_apply_to_sample</summary>

{{< source-reference id="source-2" >}}

</details>

{{< python-async-coverage lesson="11-contextvars" >}}

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节](../10-async-protocols/) · [下一节：14 · 进程池、子进程与系统边界](../12-processes/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
