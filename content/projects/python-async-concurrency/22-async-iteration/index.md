---
title: "22 · async for / 异步生成器：逐项等待异步产出"
description: "从创建异步生成器到逐项消费，沿输出看清 await 的等待、yield 的交接，以及为什么 async for 不会自动并发。"
weight: 220
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. async for / yield：结果一项项到来时，怎样逐项使用？

第 21.4 课已经用过 `yield`：准备好资源后交给使用区，退出时再恢复清理。那一课的函数经过 `@asynccontextmanager` 装饰，供 `async with` 使用。

现在的要求是：**数据可能逐项准备好，我们想拿到一项就处理一项，不必先收齐整份列表。**

普通协程可以用 `await` 等待，最后 `return` 一个列表；这能取得完整结果，但调用方要等到它返回。另一种形式是让函数通过多次 `yield` 逐项产出，调用方使用 `async for` 逐项读取。

先把本课与前课的对象分清：

| 函数的形式 | 调用后得到什么 | 调用方怎样使用 |
| --- | --- | --- |
| 不含 `yield` 的 `async def`，通过 `return` 给结果 | 协程对象 | `await` 等待一次结果 |
| 本课的 `async def`，函数体含 `yield` | 异步生成器对象 | `async for` 逐项读取 |
| 第 21 课加了 `@asynccontextmanager` 的函数 | 异步上下文管理器 | `async with` 管理进入和退出 |

本课先掌握“创建 → 请求下一项 → yield 交接 → 处理 → 再请求”。协议内部的方法留到需要时查阅。

<span id="async-iteration"></span>

## 2. ensure_async_iterator：创建对象，然后逐项消费

本例从 verl 的真实函数 `ensure_async_iterator(iterable)` 裁剪，保留函数名、参数以及 `for item in iterable: yield item`。这里只接受普通列表，暂时省略原实现接收异步输入的分支。

为了看见“准备一项时可以等待”，教学版额外加入 `sleep(0)` 和打印；**原函数的同步输入分支没有这个等待**。这里不读取网络、权重文件或模型。

<span id="yield-reading-guide"></span>

**读代码时先记住：调用方请求一项时，生成器先执行到 `yield` 并交出 `item`；后面的代码要等调用方再次请求下一项时才继续。**

[下载 example.py](example.py)，运行 `python3 example.py`。沿用 Python 3.11 及以上的课程环境，实际验证版本为 Python 3.12.3。左侧行号对应下载文件。

<div class="async-coordination-code">

```python
import asyncio


async def ensure_async_iterator(iterable):
    for item in iterable:
        print("source preparing", item)
        await asyncio.sleep(0)
        print("source yield", item)
        yield item
        print("source resumed", item)
    print("source exhausted")


async def exercise():
    stream = ensure_async_iterator([10, 11])
    print("stream created")
    async for item in stream:
        print("body received", item)
        await asyncio.sleep(0)
        print("body finished", item)
    print("loop finished")


if __name__ == "__main__":
    asyncio.run(exercise())
```

</div>

这里 `iterable` 是输入列表，`stream` 是交给 `async for` 读取的异步生成器。两个 `item` 是两个函数各自的局部变量：生成器用 `yield item` 交出当前值，`async for item in stream` 把这一项赋给消费方的 `item`。

`stream` 是一份带有执行位置的异步生成器对象。L15 只是创建它，函数体还没开始，所以第一条输出是 `stream created`。

<span id="async-iteration-output"></span>

## 3. await / yield：沿实际输出看等待和交接

下面按运行顺序列出全部输出。此例只有 `exercise` 这一份 Task；生成器与消费方是在同一份 Task 内交接，不是两份后台任务。

