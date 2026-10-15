---
title: "21.4 · asynccontextmanager：把准备和关闭接到 async with"
description: "第 21 单元拆分学习的第 4 步：asynccontextmanager：把准备和关闭接到 async with。"
weight: 214
ShowToc: false
ShowPostNavLinks: false
hideMeta: true
hideInOverview: true
---

> **与已学内容的连接**
>
> **复用的旧知识：** [第 04 课](../04-with-async-with/#async-with-basics)说明 `async with` 会执行管理器提供的进入和退出操作；[21.1](../21-resource-lifecycle/)分清了准备、使用和关闭，[21.2](../21-yield-pause/)观察了交出值与暂停，[21.3](../21-decorators/)说明装饰器怎样接收函数。
>
> **本课新增的问题：** 怎样把我们写好的准备与关闭代码交给管理器，让调用方通过 `async with` 使用资源？

## 1. asynccontextmanager：把已经认识的零件连接起来

21.1 的手动写法已经能完成一次资源使用；如果多个地方都要使用沙箱，每个调用方仍需自己安排准备与关闭。现在希望把这两段规则写在一个入口里，让调用方只写使用区。

标准库的 `asynccontextmanager` 可以把这样的函数转换成创建管理器的入口：**由 async with 在进入时推进准备代码，在离开使用区时恢复关闭代码。**

### 1.1 async def + yield：准备和关闭也需要等待

21.2 用普通 `def` 和 `yield` 观察了交出值与暂停。这里的准备和关闭还需要用 `await` 等待，因此函数要写成 `async def`。

当 `async def` 的函数体里含有 `yield`，它称为**异步生成器函数**：可以在准备与关闭时使用 `await`，也可以通过 `yield` 交出资源并暂停。它与第 01 课中只有 `return` 的协程函数不同。

再加上 `@asynccontextmanager`，装饰后的函数调用会创建供 `async with` 使用的管理器。本节由管理器负责推进其中的异步生成器：进入时推进到 `yield`，正常退出时继续执行后面的关闭代码。调用方不用自己调用 21.2 的 `next()`，也不把创建出的管理器当作协程直接 `await`。

`contextlib` 是 Python 标准库模块名；`from contextlib import asynccontextmanager` 从里面导入本节使用的装饰器。模块名本身不是另一个资源管理机制。

<span id="async-context"></span>

## 2. boot_agent_sandbox：准备、交接与关闭放在同一个入口

沿用 Slime 的真实函数名与 image、instance_id 两个输入；字典和 sleep(0) 是教学替身。原实现的服务启动、工具安装与重试放在文末源码回查中。下面只走正常路径，沿用 Python 3.11 及以上环境，实际在 Python 3.12.3 验证。

[下载 example.py](example.py)，运行 `python3 example.py`。

<div class="async-coordination-code">

```python
import asyncio
from contextlib import asynccontextmanager


@asynccontextmanager
async def boot_agent_sandbox(image, instance_id):
    print("boot", image, instance_id)
    await asyncio.sleep(0)
    sb = {"open": True}
    try:
        yield sb
    finally:
        print("closing", instance_id)
        await asyncio.sleep(0)
        sb["open"] = False
        print("closed", instance_id)


async def exercise():
    manager = boot_agent_sandbox("demo-image", "case-1")
    print("manager created")
    async with manager as sandbox:
        print("inside", sandbox["open"])
        await asyncio.sleep(0)
    print("outside", sandbox["open"])


if __name__ == "__main__":
    asyncio.run(exercise())
```

</div>

实际输出：

```text
manager created
boot demo-image case-1
inside True
closing case-1
closed case-1
outside False
```

<span id="3-async-with--yield按顺序完成一次资源使用"></span>

## 3. async with / yield：沿泳道看进入、交接和退出

从上往下看执行顺序，`L` 对应上方代码行号；等待和交接位置已标在图中。

<div class="async-context-lanes" id="async-context-swimlanes">

```text
# T = 执行顺序；L = example.py 的真实行号。
# 两条泳道共用一个 Task；每行只在一处执行代码。
# CALLER = exercise；RESOURCE = boot_agent_sandbox 的生成器函数体。
# WAIT(loop) = Task 暂停，等事件循环再次调度；RESUME = 从 await 恢复。
# YIELD(sb) = 生成器交出资源并暂停，当前 Task 转回 CALLER。
# ENTER / EXIT = async with 的进入 / 退出调用；它们本身不是挂起标记。
# +------+------------------------------+---------------------------------+------------------------+
# | STEP | CALLER (exercise)            | RESOURCE (boot_agent_sandbox)   | OUTPUT                 |
# +------+------------------------------+---------------------------------+------------------------+
# | T01  | L20-21 create; print         |                                 | manager created        |
# | T02  | L22 ENTER -> T03             |                                 |                        |
# | T03  |                              | L7 print; L8 WAIT(loop)         | boot demo-image case-1 |
# | T04  |                              | L8 RESUME; L9-10 prepare        |                        |
# | T05  |                              | L11 YIELD(sb) -> T06            |                        |
# | T06  | L22 as sandbox; L23 print    |                                 | inside True            |
# | T07  | L24 WAIT(loop)               |                                 |                        |
# | T08  | L24 RESUME; body ends        |                                 |                        |
# | T09  | L22 EXIT -> T10              |                                 |                        |
# | T10  |                              | L11 resume; L13 print           | closing case-1         |
# | T11  |                              | L14 WAIT(loop)                  |                        |
# | T12  |                              | L14 RESUME; L15-16 close; END   | closed case-1          |
# | T13  | L22 exit done; L25 print     |                                 | outside False          |
# +------+------------------------------+---------------------------------+------------------------+
# T02-T05: CALLER 的 L22 还在进入阶段，准备完成后才到 T06 使用资源。
# T03/T11: Task 分别停在 L8/L14；CALLER 不能提前执行使用区或块外代码。
# T05-T06: yield 仅暂停生成器，不把当前 Task 交回事件循环。
# T05-T10: 生成器停在 L11，直到 T09 请求退出，才在 T10 继续。
# T07-T08: Task 停在使用区的 L24；生成器仍停在 L11。
# T09-T12: 使用区已结束；L22 的退出流程再次推进生成器，完成 finally。
# T13: 退出清理已结束，CALLER 才运行 L25；END 表示生成器函数体结束。
```

</div>

[下载注释泳道图 execution-flow.py](execution-flow.py)。重点沿下面三次交接读：

1. **进入：T02 → T06。** 调用方停在 L22 的进入流程中，生成器先准备资源。T03 在 L8 暂停时，L23 还不能执行；准备完成、L11 交出 `sb` 后，`as sandbox` 才接到同一个字典。
2. **使用：T06 → T09。** 当前 Task 执行使用区。T07 在 L24 暂停时，生成器仍停在 L11；即使 L24 恢复，也先完成使用区，再开始退出，不能提前执行关闭。
3. **退出：T09 → T13。** L22 的退出流程恢复生成器，执行 `finally`。T11 在 L14 等待关闭时，L25 还不能执行；直到 T12 关闭完成、生成器结束，才回到调用方打印 `outside False`。

图中的 `OUTPUT` 对应上方的实际输出。特别看 T05 与 T11：**前者把执行交回调用方，后者暂停整个 Task，等待下一次调度。**

`manager` 负责组织进入和退出，`sandbox` 是交给调用方使用的资源。`as sandbox` 接到 `yield` 的值，没有复制字典。

### 3.1 boot_agent_sandbox 与装饰器各负责什么？

- **boot_agent_sandbox 的函数体：** 明确写出沙箱怎样准备，交出哪个对象，退出时怎样关闭。
- **@asynccontextmanager：** 把这份含 yield 的 async def 交给标准库处理，让调用它得到可供 async with 使用的管理器。
- **async with 的缩进块：** 由调用方提供使用沙箱的具体工作。

这里每次资源使用只交出一个值；多个值的异步产出留到第 22 课。

### 3.2 与 TaskGroup：结构相同，退出规则由各自提供

| 使用的管理器 | 正常进入以后用什么 | 正常退出时做什么 |
| --- | --- | --- |
| asyncio.TaskGroup | group，用来登记子任务 | 等待组内任务结束 |
| boot_agent_sandbox | sandbox，用来执行沙箱内的工作 | 关闭这份沙箱 |

async with 负责触发进入和退出，具体动作由管理器提供。这里关闭沙箱的语句是我们明确写在 finally 中的。

<span id="async-context-exits"></span>

## 4. asynccontextmanager：先掌握正常交接

1. 调用装饰后的入口只创建管理器；进入 async with 才推进到 yield。
2. yield 交给 as 的资源用于缩进中的工作；正常离开时恢复 finally，并等待关闭完成。

<span id="async-context-takeaways"></span>

自查：为什么 inside True 之后不会马上执行 outside？

<details><summary>查看解释</summary>

使用区还要完成自己的工作；离开时还要恢复管理器的 finally，等关闭结束后才执行 outside。

</details>

接下来只增加“使用区报错”这一种情况；取消放到 21.6。

{{< python-async-slime title="按需阅读：Slime 怎样启动沙箱并在退出时关闭" >}}

## boot_agent_sandbox：准备成功才 yield，使用结束后执行异步关闭

本节沿用已核对的 Slime 固定提交 `2f2318653f6f794dddd321eff7c9d4b7b174643f`。源码摘录与保存的快照逐字及哈希一致；最初在已确认的本地源码路径不可用时，从 GitHub 同一提交获取了这份文件。

跟随调用方进入 `boot_agent_sandbox(image, instance_id)`，先看以下三个阶段：

1. **准备。** 创建候选沙箱，异步进入并安装工具。Semaphore 限制同时启动的数量，失败时按原逻辑重试；若安装失败，先退出这个候选沙箱再抛出错误。
2. **交接。** 准备成功后保存为 sb，`yield sb` 交给调用方的使用范围。
3. **退出。** 使用结束后进入 finally，等待 `sb.__aexit__(None, None, None)` 完成沙箱退出。

{{< source-reference id="source-1" >}}

教学版本保留函数名、参数和 yield/finally 的关系。原来的 E2BSandbox、安装、重试及 `__aexit__` 调用被替换为字典状态与标准库 sleep；不能用教学字典的 open 字段推断真实沙箱接口。

## asynccontextmanager：标准库核对与源码位置

语义按 [Python 3.12 contextlib 文档](https://docs.python.org/3.12/library/contextlib.html#contextlib.asynccontextmanager)与本机 `contextlib.py` 核对：进入时推进到一次 yield，退出时继续推进，使用区出错时把异常送回 yield 所在位置。协议内部的方法由标准库处理，本课不要求自己实现它们。

{{< python-async-coverage lesson="21-async-contextmanager" >}}

旧下载继续保留：[manual.py](manual.py)、[yield_steps.py](yield_steps.py)、[failure.py](failure.py)、[cancellation.py](cancellation.py)。当前阅读分别转到 21.1、21.2、21.5、21.6。

{{< /python-async-slime >}}

---

[上一节：21.3 · @ 装饰器：把函数交给另一个函数处理](../21-decorators/) · [下一节：21.5 · finally：使用区报错后怎样关闭](../21-context-errors/) · [返回学习路线](../learning-route/)
