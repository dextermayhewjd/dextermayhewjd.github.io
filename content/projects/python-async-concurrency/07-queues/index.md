---
title: "18 · asyncio.Queue：让生产者与消费者交接数据"
description: "先创建共享队列，再由生产者 put、消费者 get；沿输出理解队列满与空时的等待、取出和处理完成的区别，以及结束信号。"
weight: 180
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. asyncio.Queue：一边产生数据，一边处理数据，怎样交接？

第 17 课用 Semaphore 限制进入某段工作的任务数量。现在增加一个要求：**一份任务不断产生结果，另一份任务逐个处理结果；处理暂时跟不上时，先把少量结果存起来，存满就让生产者等待。**

Semaphore 管理的是进入许可，没有提供这个存放、取走数据的交接处。普通列表可以保存数据，但列表本身不会在“没有数据可取”或“已经存满”时，替两份任务安排异步等待。

本课用一个共享的 `asyncio.Queue` 完成交接：产生数据的一方叫**生产者**，取走并处理数据的一方叫**消费者**。它们在这里是同一个事件循环中的两份异步任务。

<span id="async-queue"></span>

## 2. Queue / put / get：同一个队列，分别交给两份任务

先把对象和使用位置对应起来：

| 写法 | 放在哪里 | 做什么 |
| --- | --- | --- |
| `outputs = asyncio.Queue(maxsize=1)` | 主程序 `exercise` | 创建一个初始为空、最多放 1 项数据的队列对象 |
| `await outputs.put(value)` | 生产者 `_produce` | 放入一项数据；队列满时等待空位，放入成功后返回 `None` |
| `value = await outputs.get()` | 消费者 `_next` | 取走并返回最早入队的一项数据；队列空时等待数据 |

`_produce(outputs)` 和 `_next(outputs)` 接收的是**同一个队列对象**。像上一课一样，传入对象只是让函数能够使用它；实际交接发生在函数内部的 `put` 和 `get`。

`create_task` 负责安排这两份任务，Queue 负责存放和交接数据。队列不会自己运行生产者或消费者。

## 3. create_task + Queue：先安排消费者，再让生产者放入数据

这份独立标准库实验沿用旧材料中的 `_produce`、`_next` 和 `outputs` 命名；用数值 10、11 代替真实结果，用 `sleep` 代替处理耗时。它不是 Slime 原函数的直接裁剪，原始代码放在文末回查。

本例先创建消费者 Task，让它先尝试从空队列取数据。泳道图按时间向下读，**每一行只记录一个任务正在执行的动作，其余任务列留空**。空白表示这一行没有执行该任务；之前的等待持续到它自己的恢复行。

**`T01、T02…` 是执行顺序，`L7、L17…` 是下面 `example.py` 的真实行号。** 左侧行号可以直接定位代码，右侧 `QUEUE` 是该步结束时的队列内容。行号范围用于定位这一段代码，不表示范围内每个分支都执行过。

`WAIT` 标出挂起的代码行和要等待的条件；`RESUME` 表示真正恢复执行。图下备注逐项写明“谁在等谁的哪一步”；其中 `sleep` 等的是计时结束，`gather` 等的是两份任务结束。

<div class="async-queue-walkthrough">
<div class="async-queue-lanes" id="queue-swimlanes">

### 3.1 await：在泳道中看挂起、腾出空位和恢复

