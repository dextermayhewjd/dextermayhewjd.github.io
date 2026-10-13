---
title: "01 · async def：定义之后，什么时候执行？"
description: "先分清异步函数、协程对象和真正执行的函数体。"
weight: 10
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

<span id="coroutine-definition"></span>

## 这一节只解决一个问题

看到 `async def generate(...)` 时，不能把“定义函数”“调用函数”“执行函数体”当成同一件事。

你已经熟悉 `def`、函数参数和 `return` 就可以开始。本节暂时不需要了解线程、网络请求或 Slime 的训练过程。

<span id="run-entry"></span>

## 运行一个小实验

下面是独立的语言实验，沿用 Slime 测试里的 `generate(rollout_id)` 和 `exercise()` 名称；把实际生成逻辑替换为打印和返回编号。它不是 Slime 的完整实现。

```python
import asyncio

async def generate(rollout_id):
    print("run", rollout_id)
    return rollout_id

async def exercise():
    coro = generate(10)
    print("created")
    result = await coro
    print("result", result)

if __name__ == "__main__":
    asyncio.run(exercise())
```

[下载并运行本节 example.py](example.py)。只使用 Python 标准库；推荐 Python 3.12，最低 Python 3.11。

运行结果：

```text
created
run 10
result 10
```

按发生顺序看：

1. `async def generate` 定义了一个**协程函数**。
2. `generate(10)` 创建**协程对象**，此时还没打印 `run 10`。
3. `await coro` 开始执行这个协程，并等待它返回。
4. `asyncio.run(exercise())` 建立并运行本次实验的事件循环，最后收尾。

这里没有同时执行两个任务。先把一次调用读懂，再进入并发。

## 回到 Slime

原测试用 `generate(rollout_id)` 创建两份工作，再交给 `gather`。现在只需要认出函数定义与调用，下一节再读 `await`，第 3 节再展开 `gather`。

<details>
<summary>展开 Slime 源码：generate / exercise</summary>

{{< source-reference id="source-1" >}}

</details>

## 先自己回答

为什么 `created` 出现在 `run 10` 前面？把 `await coro` 删除后，`generate` 的函数体还会执行吗？

<details><summary>查看解释</summary>

创建协程对象本身不执行函数体。删除 `await` 且不把对象交给其他调度入口时，它不会执行，并可能产生“协程未被等待”的运行时警告。

</details>

语义核对：[Python：协程与等待对象](https://docs.python.org/3.12/library/asyncio-task.html#coroutines)。

{{< python-async-coverage lesson="01-async-def" >}}

---

[专题首页](../) · [下一节：02 · await：等待结果，不等于自动并发](../02-await/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
