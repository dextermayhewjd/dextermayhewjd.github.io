---
title: "23 · 异步能力检查与协议边界"
description: "区分函数、返回对象、类型注解和语法协议，读懂 Slime 的同步/异步扩展点。"
weight: 230
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

函数与返回对象的检查已独立为[第 25 课：inspect.isawaitable / inspect.iscoroutinefunction](../25-inspect-awaitable/)。本页保留原来的多主题参考及下载。

<span id="inspection-route"></span>
## 从一个 hook 调用走到返回结果

这一章跟随“加载 hook → 调用 → 判断返回对象 → 必要时 await → 接纳结果”，然后再看 trace 装饰器如何决定包装函数形状。重点是：**函数定义、调用返回的对象和注解提供不同证据**，不能互相替代。

<span id="isawaitable"></span>
## isawaitable 检查已经得到的对象


`isawaitable` 只判断对象能否用于 `await`，不启动它，不等它结束，也不保证业务结果类型正确。同步 hook 的函数体在调用那一行立即执行；如果它做长时间阻塞 I/O，这个检查不能把阻塞变成异步。


<span id="iscoroutinefunction"></span>
## iscoroutinefunction 在调用前决定 wrapper 形状


| 传入实现 | `iscoroutinefunction(fn)` | 调用后的对象 | 合适的后续动作 |
| --- | --- | --- | --- |
| 普通 `def` 返回整数 | 假 | 整数，`isawaitable` 为假 | 直接读取 |
| `async def` 返回整数 | 真 | 协程对象，`isawaitable` 为真 | await 后才取得整数 |
| 普通 `def` 返回另一个函数的协程对象 | 通常为假 | 协程对象，`isawaitable` 为真 | 对返回对象 await |

Python 3.12 的函数检查还识别 `functools.partial` 包装的协程函数，以及显式标记的同步函数；所以“通常为假”描述的是本实验中未标记的普通函数。不要把对少数定义形式的检查扩张成“所有异步行为均能提前识别”。


<span id="async-type-annotations"></span>
## Awaitable 与 AsyncIterator 描述契约，不安排执行

`collections.abc.Awaitable[T]` 表示 await 后能取得 T 的对象；`collections.abc.AsyncIterator[T]` 表示可以异步逐项取得 T 的迭代器。它们可以用于注解，也作为抽象基类描述协议；写一条注解不创建 Task、不自动 await，也不在运行时验证返回值。


`async def f() -> int` 中 `int` 描述 await 后的值；调用 `f()` 先拿到协程对象。这和参数注解 `value: Awaitable[int]` 描述的输入层次不同。


<span id="async-protocol-methods"></span>
## 语法会进入哪些特殊方法

第 12 节读过使用方式，现在展开协议入口。协议要求返回的对象具备相应行为；不是在任意普通方法名前添加 `async` 就能满足。

| 语法/协议方法 | 输入与输出 | 结束和异常 |
| --- | --- | --- |
| `async with resource as value` → `__aenter__()` | 返回可等待对象；await 之后的值绑定到 `value` | 进入成功后，退出时才由语法调用 `__aexit__` |
| `__aexit__(exc_type, exc_value, traceback)` | 接收退出时异常信息，正常退出三个值为 `None`；返回值也被 await | 结果为真可抑制异常；返回假或 `None` 让原异常传播 |
| `async for value in source` → `__aiter__()` | 普通方法，直接返回异步迭代器 | Python 3.12 不接受它返回待 await 的协程 |
| 每次取项 → `__anext__()` | 返回可等待对象，await 后得到下一项 | 用 `StopAsyncIteration` 表达结束，其他异常传播 |

没有任何一行语法自动把每次迭代变成并发 Task；循环体依然一项处理完再取下一项。实验 `SampleStream` 是独立的语言演示，不冒充 Slime 内部类。`__aexit__` 返回假，保留错误；`__anext__` 产出两项后停止。

<span id="async-generator-cleanup"></span>
## break 结束消费，不等于资源已就地关闭

含 `yield` 的 `async def` 是异步生成器函数，调用后得到异步生成器，不是普通协程。每次恢复取到一个产出；自然耗尽以 `StopAsyncIteration` 结束。不要在异步生成器中用 `return value` 返回最终值，也不要自己抛 `StopAsyncIteration` 代替正常结束。

消费方提前 `break` 时，应把需要的清理边界写清楚。`await generator.aclose()` 让生成器执行退出流程，包括已经进入的 `try/finally`；`contextlib.aclosing(generator)` 把它绑定到 `async with` 的退出点。这比依赖垃圾回收时间或事件循环的最终兜底更明确。第 15 节 `loop.shutdown_asyncgens()` 是手动 loop 的兜底，不替代资源使用点的关闭。