```text
# 一行只记录一个任务执行；其余任务列留空，之前的等待会持续到 RESUME。
# T = 执行顺序；L = example.py 的真实行号。P = 生产者；C = 消费者。
# WAIT = 在该行挂起；RESUME = 从等待处恢复；OK = 直接完成；END = 任务结束。
# +------+----------------------+-----------------------------+------------------------------+--------+
# | STEP | MAIN                 | PRODUCER                    | CONSUMER                     | QUEUE  |
# +------+----------------------+-----------------------------+------------------------------+--------+
# | T01  | L28-30 setup         |                             |                              | []     |
# | T02  | L31 WAIT: P+C END    |                             |                              | []     |
# | T03  |                      |                             | L16-17 WAIT: data from T04   | []     |
# | T04  |                      | L6-8 put(10) OK             |                              | [10]   |
# | T05  |                      | L6-7 WAIT: space from T06   |                              | [10]   |
# | T06  |                      |                             | L17-21 RESUME; get(10)       | []     |
# | T07  |                      |                             | L22 WAIT: timer 0.1s         | []     |
# | T08  |                      | L7-8 RESUME; put(11)        |                              | [11]   |
# | T09  |                      | L9 WAIT: space from T11     |                              | [11]   |
# | T10  |                      |                             | L22-24 RESUME; process(10)   | [11]   |
# | T11  |                      |                             | L16-21 get(11) OK            | []     |
# | T12  |                      |                             | L22 WAIT: timer 0.1s         | []     |
# | T13  |                      | L9-10 RESUME None; END      |                              | [None] |
# | T14  |                      |                             | L22-24 RESUME; process(11)   | [None] |
# | T15  |                      |                             | L16-20 get(None); END        | []     |
# | T16  | L31-32 RESUME; print |                             |                              | []     |
# +------+----------------------+-----------------------------+------------------------------+--------+
# T02: MAIN 停在 L31，等 P 在 T13 结束、C 在 T15 结束，T16 才恢复。
# T03: C 停在 L17，等 P 在 T04 的 L7 放入 10；C 到 T06 才恢复。
# T05: P 停在 L7，等 C 在 T06 的 L17 取走 10；P 到 T08 才恢复。
# T09: P 停在 L9，等 C 在 T11 的 L17 取走 11；P 到 T13 才恢复。
# T07/T12: C 停在 L22，等 0.1 秒计时结束，不是等生产者；T10/T14 恢复。
# 条件满足只表示可以继续，不会立即打断当前仍在运行的任务。
```

</div>
<div class="async-queue-code">

### 3.2 put / get：按 T 顺序与 L 行号回到代码

```python
import asyncio


async def _produce(outputs):
    for value in (10, 11):
        print("put request", value)
        await outputs.put(value)
        print("put done", value)
    await outputs.put(None)
    print("producer finished")


async def _next(outputs):
    values = []
    while True:
        print("get request")
        value = await outputs.get()
        if value is None:
            print("consumer finished")
            return values
        print("get", value)
        await asyncio.sleep(0.1)
        print("processed", value)
        values.append(value)


async def exercise():
    outputs = asyncio.Queue(maxsize=1)
    consumer = asyncio.create_task(_next(outputs))
    producer = asyncio.create_task(_produce(outputs))
    _, values = await asyncio.gather(producer, consumer)
    print("received", values)


if __name__ == "__main__":
    asyncio.run(exercise())
```

</div>
</div>

[下载 example.py](example.py) · [下载注释泳道 execution-flow.py](execution-flow.py) · 运行：`python3 -W error example.py`。本课使用 Python 3.12。

`while True` 让消费者反复取数据；遇到本例约定的 `None` 时，通过 `return values` 结束。`gather(producer, consumer)` 仍按传入顺序收集两个任务的返回值：生产者正常结束返回 `None`，用 `_` 接收；消费者返回处理后的列表，用 `values` 接收。

<span id="queue-execution-trace"></span>

### 3.3 await：需要时核对每一行输出

上面的泳道已经标明任务交接。下面保留同一次运行的逐行输出核对，每条输出对应发生它的 T 步骤；编号本身不会打印。同一步骤可以连续打印多行，不表示发生了任务切换。

输出开始前，主协程 `exercise` 已经创建两个 Task，并运行到 `await asyncio.gather(producer, consumer)`。它在这里挂起等待两份任务结束，事件循环随后运行已安排的任务。

<details>
<summary>展开按 T 步骤核对的实际输出</summary>

