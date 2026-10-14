---
title: "11.2 · ExceptionGroup / except*：读取任务组的错误"
description: "保持同一份失败实验，用 except* 按内部异常类型匹配，再从异常组中读取具体错误。"
weight: 111
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. ExceptionGroup：整组失败后，怎样读出具体错误？

上一节看到：任务 11 失败，TaskGroup 取消并等完任务 10，最后向外报告整组失败。`except Exception` 只打印了一行 `group failed`，还没有读取里面的错误。

本课不改变任务与失败条件，只增加一个关系：**TaskGroup 用异常组装起错误，`except*` 按组内异常的类型匹配。**

<span id="exception-group"></span>

## 2. except*：保持 generate 不变，读取异常组

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
    except* ValueError as errors:
        print("caught", type(errors).__name__)
        for error in errors.exceptions:
            print("error", error)


if __name__ == "__main__":
    asyncio.run(main())
```

[下载 example.py](example.py) · 运行：`python3 example.py`。本机 CPython 3.12.3 默认调度下的实际输出：

```text
start 10
start 11
cleanup 11
cleanup 10
caught ExceptionGroup
error generation 11 failed
```

`cleanup 10` 之前的过程与上一节相同；只替换了外层的异常处理部分。

<span id="except-star"></span>

## 3. except*：errors 与 error 分别是什么？

1. **`ExceptionGroup` 是异常容器，本身也是异常对象。** 本例只有任务 11 的一个 `ValueError`，TaskGroup 仍将它装进异常组后抛出；普通的 `except ValueError` 不会匹配这个外层组。
2. **`except* ValueError` 按组内类型匹配。** `as errors` 得到包含匹配错误的子组，所以 `type(errors).__name__` 仍是 `ExceptionGroup`，不是 `ValueError`。
3. **`errors.exceptions` 是元组，里面存的是异常对象。** 本例的这一层只有一个 `ValueError`；循环中的 `error` 就是它，`print` 显示它的消息 `generation 11 failed`。

任务 10 是在整组收尾时被取消的。TaskGroup 不把这次 `CancelledError` 加入这里的异常组，所以本例只有任务 11 的一个普通错误。

这里按类型匹配的是组内错误，绑定到 `errors` 的仍然是一个组。若组里还有未被 `except* ValueError` 匹配的错误，那一部分会继续向外传播。

## 4. ExceptionGroup / except*：带走两条结论

1. `except*` 可以按内部异常类型处理异常组；绑定的变量仍是匹配到的子组。
2. `errors.exceptions` 保存成员异常对象；本例读取的对象是 `ValueError`，不是错误消息字符串。

自查：`errors` 与循环里的 `error` 哪一个是组？为什么把 `except* ValueError` 改成普通 `except ValueError`，就接不住本例的外层异常？

可运行补充实验 [multiple_errors.py](multiple_errors.py)：它只把任务 10 也改成 `fail=True`。本机默认调度下会读到两个 `ValueError`。这说明组里可以包含多个错误；其他程序中，部分任务可能先被取消，不能保证所有任务都来得及失败。

下一节回到成功结果，学习怎样按完成顺序逐个取得结果：[12 · asyncio.as_completed](../08-as-completed/)。

{{< python-async-slime title="按需阅读：CPython 实现与源码位置" >}}

## 从实验回查异常组的构造

主例子是独立标准库实验，不是三库业务源码裁剪。下面是 CPython `v3.12.3` 的连续原文摘录，已与本机 Python 3.12.3 标准库逐字核对。

TaskGroup 等任务结束后，用保存的错误构造异常组并抛出。

{{< source-reference id="source-1" >}}

源码调用的是 `BaseExceptionGroup`；当所有成员都是普通 `Exception` 时，它会返回 `ExceptionGroup`，所以本例打印的是后者。

<section id="source-usage-locations">

## 本节对应的源码位置

[TaskGroup.__aexit__：构造并抛出异常组](https://github.com/python/cpython/blob/v3.12.3/Lib/asyncio/taskgroups.py#L139-L147)。

</section>

语义核对：[Python 3.12 异常组](https://docs.python.org/3.12/library/exceptions.html#exception-groups)、[`except*` 语句](https://docs.python.org/3.12/reference/compound_stmts.html#except-star)。异常组也能嵌套；本课只读取主例子里的一层。

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节：11.1 · TaskGroup：一个任务失败，取消其余未完成任务并等待收尾](../11-taskgroup-failures/) · [下一节：12 · asyncio.as_completed：按完成顺序取结果](../08-as-completed/) · [完整学习路线](../learning-route/)
