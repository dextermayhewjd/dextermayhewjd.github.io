---
title: "20 · asyncio.Event：让任务等待一个通知"
description: "用一个共享标志控制任务何时继续，分清 set、wait、clear，以及唤醒、执行、完成之间的关系。"
weight: 200
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

## 1. asyncio.Event：任务已经启动，怎样等到允许后才继续？

第 19 课用 Lock 保护共享修改，同一时刻只让一份任务进入。现在增加一个要求：**取样任务已经安排好了，但控制方还没准备好，希望取样任务先等着，收到“可以继续”的通知后再返回样本。**

Lock 解决的是谁能独占进入一段操作，没有直接表示“已经准备好”这个状态。Queue 可以专门约定一条消息作为通知；这次只需要一个“允许 / 尚未允许”的标志，就可以使用 `asyncio.Event`。

先只认识一个 Event 对象：它内部保存一个布尔标志，初始是 `False`。需要等待的一方调用 `wait()`，允许继续的一方调用 `set()`。

<span id="event-notification"></span>

## 2. Event / wait / set：共享同一个标志，分别等待和通知

### 2.1 Event：先分清对象、方法和返回值

| 写法 | 做什么 | 返回什么 |
| --- | --- | --- |
| `release = asyncio.Event()` | 创建一个标志初始为 `False` 的 Event | Event 对象 |
| `await release.wait()` | 标志为 `False` 时等待；为 `True` 时可直接完成 | `True` |
| `release.set()` | 把标志设成 `True`，使当前等待者可以继续 | `None` |
| `release.clear()` | 把标志重新设成 `False`，影响后续开始的等待 | `None` |