<table class="async-output-trace">
<thead><tr><th scope="col">编号与实际输出</th><th scope="col">谁执行到哪里，是否挂起或恢复</th></tr></thead>
<tbody>
<tr><td><strong>[T03]</strong><br><code>get request</code></td><td><strong>消费者</strong>准备调用 <code>await outputs.get()</code>。队列为空，随后在这里<strong>挂起</strong>，等生产者放入数据。</td></tr>
<tr><td><strong>[T04]</strong><br><code>put request 10</code></td><td><strong>生产者</strong>准备调用 <code>await outputs.put(10)</code>。队列有空位，这次放入可以<strong>直接完成，不挂起</strong>。</td></tr>
<tr><td><strong>[T04]</strong><br><code>put done 10</code></td><td><strong>生产者</strong>已经放入 10，继续执行下一轮循环。消费者虽然已可继续，但此时不会直接插进生产者的执行过程。</td></tr>
<tr><td><strong>[T05]</strong><br><code>put request 11</code></td><td><strong>生产者</strong>准备调用 <code>await outputs.put(11)</code>。10 还占着唯一位置，随后在这里<strong>挂起</strong>，等消费者取走数据。</td></tr>
<tr><td><strong>[T06]</strong><br><code>get 10</code></td><td><strong>消费者恢复</strong>，之前等待的 <code>get()</code> 已取到 10，队列腾出位置。打印后执行 <code>await asyncio.sleep(0.1)</code>，又在处理等待处<strong>挂起</strong>。</td></tr>
<tr><td><strong>[T08]</strong><br><code>put done 11</code></td><td><strong>生产者恢复</strong>，之前等待的 <code>put(11)</code> 已完成。接着执行没有单独打印的 <code>await outputs.put(None)</code>；队列里还有 11，因此再次<strong>挂起</strong>。</td></tr>
<tr><td><strong>[T10]</strong><br><code>processed 10</code></td><td><strong>消费者从 sleep 恢复</strong>，本例对 10 的处理结束。把 10 加入结果列表，继续下一轮取数。</td></tr>
<tr><td><strong>[T11]</strong><br><code>get request</code></td><td><strong>消费者</strong>再次准备调用 <code>await outputs.get()</code>。队列已有 11，这次可以<strong>直接取到，不挂起</strong>。</td></tr>
<tr><td><strong>[T11]</strong><br><code>get 11</code></td><td><strong>消费者</strong>已经取走 11，队列再次腾出位置。打印后执行 <code>await asyncio.sleep(0.1)</code>，在处理等待处<strong>挂起</strong>。</td></tr>
<tr><td><strong>[T13]</strong><br><code>producer finished</code></td><td><strong>生产者恢复</strong>，之前等待的 <code>put(None)</code> 已完成；结束信号现在在队列里。生产者打印后结束。</td></tr>
<tr><td><strong>[T14]</strong><br><code>processed 11</code></td><td><strong>消费者从 sleep 恢复</strong>，对 11 的处理结束，继续下一轮取数。</td></tr>
<tr><td><strong>[T15]</strong><br><code>get request</code></td><td><strong>消费者</strong>准备再次取数。队列中已有 <code>None</code>，这次 <code>get()</code> 可以<strong>直接完成，不挂起</strong>。</td></tr>
<tr><td><strong>[T15]</strong><br><code>consumer finished</code></td><td><strong>消费者</strong>读到约定的 <code>None</code>，进入 <code>if</code> 分支，返回结果列表并结束。</td></tr>
<tr><td><strong>[T16]</strong><br><code>received [10, 11]</code></td><td><strong>主协程恢复</strong>，<code>gather</code> 已等到两份任务结束，取得返回值后打印结果。</td></tr>
</tbody>
</table>

</details>

注意比较两组输出：`put request 10` 后紧接着 `put done 10`；`put request 11` 后却先出现消费者的 `get 10`。**同样写了 `await put(...)`，是否挂起取决于当时有没有空位。**

<span id="queue-transfer"></span>

## 4. await put / get：先判断等待条件，再判断执行顺序

1. **先问当前操作能否完成。** `put` 有空位就能放入，`get` 有数据就能取走；不能看到 `await` 就直接判定发生了任务切换。
2. **不能完成时，当前任务在 await 处挂起。** 后面的语句要等这次等待结束才能执行；事件循环可以运行其他就绪任务，不是另外开启一个事件循环。
3. **条件满足后，任务才有机会恢复。** 放入数据让等待的消费者可继续，取走数据让等待的生产者可继续；这不代表立刻打断当前任务并切过去。泳道的 T04、T05 里，生产者放入 10 后仍然继续，直到尝试放入 11 时才因队列满而挂起。

泳道解释的是本次运行。实际程序必须保证的关系是“有数据才能取走”和“有空位才能放入”；其他互不依赖的输出怎样交错，要结合实际调度判断。

<span id="queue-capacity"></span>

## 5. Queue.maxsize 与 None：容量限制什么，怎样结束等待？

### 5.1 Queue(maxsize=1)：限制排队数量，不代表处理已经完成

`maxsize=1` 限制的是**已经入队、尚未取走的元素数量**。当消费者手里正在处理 10 时，队列里仍然可以放着 11。

因此，`get()` 取走数据就会腾出位置，不会等后面的处理代码完成才腾位置。生产者也可能还持有一份等待入队的数据；队列容量不是整个程序的内存总量或未完成工作总数上限。

本课显式设置容量 1。省略 `maxsize` 时默认是 0，表示不设置队列元素数量的上限，并不是完全不能放数据。

<span id="queue-stop"></span>

### 5.2 put(None) / get()：结束信号是本例自己约定的

**空队列不会让 `get()` 自动返回 None；它会继续等数据。** 消费者最后能读到 `None`，是因为生产者明确执行了 `await outputs.put(None)`。

本例约定正常数据只有 10、11，所以用 `None` 表示“后面没有数据了”。它和普通数据一样，需要入队、占用位置，再由消费者取出。若业务数据本身允许 `None`，就应换一个不会混淆的结束约定。

