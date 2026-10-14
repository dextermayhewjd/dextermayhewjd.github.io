---
title: "12 · async with、async for 与异步生成器"
description: "把异步资源的进入、迭代和退出连起来。"
weight: 120
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 两种等待发生在不同位置

`async with` 管理资源的异步进入和退出；`async for` 消费一个异步可迭代对象，每次取下一项都可能需要等待。它们并不表示循环体内部自动并行。

实验沿用 `boot_agent_sandbox` 名称，但把真实沙箱替换成字符串；不连接外部服务。`chunks` 只模拟两段数据，不模拟网络协议。

```python
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def boot_agent_sandbox():
    print("enter")
    try:
        yield "sandbox"
    finally:
        print("exit")

async def chunks():
    for value in ("A", "B"):
        await asyncio.sleep(0)
        yield value

async def exercise():
    async with boot_agent_sandbox() as sandbox:
        print(sandbox)
        async for chunk in chunks():
            print(chunk)

if __name__ == "__main__":
    asyncio.run(exercise())
```

[下载并运行本节 example.py](example.py)。只使用 Python 标准库；推荐 Python 3.12，最低 Python 3.11。

运行结果：

```text
enter
sandbox
A
B
exit
```

<span id="async-context"></span>

## 先看上下文管理器

带 `@asynccontextmanager` 的异步生成器，在 `yield` 之前准备资源，把 yield 的值交给 `as` 后的变量；退出作用域后继续执行后面的清理。`finally` 使异常退出也有机会清理。


<span id="async-iteration"></span>

## 再看异步迭代

`async def` 中出现 `yield`，这个函数就产生异步生成器。调用它得到的对象用于异步迭代，不能像普通协程那样直接 `await chunks()`。


<details><summary>复述检查</summary>

`await` 等一个结果；`async for` 逐个等结果；`async with` 管理资源进入和退出时的等待。`async for` 的循环体仍然按顺序推进，除非里面另行安排并发任务。

</details>

语义核对：[asynccontextmanager](https://docs.python.org/3.12/library/contextlib.html#contextlib.asynccontextmanager)、[异步迭代](https://docs.python.org/3.12/reference/compound_stmts.html#the-async-for-statement)。

{{< python-async-slime >}}

Slime 的 `boot_agent_sandbox()` 在准备成功后 yield 沙箱，退出时调用 `__aexit__()`。不要把进入、使用和回收分散到互不关联的调用里理解。

Slime 的流式 rollout 在 `async for raw_line in response.aiter_lines()` 中逐段处理服务返回的数据；Python 语法本身不绑定 HTTPX 或某种模型服务。

<details>
<summary>展开 Slime 源码：boot_agent_sandbox</summary>

{{< source-reference id="source-1" >}}

</details>

<details>
<summary>展开 Slime 源码：流式响应读取</summary>

{{< source-reference id="source-2" >}}

</details>

{{< python-async-coverage lesson="10-async-protocols" >}}

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节](../09-thread-synchronization/) · [下一节：13 · ContextVar：让并发任务保留各自的上下文](../11-contextvars/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