`wait()` 需要 `await`；`set()` 和 `clear()` 是普通方法，不需要 `await`。这里的 `release` 是保存 Event 对象的变量名，通知动作是它的 `set()` 方法。[Python 3.12 Event 文档](https://docs.python.org/3.12/library/asyncio-sync.html#event)

### 2.2 create_task + Event：先让 fetch 等住，再允许它返回

这份标准库实验沿用 Slime 测试里的 `fetch(count)`、`group` 和 `release` 命名，保留“等到允许后返回样本组”的关系。用字符串代替真实样本，暂时只保留一个通知对象；真实测试的两个通知对象放在文末回查。

`fetch` 定义在 `exercise` 里面，可以使用这次 `exercise` 创建的 `release` 和 `group`。`count` 沿用取样接口，本例固定传入 1。

[下载 example.py](example.py)，运行 `python3 example.py`。最低 Python 3.11；本次在 Python 3.12.3、默认任务调度方式下验证。左侧行号对应下载文件。

<div class="async-coordination-code">

```python
import asyncio


async def exercise():
    release = asyncio.Event()
    group = ["sample"]

    async def fetch(count):
        print("fetch waiting")
        allowed = await release.wait()
        print("fetch resumed", allowed)
        return [group]

    task = asyncio.create_task(fetch(1))
    await asyncio.sleep(0)
    print("main set")
    release.set()
    print("main after set")
    print("received", await task)


if __name__ == "__main__":
    asyncio.run(exercise())
```

</div>

这里的 `sleep(0)` 只是让主任务让出本轮执行，以便展示 `fetch` 先进入等待。Event 也允许**先 set、后 wait**：只要开始 wait 时标志已经为真，它就不必等下一次通知。

<span id="event-swimlanes"></span>

### 2.3 wait / set：沿泳道区分通知、恢复和完成

图里先认清两份任务：**MAIN 是正在运行 `exercise()` 的主任务；FETCH 是 L14 创建、负责执行 `fetch(1)` 的任务。** `FLAG` 是同一个 Event 的许可标志，表示是否允许继续，不表示 fetch 是否完成。

从上往下读，每行只记录一份任务的动作。`T` 是执行顺序，`L` 对应上面代码的行号；空白列表示这一步没有执行该任务，先前的等待持续到它自己的 `RESUME`。

<div class="async-event-lanes">

```text
# T = 本次执行顺序；L = example.py 的真实行号。
# 每行只记录一份任务的执行；空白列的等待持续到该任务的 RESUME。
# FLAG 是同一个 release 对象里的标志，不是 fetch 的返回值。
# +------+-------------------------------+----------------------------+-------+
# | STEP | MAIN                          | FETCH                      | FLAG  |
# +------+-------------------------------+----------------------------+-------+
# | T01  | L5-14 create Event and Task   |                            | False |
# | T02  | L15 WAIT: next turn           |                            | False |
# | T03  |                               | L9-10 WAIT: set at T04     | False |
# | T04  | L16-18 RESUME; set; after set |                            | True  |
# | T05  | L19 WAIT: FETCH END           |                            | True  |
# | T06  |                               | L10-12 RESUME; return; END | True  |
# | T07  | L19 RESUME; print received    |                            | True  |
# +------+-------------------------------+----------------------------+-------+
# T02: MAIN 在 L15 让出本轮执行，FETCH 才开始运行。
# T03: FETCH 在 L10 等 release.set()，没有执行 L11、L12。
# T04: MAIN 在 L17 设置标志；FETCH 可以恢复，但 MAIN 继续执行 L18。
# T05: MAIN 在 L19 等 FETCH 结束；这次等待的是 task，不是 Event。
# T06: FETCH 到这里才从 L10 恢复，wait() 返回 True，L12 返回样本组列表。
# T07: MAIN 的 await task 得到样本组列表，随后 print。
```

</div>

[下载注释泳道图 execution-flow.py](execution-flow.py)。先看最关键的三处：

1. **T03 / L10：fetch 等“允许继续”。** 它停在 `await release.wait()`；这里等的是 Event 的标志。
2. **T04 / L17–18：main 已通知，仍接着执行。** `release.set()` 把标志设为真，让 fetch 可以恢复；它不会直接跳到 fetch，所以 L18 先打印。
3. **T05–T07 / L19：main 改为等“fetch 做完”。** main 在 `await task` 挂起后，fetch 才从 L10 恢复，执行到 return；main 最后拿到返回值。

<span id="event-output"></span>

把图和实际输出对照起来：

| 实际输出 | 正在执行什么 |
| --- | --- |
| `fetch waiting` | T03 / L9：随后在 L10 等待 `release.set()` |
| `main set` | T04 / L16：主任务准备调用 `set()` |
| `main after set` | T04 / L18：set 已返回，fetch 还没执行后面的代码 |
| `fetch resumed True` | T06 / L11：fetch 恢复，L10 的 wait 已返回 `True` |
| `received [['sample']]` | T07 / L19：await task 已取得 fetch 的返回值 |

**`set()` 让等待者可以继续，不会替它把函数执行完。** 本例中，主任务先打印 `main after set`，直到 `await task` 挂起，`fetch` 才恢复执行。

这里还有两种不同的返回值：L10 的 `await release.wait()` 得到的是标志许可 `True`；L19 的 `await task` 得到的才是样本组列表。数据由函数正常返回，Event 没有携带这份数据。

<span id="event-set-clear"></span>

## 3. set / wait / clear：保存的是标志，wait 不消耗一次通知

### 3.1 set / wait：重复设置和重复等待都不计数

在异步函数里运行下面的片段：

```python
release = asyncio.Event()
release.set()
release.set()
print("first wait", await release.wait())
print("second wait", await release.wait())
```

两行都打印 `True`，也都不需要挂起。两次 set 后，标志仍然只是 `True`；第一次 wait 返回后，标志也仍然是 `True`。

因此 **wait 不会自动 clear，也不会“取走一条通知”**。如果每份工作必须单独交接、逐项消费，前面学过的 Queue 更适合表达这种要求。

### 3.2 clear / wait：重新关闭标志，后面的等待需要下一次 set

接着上一段，在同一个异步函数里继续：

```python
release.clear()
task = asyncio.create_task(release.wait())
await asyncio.sleep(0)
print("waiting after clear", not task.done())
release.set()
print("after next set", await task)
```

输出：

```text
waiting after clear True
after next set True
```

第一行的 `True` 来自 `not task.done()`，表示任务尚未结束；第二行的 `True` 来自 wait 的返回值。含义不同。完整可运行版本见 [flags.py](flags.py)。

`clear()` 本身不等待，也不负责等上一轮任务完成。复用同一个通知对象时，应先确认上一轮工作已完成，再清除标志、安排下一轮等待。

### 3.3 clear：不会撤回已经唤醒的等待者

如果一份任务已经在 `wait()` 里等待，你先 set，紧接着 clear，它仍然可以从这一次 wait 返回；clear 会让**随后开始等待**的任务等待下一次 set。

这意味着不能用 `set(); clear()` 表示“只让谁抢到就算谁”。在 [set_then_clear.py](set_then_clear.py) 中，先前的等待者返回 `True`，新等待者则继续等：

```text
already awakened True
new waiter blocked True
new waiter released True
```

最后一行是在再次调用 set 后才发生的。本课按已经开始等待和后面才开始等待来区分它们，不用执行快慢猜谁能接到通知。

<span id="event-broadcast"></span>

## 4. Event.set：一次通知可以让多个等待者继续

如果 A、B 都在等待同一个 Event，一次 set 会让它们都可以恢复。运行 [broadcast.py](broadcast.py)，实际输出：

```text
A waiting
B waiting
main after set
A continued
B continued
all finished
```

1. A、B 各自在同一个 `ready.wait()` 处挂起。
2. 主任务调用 `ready.set()`，然后继续打印 `main after set`。
3. 主任务离开 TaskGroup、等待组内任务时，A、B 才先后恢复；组内任务结束后打印 `all finished`。

这里 A、B 后续仍由事件循环安排，不能把一次 set 理解成“同一时刻执行完两份工作”。它也没有规定只许一份工作进入。

| 机制 | 本课范围内，它表达的关系 |
| --- | --- |
| `asyncio.Event` | 标志满足后，所有等待这个通知的任务都可以继续 |
| `asyncio.Lock` | 使用同一把锁的任务，一次只允许一份进入保护区 |
| `asyncio.Queue` | 放入和取走一份份数据，空或满时等待 |

如果收到通知以后还要共同修改同一份状态，可以在后面的修改处继续使用第 19 课的 Lock。

<span id="event-cancellation"></span>

## 5. Task.cancel / Event.wait：取消等待者，不会自动设置标志

Event 没有“归还许可”这一步。取消一份正在 wait 的任务，会让它按已有的取消规则退出等待、执行自身清理；不会因此通知其他等待者。

在 [cancellation.py](cancellation.py) 中，A、B 先等待同一个未设置的 Event。取消 A 并等待其收尾后，会看到：

```text
A waiting
B waiting
A cleanup
A cancelled
B still waiting True
B continued
B cleanup
```

`B still waiting True` 说明 A 的取消没有放行 B。最后两行发生在主任务明确 `ready.set()` 之后。

写的时候检查：**哪份任务负责 set？如果它报错或取消，谁负责结束剩余等待？** Event 不会自动识别通知者已经失败。需要时，用已学过的 TaskGroup 管理这一组任务的失败与收尾，或用 `wait_for` / `timeout` 限制等待时间；不要让一次永远不会发生的通知悬在那里。

<span id="event-takeaways"></span>

## 6. Event：带走三条结论

1. **同一个 Event 保存一个布尔标志。** wait 等它允许继续，set 将它设为真，clear 将它设为假；两边要使用同一个对象。
2. **set、恢复执行和任务完成，是三个不同阶段。** set 让等待者可以继续；要确认工作完成，仍然等待对应的 Task。
3. **wait 不消费标志，set 可以通知多个等待者。** clear 影响后续等待，不撤回已经发生的唤醒；Event 也不传递业务数据或提供互斥。

试着回答：

1. 如果在创建 fetch 任务之前就先 set，它还需要等一次新的 set 吗？
2. set 两次之后，wait 三次，第三次需要等吗？
3. 为什么 `main after set` 可以先于 `fetch resumed True` 打印？
4. Event 返回的 `True` 和 fetch 返回的 `[['sample']]` 是同一个返回值吗？

<details>
<summary>查看自查解释</summary>

1. 不需要。只要开始 wait 时标志仍为真，它就能直接返回。
2. 如果没有 clear，三次都能直接返回；Event 不记录两份可消费的通知。
3. set 使 fetch 可以恢复，但不会抢走主任务的执行；主任务随后在 await task 处等待，fetch 才继续。
4. 不是。wait 返回 `True`；fetch 的 return 交出样本列表，再由 await task 取得。

</details>

下一课会从通知回到资源的使用与退出：**怎样把异步资源的准备、使用和清理组织成一个可复用的作用域？** 先从[21.1 · try/finally：分清准备、使用和关闭](../21-resource-lifecycle/)开始。

{{< python-async-slime title="按需阅读：Slime 如何用两个 Event 固定取样与暂停的顺序" >}}

## _generate_group → fetch：一个通知“已进入”，一个通知“可以返回”

以下是 Slime 固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f` 的测试。已确认的本地仓库路径本次不可用，已从 GitHub 这个提交重新核对，文件哈希与已保存快照一致。

沿同一次测试阅读：

1. 测试安排 `worker._generate_group(0)`，这条调用链进入替换后的 `fetch(count)`。
2. fetch 用 `entered.set()` 告诉测试“已经进入这里”，随后在 `release.wait()` 等待。
3. 测试先 `await entered.wait()`，确认取样在途，接着 `await worker._pause()` 执行暂停。
4. 测试再调用 `release.set()`，允许 fetch 返回；最后 `await task`，检查样本被放回缓冲。

{{< source-reference id="source-1" >}}

两个 Event 各保存自己的标志：`entered` 传递“我已经到达”，`release` 传递“现在可以继续”。主例子暂时删去 entered 和真实 worker、暂停及缓冲逻辑，用一次 `sleep(0)` 展示先进入等待的顺序；真实测试使用明确的 entered 握手确认位置，不靠固定睡眠猜测。

原始 `fetch(count)` 在该测试中直接返回 `[group]`，主例子保留了这个输入与返回形状，字符串代替真实 Sample。测试中的其他对象与业务检查不属于本课新增 API。

## Event.wait / set / clear：核对范围与全部使用位置

本次按 [Python 3.12 官方文档](https://docs.python.org/3.12/library/asyncio-sync.html#event)和本机 `asyncio/locks.py` 核对：Event 初始标志为假，wait 返回 `True`，set 唤醒当前等待者，clear 重设标志。该对象用于同一事件循环中的任务；操作系统线程间的通知留到后续课程。

源码中还会看到 `event.is_set()`，它只读取当前标志并返回布尔值，不等待，也不改变标志。它可以辅助检查，不能替代 `await event.wait()` 的等待。

{{< python-async-coverage lesson="20-async-event" >}}

{{< /python-async-slime >}}

---

[上一课：19 · asyncio.Lock](../19-async-lock/) · [下一节：21.1 · try/finally](../21-resource-lifecycle/) · [返回学习路线](../learning-route/)