<span id="inspection-lab"></span>
## 可运行实验：函数形状、返回值与关闭

[下载 example.py](example.py)，执行 `python3 -W error example.py`。只依赖标准库；推荐 Python 3.12，最低 3.11。

教学裁剪保留 `_apply_to_sample(args, sample, paths, **kwargs)` 与 `trace_function(name)` 名字和基本输入/输出。将动态导入换成本地 `HOOKS` 字典，Sample 简化为整数，省略参数签名过滤及业务类型检查；trace 的 target/attrs 解析与 span 写入简化为进入/退出记录。`SampleStream` 和 `chunks()` 则是独立语法实验。

<details><summary>展开完整实验：example.py</summary>

```python
"""Hook/trace teaching cuts plus independent async-protocol exercises."""
import asyncio
import functools
import inspect
from collections.abc import AsyncIterator, Awaitable
from contextlib import aclosing

EVENTS = []


def trace_function(name):
    # Slime keeps target resolution and trace_span here; we only record order.
    def decorator(fn):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args, **kwargs):
                EVENTS.append(name + ':enter')
                try:
                    return await fn(*args, **kwargs)
                finally:
                    EVENTS.append(name + ':exit')
            return async_wrapper

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            EVENTS.append(name + ':enter')
            try:
                return fn(*args, **kwargs)
            finally:
                EVENTS.append(name + ':exit')
        return sync_wrapper
    return decorator


@trace_function('sync')
def sync_hook(args, sample):
    return sample + 1


@trace_function('async')
async def async_hook(args, sample):
    await asyncio.sleep(0)
    return sample * 2


def deferred_hook(args, sample):
    return async_hook(args, sample)


HOOKS = {'sync': sync_hook, 'async': async_hook, 'deferred': deferred_hook}


async def _apply_to_sample(args, sample, paths, **kwargs):
    for path in paths:
        # Teaching substitution for Slime's load_function(path).
        hook = HOOKS[path]
        result = hook(args, sample, **kwargs)
        if inspect.isawaitable(result):
            result = await result
        if result is not None:
            sample = result
    return sample


class SampleStream:
    """Independent language exercise, not an excerpt from Slime."""
    def __init__(self):
        self.value = 0

    async def __aenter__(self):
        print('resource enter')
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        print('resource exit', exc_type.__name__ if exc_type else None)
        return False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.value == 2:
            raise StopAsyncIteration
        await asyncio.sleep(0)
        self.value += 1
        return self.value


async def chunks() -> AsyncIterator[int]:
    try:
        yield 10
        yield 20
    finally:
        print('generator closed')


async def exercise():
    result = await _apply_to_sample(None, 1, ['sync', 'async', 'deferred'])
    print('sample', result)
    print('trace', EVENTS)
    pending: Awaitable[int] = deferred_hook(None, 3)
    print('deferred', inspect.iscoroutinefunction(deferred_hook), inspect.isawaitable(pending))
    print('awaited', await pending)

    async with SampleStream() as stream:
        values = [value async for value in stream]
        print('values', values)

    stream: AsyncIterator[int] = chunks()
    async with aclosing(stream):
        async for value in stream:
            print('first', value)
            break


if __name__ == '__main__':
    asyncio.run(exercise())
```

</details>

```text
sample 8
trace ['sync:enter', 'sync:exit', 'async:enter', 'async:exit', 'async:enter', 'async:exit']
deferred False True
awaited 6
resource enter
values [1, 2]
resource exit None
first 10
generator closed
```

先看 `1 → 2 → 4 → 8`：三个 hook 分别同步返回、异步返回、同步返回一个协程对象；最后一个仍由 `isawaitable(result)` 接住。再看 `deferred False True`：同一个普通函数未被认作协程函数，但本次返回对象可等待。注解 `pending: Awaitable[int]` 没有替 `await pending` 执行任务。最后取异步生成器第一项后 break，`aclosing` 确保 `generator closed` 在当前作用域退出时发生。

<span id="object-method-boundaries"></span>
## 同名方法不证明对象属于原生并发 API

库存里的实例候选保留了实际源码位置，但候选不能直接等同于运行时类型结论。必须沿接收者的构造、参数来源或可靠注解辨认对象，再读该类契约。