这里仅有一个消费者。多消费者、重试和数据持久化不是本课新增的问题。

### 5.3 Task 的退出：队列不会替你管理生产者和消费者

本例假设生产者正常放入结束信号。若生产者提前失败，没有送出结束信号，等待空队列的消费者不会因此自动知道生产已经结束。

这种情况下，需要调用方负责取消并等完相关任务；第 11.1 课的 [TaskGroup 失败与收尾](../11-taskgroup-failures/)可以承担整组失败时的取消管理。取消一个正在等待的 `get` 或 `put`，也不会自动成为发送给另一方的结束通知。

## 6. Queue：带走三条结论，再做自查

1. **共享同一个对象，才能通过队列交接数据。** 主程序创建 Queue，生产者调用 `put`，消费者调用 `get`；Task 的安排与等待仍由调用方负责。
2. **满时 put 等，空时 get 等。** `maxsize` 限制的是队列里尚未取走的数据；取走以后，后续处理不再占用那个队列位置。
3. **数据与结束都需要约定。** `None` 是本例放进去的结束信号，空队列不会自动结束消费者；任务异常或取消后的收尾也仍需管理。

试着回答：

1. 为什么 `put request 11` 和 `put done 11` 中间出现了 `get 10`？
2. `put done 11` 出现时，10 是否已经处理完？这说明 `maxsize=1` 限制的是什么？
3. 如果删去生产者的 `put(None)`，消费者处理完 11 后会怎样？
4. 如果生产者和消费者各自创建一个 Queue，还能按本例这样交接吗？

<details>
<summary>查看自查解释</summary>

1. 10 已占满唯一的位置，生产者要等消费者取走它，才能放入 11。
2. 还没有。容量限制尚未取走的排队数据，不包含消费者已经拿在手里处理的数据。
3. 它会再次调用 `get()`，在空队列上继续等待。生产者结束本身不会关闭这个队列。
4. 不能。它们会各用各的存储与等待条件，生产者放入的数据不会出现在消费者的队列里。

</details>

<span id="queue-practical-pattern"></span>

## 7. Queue / TaskGroup：怎样减少对执行顺序的依赖？

**写程序时，不需要手工安排泳道图中的每一次切换。** 泳道图用于理解本次运行；实际写法要让“有数据才能取、有空位才能放、结束时有人收尾”这些条件成立。这样即使任务快慢或开始顺序改变，交接仍然能完成。

### 7.1 put / get：把等待交给队列，不用睡眠猜先后

1. **先把生产者和消费者都安排起来，再等待它们。** 如果先 `await _produce(outputs)`，等它结束后才调用消费者，容量 1 的队列会让生产者在第二次放入时停住；消费者却还没开始，没人能腾出空位。
2. **直接用 `await put(...)` 和 `await get()` 等条件。** 不必用“先睡一会儿，另一方应该准备好了”来决定能否放入或取走。本课消费者里的 `sleep(0.1)` 只是模拟处理耗时；改变这个时长会改变输出交错，不应改变最终收到的数据。
3. **让双方共用同一个队列，并明确正常结束信号。** 本例生产者正常完成时放入 `None`，消费者读到它才退出。正常数据可能是 `None` 时，需要换一个不会混淆的约定。

### 7.2 TaskGroup：一方失败，取消并等完另一方

主例子的 `gather` 可以完成正常交接；一方失败以后，剩余任务的收尾还要另行管理。沿用第 11.1 课的 TaskGroup，可以把这项责任交给任务组。

下面复用原来的 `_produce` 和 `_next`，只改变安排与等待任务的方式。保存 [with_taskgroup.py](with_taskgroup.py)，与 `example.py` 放在同一目录后运行：

```python
import asyncio

from example import _next, _produce


async def exercise():
    outputs = asyncio.Queue(maxsize=1)
    async with asyncio.TaskGroup() as group:
        consumer = group.create_task(_next(outputs))
        group.create_task(_produce(outputs))
    print("received", consumer.result())


if __name__ == "__main__":
    asyncio.run(exercise())
```

正常路径仍会收到 `[10, 11]`。离开 TaskGroup 后，消费者已经正常结束，可以用已学过的 `result()` 读取它返回的列表。

**如果一方抛出未处理的普通异常，TaskGroup 会请求取消另一方，等它收尾后再向外报告错误。** 例如生产者失败时，正在空队列上等待的消费者会收到取消；消费者失败时，正在满队列上等待的生产者也能被取消。

