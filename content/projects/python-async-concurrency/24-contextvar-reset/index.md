---
title: "24.2 · ContextVar.reset：用 token 恢复修改前的值"
description: "在同一个任务中临时修改 ContextVar，用 set 返回的 token 恢复原有绑定。"
weight: 242
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [24.1](../11-contextvars/)说明 set 修改当前任务上下文中的值，get 读取它；[第 09 课](../09-task-cancellation/)用 try/finally 安排退出时的清理。
>
> **本节新增的问题：** 不同任务的值已经隔离了。但在同一个任务里，原来保存着 10，一小段代码临时需要 20，用完以后怎样恢复原来的 10？

## 1. 为什么还需要恢复？

`set(20)` 会改变当前上下文中的值。离开某个普通代码块或返回调用方，并不会自动把它改回 10。

如果只固定写 `set(10)`，这一次可以恢复；但同一段代码下次进入时，原值也许是 30，甚至从未设置过。我们需要记住**这一次修改前的状态**。

<span id="contextvar-token"></span>
<span id="task-context"></span>

## 2. set 返回 token，reset 用它恢复

**token 是这一次 set 的恢复凭据。** `set(20)` 一边把当前上下文的值改成 20，一边返回 token；`reset(token)` 根据它恢复修改前的绑定。token 不是那个新值 20，也不是一份 Task。

[下载 example.py](example.py)，运行 `python3 -W error example.py`。这是原 [token-reset.py](../11-contextvars/token-reset.py) 的同一份实验。

```python
import asyncio
from contextvars import ContextVar


current_id = ContextVar("current_id", default=None)


async def exercise():
    current_id.set(10)  # 模拟这份任务原本已经有一个值。
    print("before", current_id.get())

    token = current_id.set(20)  # 改成临时值，同时取得这一次修改的恢复凭据。
    try:
        print("temporary", current_id.get())  # 当前上下文现在读到 20。
    finally:
        current_id.reset(token)  # 还原这次修改前的绑定，恢复为 10。

    print("restored", current_id.get())


if __name__ == "__main__":
    asyncio.run(exercise())
```

Python 3.12.3 下的实际输出：

```text
before 10
temporary 20
restored 10
```

## 3. 沿着同一份任务看变化

| 执行到哪里 | 当前 get 的结果 | 发生了什么 |
| --- | --- | --- |
| set(10) 之后 | 10 | 模拟进入临时代码前已有的值 |
| token = set(20) 之后 | 20 | 改成临时值，并取得这次修改的恢复凭据 |
| reset(token) 之后 | 10 | 恢复这次修改前的绑定 |

1. `set(10)` 建立已有值。它也返回 token，但本例不需要恢复这一步，所以没有保存。
2. `token = set(20)` 同时完成改值和记录恢复信息。之后 `get()` 立即读到 20。
3. `finally` 中执行 `reset(token)`，恢复到 10。这里没有启动新任务，也没有切换到另一个 ContextVar 对象。

**reset 不等于一律清空为 None。** 原来是 10，就恢复 10；原来没有设置过，就恢复为未设置状态，之后 get 才会使用默认值。本例默认值为 None。

使用 token 时，把它交还给产生它的同一个 ContextVar，并在同一上下文中恢复；一份 token 只能用于 reset 一次。

`try/finally` 沿用已学过的清理结构：临时工作抛出异常时，退出前仍会执行这里的恢复。恢复值不会吞掉原本的异常。

## 4. 本节带走什么？

1. 不同 Task 之间的绑定隔离，与同一 Task 内临时改值后的恢复，是两件事。
2. `set` 返回的 token 对应这一次修改；`reset(token)` 恢复修改前的状态。
3. 需要保证临时值用完后恢复时，把 reset 放进 finally。

自查：如果最初保存的是 30，临时改成 20，reset 后应该读到什么？为什么不能直接用 set(None) 代替？

答案：恢复为 30。set(None) 会设置一个新的 None，无法还原进入前的 30。

<details>
<summary>按需阅读：Slime 的 rollout_context 怎样复用这一步</summary>

回顾[第 21 单元](../21-async-contextmanager/)中进入、yield 和退出的组织方式。Slime 使用同步版本的 `contextmanager`，把本节的临时改值与恢复包进同样的结构：

```python
@contextmanager
def rollout_context(rollout_id):
    token = _task_rollout_id.set(rollout_id)  # 进入：保存这次修改的恢复凭据。
    try:
        yield  # 让调用方执行 with 内的代码。
    finally:
        _task_rollout_id.reset(token)  # 退出：恢复进入前的绑定。
```

这是带教学注释的源码片段，需要完整定义和导入才能独立运行。`_task_rollout_id` 对应 24.1 的 `current_id`；真实函数名与恢复结构保持不变。

这里使用同步的 `with`，因为进入和退出的 set/reset 本身不需要 await。with 块内的协程仍可以 await；退出时再恢复当前任务的绑定。

[查看完整可运行例子与固定版本源码](../11-contextvars/#rollout-context)。例子保留 Slime 的 `_task_rollout_id`、`rollout_context` 与恢复结构，裁去 hook 和 Sample。源码快照为 `2f2318653f6f794dddd321eff7c9d4b7b174643f`，位置是 `slime/rollout/sample_hooks.py`。

</details>

语义核对：[Python 3.12 contextvars](https://docs.python.org/3.12/library/contextvars.html)。

---

[上一课：24.1 · ContextVar.set / get](../11-contextvars/) · [下一课：25 · 辨认函数与可等待对象](../25-inspect-awaitable/) · [学习路线](../learning-route/)
