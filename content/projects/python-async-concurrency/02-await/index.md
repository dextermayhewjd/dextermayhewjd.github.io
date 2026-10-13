---
title: "02 · await：等待结果，不等于自动并发"
description: "沿执行顺序理解挂起、恢复和 asyncio.sleep。"
weight: 20
ShowToc: true
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 接着上一节问

一个协程里面写了两次 `await`，两份工作会自动同时开始吗？先运行，再判断。

```python
import asyncio

async def generate(rollout_id):
    print("start", rollout_id)
    await asyncio.sleep(0)
    print("end", rollout_id)
    return rollout_id

async def exercise():
    first = await generate(10)
    second = await generate(11)
    print("results", [first, second])

if __name__ == "__main__":
    asyncio.run(exercise())
```

[下载并运行本节 example.py](example.py)。只使用 Python 标准库；推荐 Python 3.12，最低 Python 3.11。

运行结果：

```text
start 10
end 10
start 11
end 11
results [10, 11]
```

`exercise()` 要等第一份结果返回，才会走到第二个 `generate`。本节先读清这一条执行链：**进入协程 → 等待 → 恢复 → 返回**。

<span id="await-execution"></span>

## 跟着第一份调用走一次

```text
exercise()
  │
  ├─ await generate(10)：进入 generate 的函数体
  │    ├─ 打印 start 10
  │    ├─ await asyncio.sleep(0)：当前执行链暂停一次
  │    ├─ 恢复后打印 end 10
  │    └─ return 10
  │
  ├─ 第一份调用返回后，才进入 generate(11)
  └─ 最后打印 results
```

`await generate(10)` 要等待整个 `generate(10)` 返回。内部的 `await asyncio.sleep(0)` 则是它执行过程中的一次等待；恢复后，先继续这一份 `generate` 剩下的代码。

因此，**内部暂停过，不代表外层已经执行完这一行**。第二行 `await generate(11)` 仍然要等第一行结束。

## 对比：保留赋值与去掉赋值

两组都使用最上面的同一个 `generate()`。

保留赋值：

```python
async def with_assignment():
    first = await generate(10)
    second = await generate(11)
```

去掉赋值：

```python
async def without_assignment():
    await generate(10)
    await generate(11)
```

两组输出完全相同：

```text
A: with assignment
start 10
end 10
start 11
end 11
B: without assignment
start 10
end 10
start 11
end 11
```

`first =` 和 `second =` 只保存返回值。即使不保存，`await` 也要等这份调用返回后，才能继续下一行。

[下载 comparison.py，运行这两组对比](comparison.py)。这是独立的标准库语言实验，不是 Slime 原始源码。

## 暂停之后，为什么还是先完成 10

当前实验只有这一条执行链。第二个 `generate` 还没开始，不能因为第一份内部暂停，就自动提前运行第二行。

这里的 `sleep(0)` 让出一次后可以很快恢复；如果换成 `sleep(1)`，即使没有其他工作，也要等计时条件满足。**没有别的工作可运行，不等于这次等待被跳过。**

<span id="sleep-time-and-execution"></span>

### 等待时间与代码执行要分开看

> **对于 `await asyncio.sleep(...)`，等待时间继续流逝，但当前协程的代码暂时不向下执行。**

```python
await asyncio.sleep(2)
print("继续执行")
```

这两秒里，协程停在 `await`，还不会执行后面的 `print`。这叫挂起，不是退出或终止；也不是函数体在后台继续跑。

两秒到了，只是满足了继续执行的条件。还要轮到这个协程获得执行机会，后面的 `print` 才会运行。其他代码执行所消耗的时间，不会让这次 sleep 的等待重新计时。

下一节再学习怎样安排另一份工作。在学到那里之前，先不要求从本实验中看出交错执行。

## 不只有 sleep 才能暂停

关键是等待的操作是否需要暂停，而不是函数名叫不叫 `sleep`。`asyncio.sleep()` 本身也是协程；网络读取等异步操作也可能需要等待。反过来，协程如果一路执行到 `return`，没有遇到需要暂停的操作，也可以直接返回。

因此，看见 `await` 时先问两件事：

1. 这一行要等谁的返回结果？
2. 被等待的代码内部，在哪里需要暂停？

## 回到 Slime：等待完成标记

`_await_done_marker()` 会先等待一段时间，再读取外部命令的完成标记。如果标记还没出现，就继续下一轮；读取成功时才返回退出码。

这里只关注三处顺序：`await asyncio.sleep(5)`、`await sb.exec(...)`、`return`。`sb.exec` 是执行环境提供的异步操作，具体实现在后续源码阅读时展开。

<details>
<summary>展开 Slime 源码：_await_done_marker 的等待与返回</summary>

{{< source-reference id="source-1" >}}

</details>

## 用自己的话回答

第一份 `generate` 内部等待过，为什么第二份还没有开始？去掉 `first =` 会改变顺序吗？

<details><summary>查看解释</summary>

内部等待只是第一份调用执行过程中的暂停。第一份还没返回，外层就还没执行到第二行。赋值只保存结果，去掉它不改变直接 `await` 的先后顺序。

</details>

语义核对：[协程](https://docs.python.org/3.12/library/asyncio-task.html#coroutines)、[sleep](https://docs.python.org/3.12/library/asyncio-task.html#sleeping)。

{{< python-async-coverage lesson="02-await" >}}

---

[专题首页](../) · [上一节](../01-async-def/) · [下一节：03 · Task 与 gather：把多份工作安排起来](../03-tasks/) · [源码与教程对照](../coverage/) · [全部用法](../usage-index/)