但 TaskGroup **不会替你发送正常结束信号**。如果生产者正常返回却忘了 `put(None)`，消费者仍可能一直等数据，任务组也会一直等它。正常结束靠双方约定，异常退出靠任务管理，这两件事要分别安排。

### 7.3 Queue：验证结果与退出，不要求每次打印顺序相同

检查这几个条件，比记住完整输出顺序更有用：

1. 交换两份任务的创建顺序、把容量改成 1 或 2，仍能完整收到 10、11。
2. 改变处理耗时，数据仍按入队顺序取出；程序能正常结束。
3. 故意让任意一方报错时，另一方能被取消并完成收尾，错误能报告给调用方。

这些检查针对的是同一个交接约定，而不是期待某一种固定调度顺序。[Queue 等待规则](https://docs.python.org/3.12/library/asyncio-queue.html#queue)与 [TaskGroup 失败处理](https://docs.python.org/3.12/library/asyncio-task.html#task-groups)分别负责数据交接和任务收尾。

下一课增加的问题是：**多份任务跨越 await 修改同一份共享状态，怎样保护这一整段操作？** 见[第 19 课：asyncio.Lock](../19-async-lock/)。

{{< python-async-slime title="按需阅读：Slime 交接流程与旧版同步队列资料" >}}

## _start → _produce → _next：沿同一个 outputs 查原始代码

以下是固定 Slime 快照 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的原始摘录。本次已核对本地连续源码与文件哈希；主例子的两项数据、单消费者和 `None` 结束信号是教学简化，不能直接当作原项目的结束协议。

1. **_start 创建共享队列并安排生产。** 进入结果交接的准备阶段，`self.outputs = asyncio.Queue(maxsize=1)` 保存队列对象，随后创建生产者 Task。

{{< source-reference id="source-1" >}}

2. **_produce 把生成结果放进去。** 内部 `generate_slot` 取得本轮结果，调用 `await self.outputs.put(output)`；队列满时，这份生产任务会等待。它仍可能持有尚未成功入队的结果，因此容量 1 不等于所有内存里只剩一份结果。

{{< source-reference id="source-2" >}}

3. **_next 从同一个队列取走结果。** 它把 `self.outputs.get()` 安排成 Task，同时观察取数和生产者的完成情况；取到数据就返回给上层。原实现还检查生产者错误并在退出时收尾取数任务，因此结束判断比主例子的 `None` 协议更完整。

{{< source-reference id="source-4" >}}

<span id="thread-queue"></span>

## queue.Queue：保留旧版同步队列的回查入口

同步队列将在第 30 单元正式展开。下面保留原课的资料，当前只需要知道它与本课的 `asyncio.Queue` 不同：后者用于同一事件循环中的任务，不保证 OS 线程之间的安全访问。

| 同步队列的写法 | 本次调用的行为 |
| --- | --- |
| `put(value)` | 入队；有界队列满时会阻塞调用线程 |
| `get()` | 取走一项；空队列时会阻塞调用线程 |
| `get_nowait()` | 立刻尝试取走；没有数据时抛 `queue.Empty` |
| `qsize()` / `empty()` | 查看这一刻的状态；其他线程下一刻可能改变队列 |

不能先看 `empty()`，就保证随后 `get()` 一定不阻塞。要表达“没有就算了”，应直接尝试 `get_nowait()` 并处理 `queue.Empty`；`qsize()` 适合观察积压，不是预留结果的操作。异步队列的 `empty()` 也只是状态观察，需要等待数据时使用 `await get()`。

如果使用 `queue.join()` 等待工作完成，消费者要为取出的工作配对调用 `task_done()`；本课主例子使用结束信号和 `gather`，不采用这个完成计数协议。同步、异步和进程队列还需要分别判断等待发生在哪里。

`AsyncRolloutWorker.get_completed_groups()` 使用同步 `queue.Queue`，通过 `get_nowait()` 取走当前已有的结果，遇到 `queue.Empty` 就结束这一轮收集，不等待未来结果。

{{< source-reference id="source-3" >}}

{{< python-async-coverage lesson="07-queues" >}}

语义核对：[Python 3.12 asyncio.Queue](https://docs.python.org/3.12/library/asyncio-queue.html)、[同步 queue.Queue](https://docs.python.org/3.12/library/queue.html#queue.Queue)。

{{< /python-async-slime >}}

---

[专题首页](../) · [上一节：17 · asyncio.Semaphore：限制同时进入的工作](../06-semaphore/) · [下一单元：19 · asyncio.Lock 的规划](../learning-route/#curriculum-stage-coordination) · [完整学习路线](../learning-route/)