| 表面相同的调用 | 实际区别 | 继续阅读 |
| --- | --- | --- |
| `.get(...)` | `dict.get` 读取映射；`queue.Queue.get` 是同步队列读取；`asyncio.Queue.get` 返回要等待的操作；`ray.get` 是第三方入口 | [09 · 队列](../07-queues/) |
| `.join(...)` | `str.join` 拼接字符串；`threading.Thread.join` 等线程退出；队列 `join` 等任务记账归零；调用是否阻塞/可 await 各不相同 | [09 · 队列](../07-queues/)、[11 · 线程同步](../09-thread-synchronization/) |
| `.close(...)` | 文件、子进程管道、StreamWriter、Server、第三方 client 或业务对象可能都使用这个名字；关闭资源的层次和是否需要等待不同 | [20 · 进程生命周期](../18-process-lifecycle/)、[22 · Streams](../20-async-streams/) |

同样，`inspect.isawaitable(obj)` 能告诉我们 await 合法，却不能证明 obj 来自 asyncio；第三方对象也可以实现可等待协议。源码候选表用于定位和复核，不应因为方法名像 `get` / `join` / `close` 就计入已证明的原生 API 使用。

<details><summary>语言依据与版本边界</summary>

**书上怎么说**：书中建议 Python 3.9 起用 `collections.abc` 的对应异步类型；注解区分输入等待对象与 await 后返回值。

**我的判断（本书未覆盖）**：hook 和 trace 的不同适配能力来自本章固定 Slime 源码；函数检查的 Python 3.12 扩展、提前 break 后的显式关闭按官方文档核对。

**依据 A**：《Fluent Python, 2nd Edition》（2022），第 21 章 Type Hinting Asynchronous Objects。英文 `corpus/en/ch21.md:1579–1633`，中文 `corpus/zh/ch21.md:1530–1586`，锚点 `type-hinting-asynchronous-objects`。本书基于 Python 3.10；本次验证解释器 Python 3.12.3。

原文：“With Python ≥ 3.9, use the `collections.abc` equivalents of these.”

对照：“对于 Python 3.9 及以上版本，应使用 `collections.abc` 中的对应类型。”

</details>

语义核对：[inspect 的异步检查](https://docs.python.org/3.12/library/inspect.html#inspect.isawaitable)、[异步上下文与迭代协议](https://docs.python.org/3.12/reference/datamodel.html#coroutines)、[异步生成器关闭](https://docs.python.org/3.12/reference/expressions.html#asynchronous-generator-iterator-methods)、[aclosing](https://docs.python.org/3.12/library/contextlib.html#contextlib.aclosing)、[collections.abc](https://docs.python.org/3.12/library/collections.abc.html)。

{{< python-async-slime >}}

`slime/rollout/sample_hooks.py` 的 `_apply_to_sample()` 先加载 `hook`，执行 `result = hook(...)`，然后 `inspect.isawaitable(result)`。若为真才 `result = await result`，最后检查结果类型。这样同一扩展点可接收同步函数、协程函数，也可接收“普通函数返回可等待对象”的实现。

<details><summary>展开固定源码：hook 的真实返回值检查</summary>

{{< source-reference id="source-1" >}}

</details>

`trace_function()` 在装饰时用 `inspect.iscoroutinefunction(fn)`：协程函数走 `async_wrapper`，在 trace 范围内 `await fn(...)`；同步函数走 `sync_wrapper`，在 trace 范围内直接 `fn(...)`。它检查的是函数，和前面检查返回对象的时机不同。

这个差异也影响 trace 边界：如果同步分支返回一个尚未执行的协程，`with trace_span` 在返回该对象时已经退出；以后别处才 await 的执行不自动仍处于同一个 span。Slime 的同步 wrapper 本身没有追加 `isawaitable` 适配，不能把 hook 的能力推到装饰器上。

<details><summary>展开固定源码：异步和同步 wrapper 的分支</summary>

{{< source-reference id="source-2" >}}

</details>

真实源码 `_run_request_abortable_generate(..., generate_call: Awaitable[Sample | list[Sample]])` 接收**已经创建的可等待对象**，在函数体内显式 `await generate_call`。`boot_agent_sandbox(...) -> AsyncIterator[E2BSandbox]` 的注解则配合其含 `yield` 的异步生成器实现，再由 `@asynccontextmanager` 变成异步上下文管理器入口。不能仅靠 `-> AsyncIterator[...]` 断言某函数一定启动了迭代。

<details><summary>展开固定源码：等待对象参数与沙箱生成器注解</summary>

{{< source-reference id="source-3" >}}

{{< source-reference id="source-4" >}}

{{< source-reference id="source-5" >}}

</details>

Slime 的沙箱生成器在 `yield sb` 外围用 `finally: await sb.__aexit__(None, None, None)` 负责释放。这个直接调用是源码的具体做法；一般 `async with` 语法还会传真实异常三元组，不能把两者所有行为视为完全相同。

{{< python-async-coverage lesson="21-async-inspection" >}}

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节](../20-async-streams/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
