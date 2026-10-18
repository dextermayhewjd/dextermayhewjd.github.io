---
title: "24.1 · ContextVar.set / get：保存每份任务自己的值"
description: "区分一个 ContextVar 对象与各任务上下文中的值，先理解 set 和 get。"
weight: 241
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> [第 06 课的 gather](../05-gather/)可以安排并等待多份协程任务；任务在 await 处暂停后，其他任务能够继续执行。
>
> **本节新增的问题：** 两份任务都要保存自己的编号，暂停再恢复后，怎样仍读到自己的那个值？

**ContextVar 让同一个变量对象，在不同任务的上下文中保存各自的值。** 本节先用独立的标准库例子看清 `set/get`；临时值的恢复放在[下一课 24.2](../24-contextvar-reset/)。

## 1. 普通全局变量为什么会被覆盖？

如果两个任务都把自己的编号写进同一个普通全局变量，某个任务暂停后再恢复时，读到的可能已经是另一个任务的编号。这里需要的是上下文隔离。

例如，这是一种可能的交接顺序：

1. 任务 A 把共享变量改为 10，然后暂停。
2. 任务 B 把同一个共享变量改为 11，然后暂停。
3. A 恢复，读到的已经是 11。
4. B 恢复，也读到 11。

问题在于两个任务修改同一处绑定。希望保留的是“各自的当前编号”，而不是一份会被所有任务覆盖的当前编号。

<span id="contextvar-basic"></span>

## 2. ContextVar.set / get：先看最小例子

这份独立标准库实验先只观察每份任务的值，不加入装饰器或上下文管理器。

[下载 basic.py](basic.py)，运行 `python3 -W error basic.py`。

```python
import asyncio
from contextvars import ContextVar


current_id = ContextVar("current_id", default=None)  # 创建一个对象，未设置时读取 None。


async def generate(number):
    current_id.set(number)  # 设置这份任务上下文中的值。
    await asyncio.sleep(0)  # 交还执行机会，其他任务也可以设置自己的值。
    return current_id.get()  # 恢复后读取本任务的值，不会读成另一任务的编号。


async def exercise():
    results = await asyncio.gather(generate(10), generate(11))  # 安排两份任务并收集结果。
    print(results)
    print(current_id.get())  # 本任务没有设置过，仍然读取默认值 None。


if __name__ == "__main__":
    asyncio.run(exercise())
```

Python 3.12.3 下的实际输出：

```text
[10, 11]
None
```

<span id="contextvar-object-binding"></span>

## 3. 对象只有一个，读取哪份值由当前上下文决定

`current_id` 定义在模块顶层，是一个全局名字；它始终指向创建的那一个 ContextVar 对象。两份任务并没有各自重新定义一个 `current_id`。

但调用 `current_id.set(10)` **确实修改了值**：修改的是当前任务上下文中，这个 ContextVar 对应的值。它没有把全局名字 `current_id` 改成整数 10，也没有替换那个 ContextVar 对象。

因此，“原来的变量没有被修改”需要分开理解：

| 要区分的内容 | 调用 set 后发生什么 |
| --- | --- |
| 全局名字 `current_id` 指向哪个对象 | 仍指向同一个 ContextVar 对象 |
| 当前任务上下文里保存的值 | 被 set 修改了 |
| 其他任务上下文里保存的值 | 不会因此一起被修改 |

### 3.1. 同一个对象，在不同任务中读取

| 执行位置 | 设置的值 | 读取结果 |
| --- | --- | --- |
| `generate(10)` 所在任务 | 10 | 10 |
| `generate(11)` 所在任务 | 11 | 11 |
| `exercise` 所在任务 | 没有设置 | 默认值 None |

1. A 调用 `set(10)`，改变 A 当前上下文中的绑定。
2. B 调用 `set(11)`，改变 B 当前上下文中的绑定。
3. A 恢复后调用 `get()`，读取 A 上下文中的 10。
4. B 恢复后调用 `get()`，读取 B 上下文中的 11。

**没有创建两个 ContextVar 对象。** `current_id` 仍是同一个对象，但两份任务各自携带上下文；`get()` 按正在执行的上下文取值。

本例中，两个子任务设置自己的值，不会把 `exercise` 的值也改掉，所以最后仍打印 None。这里先验证不同任务之间的隔离；同一任务里临时改值后怎样恢复，[24.2 用 token/reset 说明](../24-contextvar-reset/)。

### 3.2. 区分不同 Task 与不同协程函数

**不是每个协程函数天然各有一份上下文。** 本例的 gather 把两份协程安排成不同 Task，才形成各自的任务上下文。

如果在同一个 Task 里直接 `await` 另一个协程，它们通常使用同一份上下文。被等待的协程执行 set，后面回到调用方时也能读到这个改动；要恢复之前的值，接着读 [24.2](../24-contextvar-reset/)。

## 4. 本节带走什么？

1. 模块顶层的 `current_id` 指向一个 ContextVar 对象；各任务不必各建一个对象。
2. `set(value)` 修改当前上下文中的值，`get()` 读取当前上下文中的值。
3. 创建 Task 时默认复制当前上下文；之后各 Task 的绑定变化彼此隔离。
4. 在同一个 Task 里直接 await 另一协程，不会因此新建一份任务上下文。

自查：如果把 `gather(generate(10), generate(11))` 改为在 `exercise` 中依次直接 await 两次 `generate`，最后 `exercise` 的 `get()` 还会是 None 吗？

答案：会是 11。两次调用都在同一个 Task 中修改值，最后一次 set 留下的就是 11。

<span id="contextvar-token"></span>
<span id="task-context"></span>

临时修改与恢复已拆到 [24.2 · ContextVar.reset：用 token 恢复修改前的值](../24-contextvar-reset/)。原有的 [token-reset.py 下载](token-reset.py)继续保留。

语义核对：[Python 3.12 contextvars](https://docs.python.org/3.12/library/contextvars.html)。

{{< python-async-slime >}}

<span id="rollout-context"></span>

### 两节学完后回查：Slime 的完整例子与原始源码

先学完 [24.2 的 token/reset](../24-contextvar-reset/)，再展开这里回查完整应用。原有 `example.py` 与固定版本源码保留在此。

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

两个任务都在设置编号后暂停一次，恢复后仍读到各自的编号。`rollout_context` 在进入时保留 set 返回的 token，在退出时用 reset 恢复；临时修改与恢复的过程在 24.2 展开。

### 按需回查：绑定隔离与共享可变对象

ContextVar 隔离的是上下文中的绑定，不会把绑定到的可变对象自动深拷贝。如果多个上下文都持有同一个列表，它们仍可能修改同一份列表；这时还要考虑状态设计和同步。

<details><summary>复述检查</summary>

锁决定谁可以同时操作共享状态；ContextVar 决定这次任务读取哪一个上下文值。两者解决不同问题。

</details>

### Slime 怎样把它交给 hook

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

[前置回顾：06 · gather](../05-gather/) · [下一课：24.2 · token/reset](../24-contextvar-reset/) · [学习路线](../learning-route/) · [源码与教程对照](../coverage/)