| 实际输出 | 执行位置与这一步发生的事 |
| --- | --- |
| `stream created` | L15–16：只创建 stream，没有运行生成器函数体 |
| `source preparing 10` | L17 请求第一项，进入生成器的 L5–6 |
| `source yield 10` | L7 的等待完成后到 L8；下一行 L9 将交出 10 |
| `body received 10` | L9 交出值并暂停生成器；L17 接住 10，进入循环体的 L18 |
| `body finished 10` | L19 等待完成后运行 L20；此时生成器仍停在 L9 |
| `source resumed 10` | 循环体结束，L17 再请求下一项；生成器才从 L9 后面的 L10 恢复 |
| `source preparing 11` | 生成器的普通 for 进入下一轮，到 L6 准备 11 |
| `source yield 11` | L7 再次等待完成，到 L8；下一行 L9 交出 11 |
| `body received 11` | L17 接住 11，运行 L18；生成器又停在 L9 |
| `body finished 11` | L19 等待完成，运行 L20 |
| `source resumed 11` | L17 再请求下一项，生成器从 L9 后面的 L10 恢复 |
| `source exhausted` | L5 的普通 for 已经结束，执行 L11；生成器随后结束 |
| `loop finished` | L17 得知没有下一项，正常结束 async for，才执行 L21 |

### 3.1 await：等待准备或处理，可能让当前 Task 挂起

L7 的 `await asyncio.sleep(0)` 在准备数据的一侧；L19 的等待在消费数据的一侧。两处 sleep 都会让当前 Task 挂起一次，事件循环可以运行其他已就绪任务。本例没有额外创建其他任务。

`async for` 每次取下一项，也要等待异步迭代对象完成这次请求。请求可能需要实际等待，也可能立刻取得一项，不能只凭看见 `async for` 就认定发生了任务切换。

### 3.2 yield：交出这一项，暂停在这个位置

本例先打印 `body finished 10`，`async for` 才请求下一项，让生成器从 L9 后面的 L10 继续，打印 `source resumed 10`。L19 即使包含等待，生成器也不会趁这个等待自动准备 11。

这两个动作要分别理解：`await` 等待某个操作，`yield` 交出一项并保留生成器的执行位置。

### 3.3 async for：先完成这一轮循环体，再请求下一项

此例每一轮都遵循“准备一项 → 交给循环体 → 处理完 → 再请求”的顺序。`async for` 没有把每一轮循环体自动变成独立任务。

如果以后需要同时处理多项，就要另外安排任务并控制并发数量；本课先保留顺序消费，避免把“逐项到来”和“并发处理”混在一起。

<span id="async-iteration-boundaries"></span>

## 4. async for：几个容易混淆的边界

### 4.1 await / 普通 for：都不能直接消费本例的 stream

`stream` 不是普通协程对象，也不是普通同步迭代对象。[wrong_consumption.py](wrong_consumption.py) 用同一个函数验证了两种错误写法：

```text
stream created
await stream: TypeError
for item in stream: TypeError
```

这里应使用 `async for item in stream`。不要把 `async for` 理解成“先 await 出一个完整列表，再对列表做普通 for”；它是在逐次请求下一项。

### 4.2 async for：没有实际等待时，可以连续完成多轮

原函数的同步输入分支很短：

```python
async def ensure_async_iterator(iterable):
    for item in iterable:
        yield item
```

[no_wait.py](no_wait.py) 使用这个版本，先创建一份 `other_work` 任务，再用没有 await 的循环体消费 10、11，最后 `await task`。默认任务工厂下，输出是：

```text
item 10
item 11
loop finished
other task
```

原因是取项和循环体都能立即继续，前面的 async for 没有把执行机会让给 `other_work`；最后等待 task 时，另一份任务才开始运行。这也说明：**把同步数据包成异步生成器，不会自动把同步工作变成非阻塞工作。**

### 4.3 生成器结束后：同一个对象不会从头再来

本例读完 11 后，还会再请求一次，才发现没有下一项。空列表则第一轮就没有可交出的值，不执行循环体。

已经读完的同一个 `stream` 再次用于 async for，不会重新产出 10、11。想再执行一遍，应重新调用 `ensure_async_iterator([10, 11])` 创建新对象。

### 4.4 break / 异常：提前停止的清理留到下一课

本课主例子会读到自然结束。提前 break、循环体报错或取消时，不能据此推断生成器已经运行到末尾，更不能依赖它立即完成所有清理。

第 23.1 课将用 `contextlib.aclosing` 给提前停止时的关闭安排明确位置。这里先记住：**停止消费，与生成器自然读完，是两件事。**

<span id="async-iteration-takeaways"></span>

