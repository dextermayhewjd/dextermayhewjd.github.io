---
title: "25 · inspect.isawaitable / inspect.iscoroutinefunction：辨认函数与可等待对象"
description: "先辨认函数，再辨认调用返回的对象，决定是否需要 await。"
weight: 250
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 01 课](../01-async-def/)已经区分协程函数和调用得到的协程对象；[第 02 课](../02-await/)用 await 执行并等待协程，取得返回值。
>
> **本节新增的需求：** 同一个调用位置可能收到普通函数，也可能收到协程函数，需要判断调用后拿到的对象是否应当 await。
>
> **本节的解决方式：** 用 `inspect.iscoroutinefunction(fn)` 辨认函数，用 `inspect.isawaitable(result)` 辨认已经拿到的返回对象。

## 1. inspect：先分清被检查的是函数还是返回对象

拿到别人提供的函数 `fn` 时，`fn` 与 `fn(3)` 是两层东西：前者是函数，后者是调用它之后得到的对象。

<div class="async-api-reference">

| 要问的问题 | 应当检查谁 |
| --- | --- |
| 这个函数是否被识别为协程函数？ | 把函数 fn 传给 iscoroutinefunction |
| 已经拿到的对象能否 await？ | 把返回对象 result 传给 isawaitable |

</div>

**知道函数是什么，与知道调用后拿到什么，是两次不同的判断。**

## 2. iscoroutinefunction / isawaitable：对比三种调用结果

沿用取样本的名称：get_samples 是普通函数，get_samples_async 是协程函数。再增加一个普通函数 get_samples_later，专门展示“普通函数也能返回协程对象”。

本例在主线程的一份协程中依次调用这三个函数，重点只看函数与返回对象的区别。

[下载 example.py](example.py)，运行 `python3 -W error example.py`。

<div class="async-coordination-code">

```python
import asyncio
import inspect


def get_samples(num_samples):
    return list(range(num_samples))


async def get_samples_async(num_samples):
    return list(range(num_samples))


def get_samples_later(num_samples):
    # 普通函数也能返回协程对象；此时还没有执行协程函数体。
    return get_samples_async(num_samples)


async def exercise():
    for name, fn in [
        ("sync", get_samples),
        ("async", get_samples_async),
        ("later", get_samples_later),
    ]:
        # 先检查函数；True 表示识别为协程函数，这一步不调用它。
        print(name, "function", inspect.iscoroutinefunction(fn))
        result = fn(3)  # 调用一次：得到列表，或者得到尚未执行的协程对象。
        can_await = inspect.isawaitable(result)  # 再检查返回对象；不执行或等待它。
        print(name, "awaitable", can_await)  # True：可以 await；False：本例直接使用列表。
        if can_await:
            result = await result  # 执行并等待本例的协程对象，取得它返回的列表。
        print(name, "samples", result)


if __name__ == "__main__":
    asyncio.run(exercise())  # 运行一次实验，依次检查三个函数及其返回对象。
```

</div>

实际输出：

```text
sync function False
sync awaitable False
sync samples [0, 1, 2]
async function True
async awaitable True
async samples [0, 1, 2]
later function False
later awaitable True
later samples [0, 1, 2]
```

## 3. fn / result / await：沿同一次调用分三步读

### 3.1. iscoroutinefunction：检查函数，不调用函数

<span id="iscoroutinefunction"></span>

`inspect.iscoroutinefunction(fn)` 接收函数对象。主例子中，检查 get_samples_async 得到 True；检查两个普通函数得到 False。

检查本身不会调用 fn。真正的调用在下一行 `result = fn(3)`：普通函数立即执行函数体；协程函数先返回一个协程对象。

### 3.2. isawaitable：检查调用后已经得到的对象

<span id="isawaitable"></span>

`inspect.isawaitable(result)` 接收返回对象。列表得到 False，协程对象得到 True；这一步不会执行被检查的协程，也不会等待其结果。

如果一个普通函数在调用时做阻塞工作，阻塞发生在 `fn(3)` 那一行；后面的 inspect 检查不会把它自动变成异步工作。

### 3.3. await：根据对象决定是否等待

主例子在 `can_await` 为 True 时执行 `await result`，拿到列表后再打印；为 False 时，result 已经是列表，直接打印即可。

**两个检查都只返回判断结果；真正执行和等待的是调用与 await。**

## 4. 普通 def 返回协程：为什么只检查函数还不够？

get_samples_later 是本课最关键的一行对比：它自身是普通函数，所以函数检查为 False；但它返回 get_samples_async 创建的协程对象，因此对象检查为 True。

<div class="async-api-reference">

| 本例函数 | 函数检查 → 调用后的对象检查 |
| --- | --- |
| get_samples | False → False：返回列表，直接使用 |
| get_samples_async | True → True：返回协程对象，await 后取得列表 |
| get_samples_later | False → True：普通函数返回了协程对象，也需要 await |

</div>

因此，如果当前问题是“怎样接收这个调用的结果”，应当检查已经拿到的 result；不能仅因为函数检查为 False，就断言返回值不需要 await。

## 5. inspect：带走三条结论

1. iscoroutinefunction 检查函数，isawaitable 检查对象。
2. 普通函数也可能返回可等待对象，所以两次检查不能互相替代。
3. 检查不会替你执行或等待；本例在调用后，根据对象检查结果决定是否 await。

自查：get_samples_later 的函数检查为 False，为什么还要 await 它的返回值？isawaitable 返回 True 时，是否已经取得了最终列表？

<details><summary>查看解释</summary>

因为它返回的是协程对象；True 只表示这个对象支持 await，不表示协程已经运行或取得了结果。本例还需要执行 await result，才拿到列表。

</details>

## 6. inspect：本课接口速查

<div class="async-api-reference">

| 调用 | 回答什么 |
| --- | --- |
| inspect.iscoroutinefunction(fn) | fn 是否被识别为协程函数 |
| inspect.isawaitable(result) | result 是否可用于 await 表达式 |

</div>

{{< python-async-slime title="按需阅读：源码用法与版本边界" >}}

主例子是独立标准库实验。下面是 Slime 固定教学快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 中两种检查的实际用法。

`_apply_to_sample` 先调用 hook，再检查返回值是否需要 await；与主例子接收 result 的顺序相同。

{{< source-reference id="source-1" >}}

`trace_function` 则先检查传入的函数，用来决定包装函数采用哪一种定义形式。本课只辨认检查对象，不展开装饰器内部的跟踪逻辑。

{{< source-reference id="source-2" >}}

{{< python-async-coverage lesson="25-inspect-awaitable" >}}

依据：[Python 3.12：iscoroutinefunction](https://docs.python.org/3.12/library/inspect.html#inspect.iscoroutinefunction)、[isawaitable](https://docs.python.org/3.12/library/inspect.html#inspect.isawaitable)。例子在 Python 3.12.3 运行，使用 Python 3.11 及以上版本。

本例三个函数均未额外包装或标记。Python 版本也会影响部分包装函数或显式标记函数的识别范围，其他形式按对应版本的官方文档判断。

{{< /python-async-slime >}}

---

[上一课：24.2 · token/reset](../24-contextvar-reset/) · [前置回顾：34 · wrap_future](../34-wrap-future/) · [下一重点：37 · subprocess.run](../37-subprocess-run/) · [重点续学路线](../learning-route/#priority-reading)