## 5. async for / yield：带走三条结论

1. **调用含 yield 的 async def，得到异步生成器对象，函数体此时还没开始。** 本课用 async for 消费它，不直接 await 它。
2. **每次 yield 交出一项；下一次请求才从 yield 后面恢复。** 等待准备数据和等待循环体工作，都不等于自动生产下一项。
3. **async for 逐项请求，循环体仍按顺序完成。** 读完、提前停止、并发处理分别有不同的行为与责任。

试着不看上面的解释回答：

1. 为什么 `stream created` 先于 `source preparing 10`？
2. `body received 10` 后，生成器停在哪里？
3. 为什么 `source resumed 10` 在 `body finished 10` 后面？
4. 为什么 no_wait.py 的 `other task` 最后才出现？

<details>
<summary>查看自查解释</summary>

1. 创建异步生成器不执行其函数体，第一次请求下一项才开始。
2. 停在交出 10 的 yield；消费方正在运行自己的循环体。
3. 循环体先完成，再由 async for 请求下一项；这个请求才恢复生成器。
4. 该例取项与循环体都没有需要挂起的操作，最后 await task 才给另一份任务执行机会。

</details>

提前停止时怎样关闭异步生成器，保留在[第 23.1 单元的 aclosing 规划](../learning-route/#curriculum-stage-protocols)。本轮先进入高频线程主线：[26 · asyncio.to_thread：把阻塞函数交给线程](../26-to-thread/)。

{{< python-async-slime title="按需阅读：项目用法、源码证据与语义核对" >}}

## ensure_async_iterator：把输入统一交给异步循环消费

本节使用四库统计已经固定的 verl 提交 `1d367a4f459a43768f76312c0d3430a99ec46b8c`。本地仓库当前 HEAD 与该版本不同；已通过本地 Git 读取固定提交的文件，并与保存的快照逐字及哈希核对。

原函数接受的输入可能本来就能异步迭代，也可能只是普通可迭代对象。它分别读取输入，再用 yield 逐项交给调用方；本课只裁剪了第二个分支。

{{< source-reference id="source-1" >}}

调用方 `get_named_tensor_buckets` 从输入中逐项取得 `(name, tensor)`，再处理当前权重项。这里只观察 async for 的取项位置；张量大小与分桶逻辑不属于本课。

{{< source-reference id="source-2" >}}

教学裁剪保留了 `ensure_async_iterator(iterable)` 和同步输入分支；删除了原函数通过 `hasattr` 选择异步输入的部分。打印和两处 sleep 用于展示执行顺序，不代表原函数会等待网络或主动安排并发任务。

## 语义核对：Python 文档与 Fluent Python

本课依据 [Python 3.12 的 async for 语句](https://docs.python.org/3.12/reference/compound_stmts.html#the-async-for-statement)和[异步生成器函数](https://docs.python.org/3.12/reference/expressions.html#asynchronous-generator-functions)核对；实际运行版本为 Python 3.12.3。

**书上怎么说：**《Fluent Python》第 2 版第 21 章，Asynchronous Iteration and Asynchronous Iterables：

> Similarly, `async for` works with asynchronous iterables: objects that implement `__aiter__`.

官方中译对应原句：

> 类似地，`async for` 处理异步可迭代对象，即实现了 `__aiter__` 的对象。

本地镜像位置：英文 `corpus/en/ch21.md:1087–1110`，中文 `corpus/zh/ch21.md:1053–1076`，共同锚点 `asynchronous-iteration-and-asynchronous-iterables`。本书基于 Python 3.10；本节基础语义已用上述文档和 Python 3.12.3 的实验交叉核对。

**我的判断（教学安排）：**先使用异步生成器理解创建、逐项交接与顺序消费；书中提到的协议方法名只用于核对出处，本课不要求自行实现协议类。提前停止后的关闭由下一课展开。

下面的用法索引沿用 Slime 固定资料集，与上面主例子的 verl 来源分开保留。

{{< python-async-coverage lesson="22-async-iteration" >}}

{{< /python-async-slime >}}

---

[上一节：21.6 · Task.cancel：使用区被取消后怎样关闭](../21-context-cancellation/) · [返回学习路线](../learning-route/)
